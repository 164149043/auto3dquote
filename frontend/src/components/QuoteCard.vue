<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import type { QuoteResponse, QuoteParams, PaintConfig } from '../types/api'
import { useQuoteApi } from '../composables/useQuoteApi'
import PreviewModal from './PreviewModal.vue'
import ParameterPanel from './ParameterPanel.vue'

const props = defineProps<{
  file: File
}>()

const emit = defineEmits<{
  remove: []
  'price-changed': [price: number | null]
}>()

const { submitQuote, convertToStl } = useQuoteApi()

const CAD_EXTENSIONS = ['.stp', '.step']
const DEFAULT_THUMB_COLOR = 0x00e5c7

function isCadFile(file: File): boolean {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  return CAD_EXTENSIONS.includes(ext)
}

// State
const previewFile = ref<File | Blob | null>(null)
const isConverting = ref(false)
const paintOptions = ref<PaintConfig | null>(null)
const quoteResult = ref<QuoteResponse | null>(null)
const isLoading = ref(false)
const error = ref('')
const showPreviewModal = ref(false)
const currentParams = ref<QuoteParams | null>(null)
const showDetail = ref(false)

// Thumbnail
const thumbContainer = ref<HTMLDivElement | null>(null)
let thumbScene: THREE.Scene
let thumbCamera: THREE.PerspectiveCamera
let thumbRenderer: THREE.WebGLRenderer
let thumbMesh: THREE.Mesh | null = null
let thumbAnimId = 0

function initThumb() {
  if (!thumbContainer.value) return
  const el = thumbContainer.value
  const w = el.clientWidth
  const h = el.clientHeight

  thumbScene = new THREE.Scene()
  thumbScene.background = new THREE.Color(0x111827)

  thumbCamera = new THREE.PerspectiveCamera(45, w / h, 0.1, 10000)
  thumbCamera.position.set(50, 50, 50)

  thumbRenderer = new THREE.WebGLRenderer({ antialias: true })
  thumbRenderer.setSize(w, h)
  thumbRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  el.appendChild(thumbRenderer.domElement)

  thumbScene.add(new THREE.AmbientLight(0xffffff, 0.5))
  const dir = new THREE.DirectionalLight(0x00e5c7, 0.6)
  dir.position.set(50, 100, 50)
  thumbScene.add(dir)

  const grid = new THREE.GridHelper(200, 40, 0x1c2538, 0x1c2538)
  grid.position.y = -0.1
  thumbScene.add(grid)

  function animate() {
    thumbAnimId = requestAnimationFrame(animate)
    thumbRenderer.render(thumbScene, thumbCamera)
  }
  animate()
}

function loadThumbModel(file: File | Blob) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const buffer = e.target?.result as ArrayBuffer
    if (file instanceof File) {
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
      if (ext !== '.stl') return
    }
    const loader = new STLLoader()
    const geometry = loader.parse(buffer)
    geometry.computeVertexNormals()

    if (thumbMesh) {
      thumbScene.remove(thumbMesh)
      thumbMesh.geometry.dispose()
      ;(thumbMesh.material as THREE.Material).dispose()
    }

    const material = new THREE.MeshStandardMaterial({
      color: paintOptions.value ? new THREE.Color(paintOptions.value.color) : DEFAULT_THUMB_COLOR,
      metalness: 0.3, roughness: 0.4,
    })
    thumbMesh = new THREE.Mesh(geometry, material)
    thumbScene.add(thumbMesh)

    geometry.computeBoundingBox()
    const box = geometry.boundingBox!
    const center = new THREE.Vector3()
    box.getCenter(center)
    const size = new THREE.Vector3()
    box.getSize(size)
    const maxDim = Math.max(size.x, size.y, size.z)
    const dist = maxDim * 2
    thumbCamera.position.set(center.x + dist, center.y + dist, center.z + dist)
    thumbCamera.lookAt(center)
  }
  reader.readAsArrayBuffer(file)
}

// Debounce
let debounceTimer: ReturnType<typeof setTimeout> | null = null

function scheduleQuote() {
  if (!currentParams.value) return
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => onSubmit(), 500)
}

