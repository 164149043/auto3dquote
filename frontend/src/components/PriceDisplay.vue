<script setup lang="ts">
import { formatPrice } from '../utils/format'

defineProps<{
  price: number | null
  isLoading: boolean
}>()
</script>

<template>
  <div class="rounded-lg p-3 border border-edge/50 text-center" style="background: linear-gradient(135deg, rgba(0,229,199,0.04) 0%, rgba(245,158,11,0.04) 100%);">
    <p class="text-[10px] text-ghost uppercase tracking-widest mb-1 font-mono">产品总价</p>
    <div v-if="isLoading" class="flex items-center justify-center gap-1.5 py-1">
      <span class="w-3 h-3 border border-teal border-t-transparent rounded-full animate-spin"></span>
      <span class="text-xs text-teal font-mono">报价中...</span>
    </div>
    <p v-else-if="price !== null" class="text-xl font-display font-bold number-display text-amber">{{ formatPrice(price) }}</p>
    <p v-else class="text-lg text-ghost/30 font-mono">--</p>
  </div>
</template>
