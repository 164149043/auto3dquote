<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'

const DEFAULT_THUMB_COLOR = 0x00e5c7

const props = defineProps<{
  fileName: string
  file: File | Blob | null
  dimensions: { x: number; y: number; z: number } | null
  volume: number | null
  vertices: number | null
  triangles: number | null
  paintColor?: string | null
}>()

const emit = defineEmits<{
  'preview-click': []
  reset: []
}>()

const thumbnailContainer = ref<HTMLDivElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let currentMesh: THREE.Mesh | null = null
let animationId = 0

function initScene() {
  if (!thumbnailContainer.value) return

  const container = thumbnailContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x111827)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000)
  camera.position.set(50, 50, 50)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  container.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  const ambient = new THREE.AmbientLight(0xffffff, 0.4)
  scene.add(ambient)
  const directional = new THREE.DirectionalLight(0x00e5c7, 0.6)
  directional.position.set(50, 100, 50)
  scene.add(directional)
  const backLight = new THREE.DirectionalLight(0xf59e0b, 0.3)
  backLight.position.set(-50, -20, -50)
  scene.add(backLight)

  // Subtle grid
  const gridHelper = new THREE.GridHelper(200, 40, 0x1c2538, 0x1c2538)
  gridHelper.position.y = -0.1
  scene.add(gridHelper)

  function animate() {
    animationId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
  }
  animate()
}

function loadModel(file: File | Blob) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const buffer = e.target?.result as ArrayBuffer
    const loader = new STLLoader()
    const geometry = loader.parse(buffer)
    geometry.computeVertexNormals()

    if (currentMesh) {
      scene.remove(currentMesh)
      currentMesh.geometry.dispose()
      ;(currentMesh.material as THREE.Material).dispose()
    }

    const material = new THREE.MeshStandardMaterial({
      color: props.paintColor ? new THREE.Color(props.paintColor) : DEFAULT_THUMB_COLOR,
      metalness: 0.3,
      roughness: 0.4,
      emissive: 0x003322,
      emissiveIntensity: 0.1,
    })

    currentMesh = new THREE.Mesh(geometry, material)
    scene.add(currentMesh)

    geometry.computeBoundingBox()
    const box = geometry.boundingBox!
    const center = new THREE.Vector3()
    box.getCenter(center)
    const size = new THREE.Vector3()
    box.getSize(size)
    const maxDim = Math.max(size.x, size.y, size.z)
    const distance = maxDim * 2

    camera.position.set(center.x + distance, center.y + distance, center.z + distance)
    controls.target.copy(center)
    controls.update()
  }
  reader.readAsArrayBuffer(file)
}

function formatDimensions() {
  if (!props.dimensions) return '--'
  const { x, y, z } = props.dimensions
  return `${x.toFixed(2)} x ${y.toFixed(2)} x ${z.toFixed(2)} mm`
}

function formatVolume() {
  if (props.volume == null) return '--'
  if (props.volume >= 1000) return `${(props.volume / 1000).toFixed(2)} cm³`
  return `${props.volume.toFixed(1)} mm³`
}

watch(() => props.file, (newFile) => {
  if (newFile && scene) loadModel(newFile)
})

watch(() => props.paintColor, (color) => {
  if (!currentMesh) return
  const mat = currentMesh.material as THREE.MeshStandardMaterial
  mat.color.set(color ? new THREE.Color(color) : DEFAULT_THUMB_COLOR)
})

onMounted(() => {
  initScene()
  if (props.file) loadModel(props.file)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  if (currentMesh) {
    currentMesh.geometry.dispose()
    ;(currentMesh.material as THREE.Material).dispose()
  }
  renderer?.dispose()
  controls?.dispose()
})
</script>

<template>
  <div class="glass-panel overflow-hidden corner-markers">
    <div class="flex flex-col sm:flex-row">
      <!-- 3D Thumbnail -->
      <div
        class="sm:w-60 h-40 cursor-pointer relative group flex-shrink-0 overflow-hidden"
        @click="emit('preview-click')"
      >
        <div ref="thumbnailContainer" class="w-full h-full"></div>
        <!-- Hover overlay -->
        <div class="absolute inset-0 bg-teal/0 group-hover:bg-teal/10 transition-all duration-300 flex items-center justify-center">
          <div class="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center gap-2 px-4 py-2 rounded-lg bg-void/60 backdrop-blur-sm">
            <svg class="w-4 h-4 text-teal" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" /></svg>
            <span class="text-sm font-medium text-teal">放大预览</span>
          </div>
        </div>
        <!-- Corner marker -->
        <div class="absolute top-2 left-2 w-3 h-3 border-t border-l border-teal/30"></div>
      </div>

      <!-- File info -->
      <div class="flex-1 p-5 flex flex-col justify-between min-w-0">
        <div>
          <!-- Filename -->
          <h3 class="font-display font-semibold text-mist text-sm truncate mb-3" :title="fileName">
            {{ fileName }}
          </h3>

          <!-- Meta grid -->
          <div class="grid grid-cols-2 gap-x-4 gap-y-2.5">
            <div class="flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-teal/60 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z"/></svg>
              <div>
                <span class="text-[10px] text-ghost uppercase tracking-wider block leading-none mb-0.5">尺寸</span>
                <span class="text-xs font-mono text-mist number-display">{{ formatDimensions() }}</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-3.5 h-3.5 text-amber/60 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a8 8 0 100 16 8 8 0 000-16zM8 12.5a.5.5 0 01-.5-.5V8a.5.5 0 011 0v4a.5.5 0 01-.5.5zm4 0a.5.5 0 01-.5-.5V8a.5.5 0 011 0v4a.5.5 0 01-.5.5z"/></svg>
              <div>
                <span class="text-[10px] text-ghost uppercase tracking-wider block leading-none mb-0.5">体积</span>
                <span class="text-xs font-mono text-mist number-display">{{ formatVolume() }}</span>
              </div>
            </div>
            <div v-if="vertices" class="flex items-center gap-2 col-span-2">
              <svg class="w-3.5 h-3.5 text-edge-light flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path d="M5.5 2.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM11 4a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM5.5 8.5a1.5 1.5 0 100 3 1.5 1.5 0 000-3zM11 10a1.5 1.5 0 100 3 1.5 1.5 0 000-3z"/></svg>
              <span class="text-xs font-mono text-ghost number-display">{{ vertices?.toLocaleString() }} 顶点 / {{ triangles?.toLocaleString() }} 面片</span>
            </div>
          </div>
        </div>

        <button
          @click="emit('reset')"
          class="self-start text-xs text-teal hover:text-teal-dim font-medium mt-3 transition-colors duration-200 flex items-center gap-1.5"
        >
          <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg>
          重新上传
        </button>
      </div>
    </div>
  </div>
</template>
