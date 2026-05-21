<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js'

const props = defineProps<{
  file: File | Blob | null
  paintColor?: string | null
}>()

const emit = defineEmits<{
  'model-loaded': [info: { vertices: number; triangles: number }]
  'load-error': [message: string]
}>()

const DEFAULT_COLOR = 0x3b82f6

const canvasContainer = ref<HTMLDivElement | null>(null)
const isLoading = ref(false)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let labelRenderer: CSS2DRenderer
let controls: OrbitControls
let currentMesh: THREE.Mesh | null = null
let annotationGroup: THREE.Group | null = null
let animationId = 0
let resizeObserver: ResizeObserver | null = null
const previewError = ref('')

function initScene() {
  if (!canvasContainer.value) return

  const container = canvasContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x0a0f1e)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000)
  camera.position.set(50, 50, 50)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)

  // CSS2D label renderer — overlays HTML elements in 3D space
  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.left = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  container.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05

  const ambient = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambient)
  const directional = new THREE.DirectionalLight(0xffffff, 0.8)
  directional.position.set(50, 100, 50)
  scene.add(directional)

  function animate() {
    animationId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
    labelRenderer.render(scene, camera)
  }
  animate()

  resizeObserver = new ResizeObserver(() => {
    const w = container.clientWidth
    const h = container.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
    labelRenderer.setSize(w, h)
  })
  resizeObserver.observe(container)
}

/**
 * 在模型周围绘制包围盒线框 + 三个方向的尺寸标注线
 */
function addDimensionAnnotations(center: THREE.Vector3, size: THREE.Vector3) {
  // 清除旧标注
  if (annotationGroup) {
    scene.remove(annotationGroup)
    annotationGroup.traverse((child) => {
      if (child instanceof CSS2DObject && child.element.parentNode) {
        child.element.parentNode.removeChild(child.element)
      }
      if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
        child.geometry.dispose()
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
  }

  annotationGroup = new THREE.Group()

  const hx = size.x / 2
  const hy = size.y / 2
  const hz = size.z / 2

  // ---- 1. 包围盒线框 ----
  const boxGeo = new THREE.BoxGeometry(size.x, size.y, size.z)
  const edges = new THREE.EdgesGeometry(boxGeo)
  const boxLine = new THREE.LineSegments(
    edges,
    new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.5 }),
  )
  boxLine.position.copy(center)
  annotationGroup.add(boxLine)
  boxGeo.dispose()

  // ---- 2. 尺寸标注线 ----
  const offset = Math.max(size.x, size.y, size.z) * 0.08 + 2
  const tickLen = Math.max(size.x, size.y, size.z) * 0.04 + 1

  type AxisDef = { axis: 'x' | 'y' | 'z'; color: number; label: string }
  const axes: AxisDef[] = [
    { axis: 'x', color: 0xef4444, label: `${size.x.toFixed(2)} mm` },
    { axis: 'y', color: 0x22c55e, label: `${size.y.toFixed(2)} mm` },
    { axis: 'z', color: 0x3b82f6, label: `${size.z.toFixed(2)} mm` },
  ]

  for (const { axis, color, label } of axes) {
    // 标注线的起止点和方向
    const start = center.clone()
    const end = center.clone()
    let tickDir: THREE.Vector3

    if (axis === 'x') {
      // X 方向标注放在模型下方前方
      start.x = center.x - hx
      end.x = center.x + hx
      start.y = end.y = center.y - hy - offset
      start.z = end.z = center.z + hz + offset
      tickDir = new THREE.Vector3(0, 1, 0)
    } else if (axis === 'y') {
      // Y 方向标注放在模型右侧前方
      start.y = center.y - hy
      end.y = center.y + hy
      start.x = end.x = center.x + hx + offset
      start.z = end.z = center.z + hz + offset
      tickDir = new THREE.Vector3(-1, 0, 0)
    } else {
      // Z 方向标注放在模型右侧下方
      start.z = center.z - hz
      end.z = center.z + hz
      start.x = end.x = center.x + hx + offset
      start.y = end.y = center.y - hy - offset
      tickDir = new THREE.Vector3(-1, 0, 0)
    }

    // 主标注线
    const lineGeo = new THREE.BufferGeometry().setFromPoints([start, end])
    const line = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({ color }))
    annotationGroup.add(line)

    // 起止端短竖线 (tick marks)
    const tickStart1 = start.clone().addScaledVector(tickDir, tickLen)
    const tickStart2 = start.clone().addScaledVector(tickDir, -tickLen * 0.3)
    const tickGeo1 = new THREE.BufferGeometry().setFromPoints([tickStart1, tickStart2])
    annotationGroup.add(new THREE.Line(tickGeo1, new THREE.LineBasicMaterial({ color })))

    const tickEnd1 = end.clone().addScaledVector(tickDir, tickLen)
    const tickEnd2 = end.clone().addScaledVector(tickDir, -tickLen * 0.3)
    const tickGeo2 = new THREE.BufferGeometry().setFromPoints([tickEnd1, tickEnd2])
    annotationGroup.add(new THREE.Line(tickGeo2, new THREE.LineBasicMaterial({ color })))

    // 连接线 — 从包围盒角落到标注线起点/终点的虚线引导
    const dashMat = new THREE.LineDashedMaterial({
      color,
      dashSize: 1.5,
      gapSize: 1,
      transparent: true,
      opacity: 0.4,
    })

    const cornerStart = start.clone()
    const cornerEnd = end.clone()
    if (axis === 'x') {
      cornerStart.y = cornerEnd.y = center.y - hy
      cornerStart.z = cornerEnd.z = center.z + hz
    } else if (axis === 'y') {
      cornerStart.x = cornerEnd.x = center.x + hx
      cornerStart.z = cornerEnd.z = center.z + hz
    } else {
      cornerStart.x = cornerEnd.x = center.x + hx
      cornerStart.y = cornerEnd.y = center.y - hy
    }

    const guide1Geo = new THREE.BufferGeometry().setFromPoints([cornerStart, start])
    const guide1 = new THREE.Line(guide1Geo, dashMat)
    guide1.computeLineDistances()
    annotationGroup.add(guide1)

    const guide2Geo = new THREE.BufferGeometry().setFromPoints([cornerEnd, end])
    const guide2 = new THREE.Line(guide2Geo, dashMat)
    guide2.computeLineDistances()
    annotationGroup.add(guide2)

    // CSS2D 文字标签
    const labelDiv = document.createElement('div')
    labelDiv.textContent = label
    labelDiv.style.cssText = `
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      font-family: system-ui, -apple-system, sans-serif;
      white-space: nowrap;
      pointer-events: none;
      user-select: none;
    `

    // 标签背景色跟随轴线颜色（半透明）
    if (axis === 'x') {
      labelDiv.style.background = 'rgba(239, 68, 68, 0.12)'
      labelDiv.style.color = '#dc2626'
    } else if (axis === 'y') {
      labelDiv.style.background = 'rgba(34, 197, 94, 0.12)'
      labelDiv.style.color = '#16a34a'
    } else {
      labelDiv.style.background = 'rgba(59, 130, 246, 0.12)'
      labelDiv.style.color = '#2563eb'
    }

    const labelObj = new CSS2DObject(labelDiv)
    labelObj.position.copy(start).lerp(end, 0.5)
    annotationGroup.add(labelObj)
  }

  scene.add(annotationGroup)
}

