<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  text: string
}>()

const show = ref(false)
</script>

<template>
  <span class="relative inline-flex items-center" @mouseenter="show = true" @mouseleave="show = false">
    <button
      class="w-3.5 h-3.5 rounded-full bg-edge/60 text-ghost text-[9px] font-bold flex items-center justify-center hover:bg-teal/30 hover:text-teal transition-colors duration-200"
      @click="show = !show"
      type="button"
    >?</button>
    <Transition name="tooltip">
      <div
        v-if="show"
        class="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-xs text-mist rounded-lg w-56 text-left border border-edge/50"
        style="background: rgba(22,29,47,0.95); backdrop-filter: blur(12px);"
      >
        {{ text }}
        <div class="absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-panel border-r border-b border-edge/50 rotate-45 -mt-1"></div>
      </div>
    </Transition>
  </span>
</template>

<style scoped>
.tooltip-enter-active { transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1); }
.tooltip-leave-active { transition: all 0.15s ease-in; }
.tooltip-enter-from, .tooltip-leave-to { opacity: 0; transform: translateX(-50%) translateY(4px); }
</style>
