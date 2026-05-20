<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { QuoteParams, OptionsResponse, ProcessOption, PostProcessOption, DeliveryOption, MaterialOption, PaintConfig } from '../types/api'
import { useQuoteApi } from '../composables/useQuoteApi'
import MaterialSelectModal from './MaterialSelectModal.vue'
import SurfaceTreatmentSection from './SurfaceTreatmentSection.vue'
import DeliveryTimeSelector from './DeliveryTimeSelector.vue'
import PriceDisplay from './PriceDisplay.vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  'params-changed': [params: QuoteParams]
  submit: []
}>()

const { fetchOptions } = useQuoteApi()

const options = ref<OptionsResponse | null>(null)
const optionsError = ref('')
const showMaterialModal = ref(false)
const paintSelection = ref<PaintConfig | null>(null)

const params = reactive<QuoteParams>({
  process: 'fdm',
  material: 'PLA',
  quality: 'standard',
  quantity: 1,
  post_processing: [],
  delivery: 'standard',
})

const currentProcess = computed<ProcessOption | undefined>(() => {
  return options.value?.processes.find(p => p.id === params.process)
})

const currentMaterials = computed(() => currentProcess.value?.materials ?? [])
const currentPostProcesses = computed(() => currentProcess.value?.post_processes ?? [])
const currentDeliveryOptions = computed(() => currentProcess.value?.delivery_options ?? [])

const selectedMaterialInfo = computed<MaterialOption | undefined>(() => {
  return currentMaterials.value.find(m => m.id === params.material)
})

function onMaterialSelect(payload: { processId: string; materialId: string }) {
  params.process = payload.processId
  params.material = payload.materialId
  params.post_processing = []
  showMaterialModal.value = false
  emitParams()
}

function togglePostProcess(ppId: string) {
  const idx = params.post_processing.indexOf(ppId)
  if (idx >= 0) {
    params.post_processing.splice(idx, 1)
  } else {
    params.post_processing.push(ppId)
  }
  emitParams()
}

function onDeliveryChange(id: string) {
  params.delivery = id
  emitParams()
}

function emitParams() {
  emit('params-changed', { ...params, post_processing: [...params.post_processing] })
}

function formatMaterialPrice(mat: MaterialOption) {
  return `¥${mat.price}/${mat.unit}`
}

onMounted(async () => {
  try {
    const data = await fetchOptions()
    options.value = data
    const defaultDelivery = data.processes[0]?.delivery_options.find(d => d.days === 2 || d.id === 'express')
    if (defaultDelivery) {
      params.delivery = defaultDelivery.id
    }
    emitParams()
  } catch {
    optionsError.value = '获取选项列表失败，显示默认配置'
  }
})
</script>

<template>
  <div class="space-y-5">
    <p v-if="optionsError" class="text-xs text-amber bg-amber/10 rounded-lg px-3 py-2 border border-amber/20">{{ optionsError }}</p>

    <!-- Material Selection -->
    <div>
      <label class="block text-xs font-medium text-ghost uppercase tracking-wider mb-2">材料</label>
      <div
        @click="disabled ? null : showMaterialModal = true"
        :class="[
          'px-4 py-3 rounded-xl border transition-all duration-200',
          disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:border-teal/40 hover:bg-teal-glass',
          'border-edge bg-deep'
        ]"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div v-if="selectedMaterialInfo?.image_url" class="w-9 h-9 rounded-lg overflow-hidden bg-surface flex-shrink-0 border border-edge/50">
              <img :src="selectedMaterialInfo.image_url" :alt="selectedMaterialInfo.label" class="w-full h-full object-cover" />
            </div>
            <div v-else class="w-9 h-9 rounded-lg bg-teal/10 border border-teal/20 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-teal/60" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 2.75c1.24 0 2.25 1.01 2.25 2.25s-1.01 2.25-2.25 2.25S9.75 8.24 9.75 7s1.01-2.25 2.25-2.25zM17 17H7v-1.5c0-1.67 3.33-2.5 5-2.5s5 .83 5 2.5V17z"/></svg>
            </div>
            <div>
              <p class="font-medium text-mist text-sm">{{ selectedMaterialInfo?.label || '选择材料' }}</p>
              <p v-if="selectedMaterialInfo" class="text-[11px] text-ghost font-mono mt-0.5">{{ formatMaterialPrice(selectedMaterialInfo) }}</p>
            </div>
          </div>
          <svg class="w-4 h-4 text-ghost" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" /></svg>
        </div>
      </div>
    </div>

    <!-- Surface Treatment -->
    <SurfaceTreatmentSection
      v-if="currentPostProcesses.length > 0"
      :options="currentPostProcesses"
      :selected="params.post_processing"
      :disabled="!!disabled"
      :paintSelection="paintSelection"
      @toggle="togglePostProcess"
      @update:paint="paintSelection = $event"
    />

    <!-- Quantity -->
    <div>
      <label class="block text-xs font-medium text-ghost uppercase tracking-wider mb-2">数量</label>
      <div class="flex items-center gap-2">
        <button
          @click="params.quantity = Math.max(1, params.quantity - 1); emitParams()"
          :disabled="disabled"
          class="w-9 h-9 rounded-lg border border-edge bg-deep text-silver font-bold text-sm hover:border-teal/40 hover:text-teal transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >-</button>
        <input
          type="number"
          v-model.number="params.quantity"
          min="1"
          max="1000"
          :disabled="disabled"
          class="w-20 text-center py-2 rounded-lg input-dark font-mono text-sm"
          @change="emitParams()"
        />
        <button
          @click="params.quantity = Math.min(1000, params.quantity + 1); emitParams()"
          :disabled="disabled"
          class="w-9 h-9 rounded-lg border border-edge bg-deep text-silver font-bold text-sm hover:border-teal/40 hover:text-teal transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
        >+</button>
        <span class="text-[10px] text-ghost/50 font-mono ml-1">MAX 1000</span>
      </div>
    </div>

    <!-- Delivery Time -->
    <DeliveryTimeSelector
      v-if="currentDeliveryOptions.length > 0"
      :options="currentDeliveryOptions"
      :selected="params.delivery"
      :disabled="!!disabled"
      @change="onDeliveryChange"
    />

    <!-- Price Display + Submit -->
    <PriceDisplay
      :price="null"
      :isLoading="!!disabled"
      @submit="emit('submit')"
    />

    <!-- Action buttons -->
    <div class="flex gap-2 pt-1">
      <button disabled class="flex-1 py-2 rounded-lg border border-edge/50 text-ghost/30 text-xs cursor-not-allowed font-mono">CART</button>
      <button disabled class="flex-1 py-2 rounded-lg border border-edge/50 text-ghost/30 text-xs cursor-not-allowed font-mono">COPY</button>
      <button disabled class="flex-1 py-2 rounded-lg border border-edge/50 text-ghost/30 text-xs cursor-not-allowed font-mono">DEL</button>
    </div>

    <!-- Material select modal -->
    <MaterialSelectModal
      :visible="showMaterialModal"
      :processes="options?.processes ?? []"
      :selectedProcess="params.process"
      :selectedMaterial="params.material"
      @select="onMaterialSelect"
      @close="showMaterialModal = false"
    />
  </div>
</template>
