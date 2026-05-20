<script setup lang="ts">
import type { MaterialOption } from '../types/api'

defineProps<{
  material: MaterialOption
  selected: boolean
}>()

defineEmits<{
  click: []
}>()

function formatPrice(mat: MaterialOption) {
  return `¥${mat.price}/${mat.unit}`
}
</script>

<template>
  <button
    @click="$emit('click')"
    :class="[
      'flex flex-col items-center p-3 rounded-xl border transition-all duration-200 text-left group',
      selected
        ? 'border-teal/50 bg-teal/10 glow-teal'
        : 'border-edge/50 bg-deep hover:border-edge hover:bg-surface'
    ]"
  >
    <!-- Image -->
    <div class="w-full h-20 rounded-lg bg-abyss mb-2 flex items-center justify-center overflow-hidden border border-edge/30">
      <img
        v-if="material.image_url"
        :src="material.image_url"
        :alt="material.label"
        class="w-full h-full object-cover"
      />
      <svg v-else class="w-6 h-6 text-edge-light" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 2.75c1.24 0 2.25 1.01 2.25 2.25s-1.01 2.25-2.25 2.25S9.75 8.24 9.75 7s1.01-2.25 2.25-2.25zM17 17H7v-1.5c0-1.67 3.33-2.5 5-2.5s5 .83 5 2.5V17z"/>
      </svg>
    </div>
    <!-- Name + price -->
    <p class="text-xs font-medium text-mist truncate w-full text-center">{{ material.label }}</p>
    <p class="text-[10px] text-ghost font-mono mt-0.5">{{ formatPrice(material) }}</p>
  </button>
</template>