onMounted(async () => {
  initThumb()

  if (isCadFile(props.file)) {
    isConverting.value = true
    try {
      const stlBlob = await convertToStl(props.file)
      previewFile.value = new File([stlBlob], props.file.name.replace(/\.\w+$/, '.stl'), { type: 'application/octet-stream' })
      loadThumbModel(previewFile.value)
    } catch (e: unknown) {
      error.value = `STEP 转换失败: ${e instanceof Error ? e.message : '未知错误'}`
    } finally {
      isConverting.value = false
      scheduleQuote()
    }
  } else {
    previewFile.value = props.file
    loadThumbModel(props.file)
    scheduleQuote()
  }
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  cancelAnimationFrame(thumbAnimId)
  if (thumbMesh) {
    thumbMesh.geometry.dispose()
    ;(thumbMesh.material as THREE.Material).dispose()
  }
  thumbRenderer?.dispose()
})

function onParamsChanged(newParams: QuoteParams & { paint_options?: PaintConfig | null }) {
  const { paint_options, ...rest } = newParams
  currentParams.value = rest
  paintOptions.value = paint_options ?? null
  // Update thumbnail color
  if (thumbMesh) {
    const mat = thumbMesh.material as THREE.MeshStandardMaterial
    mat.color.set(paintOptions.value ? new THREE.Color(paintOptions.value.color) : DEFAULT_THUMB_COLOR)
  }
  scheduleQuote()
}

async function onSubmit() {
  if (!currentParams.value) return
  isLoading.value = true
  error.value = ''

  try {
    const result = await submitQuote(props.file, { ...currentParams.value, paint_options: paintOptions.value })
    quoteResult.value = result
    emit('price-changed', result.quote?.total_price ?? null)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '报价请求失败'
    emit('price-changed', null)
  } finally {
    isLoading.value = false
  }
}

// Compact info helpers
function fmtDim(): string {
  const bb = quoteResult.value?.analysis?.bounding_box
  if (!bb) return '--'
  return `${bb.x_mm.toFixed(1)}×${bb.y_mm.toFixed(1)}×${bb.z_mm.toFixed(1)}mm`
}

function fmtVol(): string {
  const v = quoteResult.value?.analysis?.volume_mm3
  if (v == null) return '--'
  return v >= 1000 ? `${(v / 1000).toFixed(1)}cm³` : `${v.toFixed(0)}mm³`
}

function fmtWeight(): string {
  const g = quoteResult.value?.slicing?.filament_used_grams
  if (g == null) return '--'
  return `${g}g`
}

function fmtTime(): string {
  return quoteResult.value?.slicing?.print_time_formatted ?? '--'
}

function priceLine(): string {
  if (!quoteResult.value?.quote) return ''
  const q = quoteResult.value.quote
  const parts = [`材料¥${q.material_cost.subtotal.toFixed(2)}`, `时间¥${q.time_cost.subtotal.toFixed(2)}`]
  if (q.support_cost > 0) parts.push(`支撑¥${q.support_cost.toFixed(2)}`)
  if (q.difficulty_surcharge > 0) parts.push(`难度¥${q.difficulty_surcharge.toFixed(2)}`)
  if (q.delivery_surcharge > 0) parts.push(`加急¥${q.delivery_surcharge.toFixed(2)}`)
  for (const pp of q.post_process_costs) parts.push(`${pp.name}¥${pp.subtotal.toFixed(2)}`)
  if (q.quantity_discount > 0) parts.push(`折扣-¥${q.quantity_discount.toFixed(2)}`)
  return parts.join(' + ')
}
</script>

