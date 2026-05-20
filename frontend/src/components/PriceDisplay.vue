<script setup lang="ts">
import { formatPrice } from '../utils/format'

defineProps<{
  price: number | null
  isLoading: boolean
}>()

const emit = defineEmits<{
  submit: []
}>()
</script>

<template>
  <div class="rounded-xl p-5 border border-edge/50" style="background: linear-gradient(135deg, rgba(0,229,199,0.04) 0%, rgba(245,158,11,0.04) 100%);">
    <div class="text-center mb-4">
      <p class="text-[10px] text-ghost uppercase tracking-widest mb-2 font-mono">产品总价</p>
      <p v-if="price !== null" class="text-3xl font-display font-bold number-display text-amber">{{ formatPrice(price) }}</p>
      <p v-else class="text-3xl font-mono text-ghost/30">--</p>
    </div>
    <button
      @click="emit('submit')"
      :disabled="isLoading"
      :class="[
        'w-full py-3 rounded-xl font-display font-semibold text-sm tracking-wide transition-all duration-300',
        isLoading
          ? 'bg-elevated text-ghost cursor-not-allowed'
          : 'btn-primary'
      ]"
    >
      <span v-if="isLoading" class="flex items-center justify-center gap-2">
        <span class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
        报价中...
      </span>
      <span v-else>获取报价</span>
    </button>
  </div>
</template>
