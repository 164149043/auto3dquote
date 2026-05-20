<script setup lang="ts">
import { ref } from 'vue'
import type { PostProcessOption } from '../types/api'
import InfoTooltip from './InfoTooltip.vue'
import PaintSubOptionDialog, { type PaintSelection } from './PaintSubOptionDialog.vue'

const props = defineProps<{
  options: PostProcessOption[]
  selected: string[]
  disabled: boolean
  paintSelection: PaintSelection | null
}>()

const emit = defineEmits<{
  toggle: [id: string]
  'update:paint': [selection: PaintSelection | null]
}>()

const showPaintDialog = ref(false)

const PP_DESCRIPTIONS: Record<string, string> = {
  sanding: '使用砂纸对零件表面进行打磨处理，去除层纹和毛刺，使表面更加光滑。',
  painting: '对零件表面喷涂指定颜色的油漆，可选择哑光或高光效果，支持自定义颜色。',
  polishing: '通过机械或化学方式使零件表面达到镜面光泽效果。',
  tapping: '在零件预留孔位加工内螺纹，安装螺母或螺栓连接。',
  heat_treatment: '通过加热和冷却改善材料力学性能，提高强度和硬度。',
  anodizing: '铝材表面的阳极氧化处理，增加耐腐蚀性和表面硬度，可着色。',
  electroplating: '在零件表面沉积一层金属镀层（如镀铬、镀镍），提高耐磨性和外观。',
  support_removal: '去除3D打印过程中产生的支撑结构，清理表面残留。',
  uv_curing: '对光敏树脂零件进行紫外线二次固化，提高强度和稳定性。',
  infiltration: '将液态树脂或蜡渗入SLS零件内部，提高强度和表面质量。',
  dyeing: '对SLS/MJF零件进行染色处理，使表面呈现指定颜色。',
}

function getDescription(pp: PostProcessOption): string {
  return pp.description || PP_DESCRIPTIONS[pp.id] || ''
}

function formatPpPrice(pp: PostProcessOption) {
  if (pp.price_mode === 'fixed') return `+¥${pp.price_value}`
  return `+${(pp.price_value * 100).toFixed(0)}%`
}

function onToggle(pp: PostProcessOption) {
  if (props.disabled) return
  if (pp.id === 'painting') {
    const isCurrentlySelected = props.selected.includes(pp.id)
    if (!isCurrentlySelected) {
      showPaintDialog.value = true
    } else {
      emit('update:paint', null)
      emit('toggle', pp.id)
    }
    return
  }
  emit('toggle', pp.id)
}

function onPaintConfirm(selection: PaintSelection) {
  showPaintDialog.value = false
  emit('update:paint', selection)
  if (!props.selected.includes('painting')) {
    emit('toggle', 'painting')
  }
}

function onPaintCancel() {
  showPaintDialog.value = false
  if (!props.paintSelection) {
    if (props.selected.includes('painting')) {
      emit('toggle', 'painting')
    }
  }
}
</script>

<template>
  <div>
    <label class="block text-xs font-medium text-ghost uppercase tracking-wider mb-2">表面处理</label>
    <div class="space-y-2">
      <div
        v-for="pp in options"
        :key="pp.id"
        :class="[
          'flex items-center justify-between px-3.5 py-2.5 rounded-lg border transition-all duration-200',
          selected.includes(pp.id) ? 'border-teal/40 bg-teal/8' : 'border-edge/50 bg-deep hover:border-edge',
          disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'
        ]"
        @click="onToggle(pp)"
      >
        <div class="flex items-center gap-2.5">
          <!-- Custom checkbox -->
          <div
            :class="[
              'w-4 h-4 rounded border flex items-center justify-center transition-all duration-200',
              selected.includes(pp.id)
                ? 'bg-teal border-teal'
                : 'border-edge-light bg-transparent'
            ]"
          >
            <svg v-if="selected.includes(pp.id)" class="w-2.5 h-2.5 text-void" viewBox="0 0 12 12" fill="currentColor">
              <path d="M10 3L4.5 8.5 2 6l1-1 1.5 1.5L9 2l1 1z"/>
            </svg>
          </div>
          <span class="text-sm text-silver">{{ pp.label }}</span>
          <InfoTooltip v-if="getDescription(pp)" :text="getDescription(pp)" />
          <!-- Paint color indicator -->
          <span
            v-if="pp.id === 'painting' && paintSelection"
            class="inline-flex items-center gap-1 text-[10px] text-ghost"
          >
            <span class="w-2.5 h-2.5 rounded-sm border border-edge" :style="{ backgroundColor: paintSelection.color }"></span>
            {{ paintSelection.colorName || '' }} ({{ paintSelection.finishType === 'matte' ? '哑光' : '高光' }})
          </span>
        </div>
        <span class="text-[10px] text-ghost font-mono">{{ formatPpPrice(pp) }}</span>
      </div>
    </div>

    <PaintSubOptionDialog
      :visible="showPaintDialog"
      :currentSelection="paintSelection"
      @confirm="onPaintConfirm"
      @cancel="onPaintCancel"
    />
  </div>
</template>