function loadModel(file: File | Blob) {
  isLoading.value = true

  const reader = new FileReader()
  reader.onload = (e) => {
    const buffer = e.target?.result as ArrayBuffer

    // 如果是 File 对象且有非 STL 扩展名，显示不支持提示
    // Blob 对象（从 STEP 转换的 STL）直接当 STL 处理
    if (file instanceof File) {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
      if (ext !== '.stl') {
        isLoading.value = false
        const msg = `${ext.toUpperCase().slice(1)} 格式暂不支持在线预览，但仍可获取报价`
        previewError.value = msg
        emit('load-error', msg)
        return
      }
    }
    previewError.value = ''

    let geometry: THREE.BufferGeometry

    const loader = new STLLoader()
    geometry = loader.parse(buffer)

    geometry.computeVertexNormals()

    if (currentMesh) {
      scene.remove(currentMesh)
      currentMesh.geometry.dispose()
      ;(currentMesh.material as THREE.Material).dispose()
    }

    const material = new THREE.MeshPhongMaterial({
      color: props.paintColor ? new THREE.Color(props.paintColor) : DEFAULT_COLOR,
      specular: 0x111111,
      shininess: 50,
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

    // 绘制尺寸标注
    addDimensionAnnotations(center, size)

    isLoading.value = false

    emit('model-loaded', {
      vertices: geometry.attributes.position.count,
      triangles: geometry.index ? geometry.index.count / 3 : geometry.attributes.position.count / 3,
    })
  }

  reader.onerror = () => {
    isLoading.value = false
    previewError.value = '文件读取失败'
  }

  reader.readAsArrayBuffer(file)
}

watch(() => props.file, (newFile) => {
  if (newFile && scene) loadModel(newFile)
})

watch(() => props.paintColor, (color) => {
  if (!currentMesh) return
  const mat = currentMesh.material as THREE.MeshPhongMaterial
  mat.color.set(color ? new THREE.Color(color) : DEFAULT_COLOR)
})

onMounted(() => {
  initScene()
  if (props.file) loadModel(props.file)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  if (annotationGroup) {
    annotationGroup.traverse((child) => {
      if (child instanceof CSS2DObject && child.element.parentNode) {
        child.element.parentNode.removeChild(child.element)
      }
      if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
        child.geometry.dispose()
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
    scene?.remove(annotationGroup)
  }
  if (currentMesh) {
    currentMesh.geometry.dispose()
    ;(currentMesh.material as THREE.Material).dispose()
  }
  if (labelRenderer && canvasContainer.value) {
    canvasContainer.value.removeChild(labelRenderer.domElement)
  }
  renderer?.dispose()
  controls?.dispose()
})
</script>

<template>
  <div class="relative w-full bg-deep overflow-hidden" style="height: 500px;">
    <div ref="canvasContainer" class="w-full h-full"></div>
    <div
      v-if="isLoading"
      class="absolute inset-0 flex items-center justify-center"
      style="background: rgba(10,15,30,0.85);"
    >
      <div class="text-teal font-medium animate-pulse font-mono text-sm">加载模型中...</div>
    </div>
    <div
      v-if="previewError && !isLoading"
      class="absolute inset-0 bg-deep flex items-center justify-center"
    >
      <div class="text-center text-ghost">
        <svg class="w-12 h-12 mx-auto mb-3 text-edge-light" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 2.75c1.24 0 2.25 1.01 2.25 2.25s-1.01 2.25-2.25 2.25S9.75 8.24 9.75 7s1.01-2.25 2.25-2.25zM17 17H7v-1.5c0-1.67 3.33-2.5 5-2.5s5 .83 5 2.5V17z"/></svg>
        <p class="text-sm">{{ previewError }}</p>
      </div>
    </div>
  </div>
</template>