<template>
  <div class="glass-panel overflow-hidden animate-fade-in-up relative">
    <div class="flex">
      <!-- Left: Tiny 3D thumbnail -->
      <div
        class="w-[120px] h-[110px] flex-shrink-0 cursor-pointer relative group border-r border-edge/30"
        @click="showPreviewModal = true"
      >
        <div ref="thumbContainer" class="w-full h-full"></div>
        <div class="absolute inset-0 flex items-center justify-center bg-void/0 group-hover:bg-void/40 transition-all">
          <svg class="w-5 h-5 text-teal opacity-0 group-hover:opacity-100 transition-opacity" viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" /></svg>
        </div>
        <!-- STEP converting -->
        <div v-if="isConverting" class="absolute inset-0 flex items-center justify-center bg-void/80">
          <div class="w-4 h-4 border-2 border-teal border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>

      <!-- Right: Content -->
      <div class="flex-1 min-w-0 p-3 flex flex-col gap-2">
        <!-- Row 1: filename + price + remove -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <span class="text-xs font-mono text-mist truncate">{{ file.name }}</span>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span v-if="quoteResult?.quote" class="text-2xl font-display font-bold number-display" style="color: var(--color-amber);">¥{{ quoteResult.quote.total_price.toFixed(2) }}</span>
            <button
              @click="emit('remove')"
              class="w-5 h-5 rounded flex items-center justify-center text-ghost/50 hover:text-danger hover:bg-danger/10 transition-all"
              title="移除"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
            </button>
          </div>
        </div>

        <!-- Row 2: model info -->
        <div class="flex items-center gap-3 text-[10px] text-ghost/70 font-mono">
          <span>{{ fmtDim() }}</span>
          <span>{{ fmtVol() }}</span>
          <span v-if="quoteResult?.slicing">{{ fmtWeight() }}</span>
          <span v-if="quoteResult?.slicing">{{ fmtTime() }}</span>
        </div>

        <!-- Row 3: params (inline compact) -->
        <ParameterPanel
          :disabled="isLoading"
          @params-changed="onParamsChanged"
        />

        <!-- Row 4: error -->
        <div v-if="error" class="text-[10px] text-danger flex items-center gap-1">
          <svg class="w-3 h-3 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
          {{ error }}
        </div>

        <!-- Row 5: price summary -->
        <div v-if="quoteResult?.quote" class="flex items-center justify-between">
          <span class="text-[10px] text-ghost/50 font-mono truncate">{{ priceLine() }}</span>
          <button
            @click="showDetail = !showDetail"
            class="text-[10px] text-teal/60 hover:text-teal font-mono flex-shrink-0 ml-2"
          >{{ showDetail ? '收起' : '详情' }}</button>
        </div>
      </div>
    </div>

    <!-- Expanded detail -->
    <div v-if="showDetail && quoteResult?.quote" class="border-t border-edge/30 px-3 py-2">
      <div class="grid grid-cols-2 gap-x-6 gap-y-1 text-[10px] font-mono">
        <div class="flex justify-between"><span class="text-ghost">材料</span><span class="text-mist">¥{{ quoteResult.quote.material_cost.subtotal.toFixed(2) }}</span></div>
        <div class="flex justify-between"><span class="text-ghost">时间</span><span class="text-mist">¥{{ quoteResult.quote.time_cost.subtotal.toFixed(2) }}</span></div>
        <div v-if="quoteResult.quote.support_cost > 0" class="flex justify-between"><span class="text-ghost">支撑</span><span class="text-mist">¥{{ quoteResult.quote.support_cost.toFixed(2) }}</span></div>
        <div v-if="quoteResult.quote.difficulty_surcharge > 0" class="flex justify-between"><span class="text-ghost">难度加价</span><span class="text-amber">¥{{ quoteResult.quote.difficulty_surcharge.toFixed(2) }}</span></div>
        <div v-if="quoteResult.quote.delivery_surcharge > 0" class="flex justify-between"><span class="text-ghost">加急</span><span class="text-amber">¥{{ quoteResult.quote.delivery_surcharge.toFixed(2) }}</span></div>
        <div v-for="pp in quoteResult.quote.post_process_costs" :key="pp.type" class="flex justify-between"><span class="text-ghost">{{ pp.name }}</span><span class="text-mist">¥{{ pp.subtotal.toFixed(2) }}</span></div>
        <div v-if="quoteResult.quote.quantity_discount > 0" class="flex justify-between"><span class="text-ghost">折扣</span><span class="text-teal">-¥{{ quoteResult.quote.quantity_discount.toFixed(2) }}</span></div>
        <div class="flex justify-between"><span class="text-ghost">加价率</span><span class="text-mist">×{{ quoteResult.quote.markup_rate }}</span></div>
      </div>
      <div v-if="quoteResult.warnings.length" class="mt-1.5 flex flex-wrap gap-1">
        <span v-for="(w, i) in quoteResult.warnings" :key="i" class="text-[9px] text-amber/70">⚠ {{ w }}</span>
      </div>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="isLoading"
      class="absolute inset-0 z-20 flex items-center justify-center"
      style="background: rgba(10,15,30,0.75); backdrop-filter: blur(4px);"
    >
      <div class="flex items-center gap-2.5">
        <div class="relative w-8 h-8">
          <div class="w-8 h-8 border-2 border-teal/20 rounded-full"></div>
          <div class="w-8 h-8 border-2 border-teal border-t-transparent rounded-full animate-spin absolute inset-0"></div>
        </div>
        <span class="text-sm font-display font-semibold text-teal tracking-wider">正在计算...</span>
      </div>
    </div>

    <!-- Preview modal -->
    <PreviewModal
      :visible="showPreviewModal"
      :file="previewFile"
      :paint-color="paintOptions?.color ?? null"
      @close="showPreviewModal = false"
    />
  </div>
</template>
