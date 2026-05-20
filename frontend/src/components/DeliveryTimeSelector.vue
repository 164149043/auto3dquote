<script setup lang="ts">
import type { DeliveryOption } from '../types/api'

defineProps<{
  options: DeliveryOption[]
  selected: string
  disabled: boolean
}>()

const emit = defineEmits<{
  change: [id: string]
}>()

function formatSurcharge(opt: DeliveryOption) {
  if (opt.surcharge <= 0) return ''
  return `+${(opt.surcharge * 100).toFixed(0)}%`
}
</script>

<template>
  <div>
    <label class="block text-xs font-medium text-ghost uppercase tracking-wider mb-2">产品交期</label>
    <div class="flex gap-2">
      <button
        v-for="opt in options"
        :key="opt.id"
        @click="!disabled && emit('change', opt.id)"
        :class="[
          'flex-1 py-3 px-3 rounded-xl border text-center transition-all duration-200',
          disabled ? 'cursor-not-allowed opacity-40' : 'cursor-pointer',
          selected === opt.id
            ? 'border-teal/50 bg-teal/10 text-teal glow-teal'
            : 'border-edge bg-deep text-silver hover:border-edge-light'
        ]"
      >
        <div class="font-medium text-sm">{{ opt.label }}</div>
        <div v-if="formatSurcharge(opt)" class="text-[10px] text-amber mt-1 font-mono">{{ formatSurcharge(opt) }}</div>
      </button>
    </div>
  </div>
</template>
