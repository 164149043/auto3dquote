<script setup lang="ts">
import ModelPreview from './ModelPreview.vue'

defineProps<{
  visible: boolean
  file: File | Blob | null
}>()

defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-void/90 backdrop-blur-md" @click="$emit('close')"></div>
        <div class="relative w-[90vw] h-[85vh] rounded-2xl border border-edge/50 overflow-hidden z-10 animate-fade-in-scale"
          style="background: rgba(10,15,30,0.95);">
          <div class="absolute top-4 right-4 z-20">
            <button
              @click="$emit('close')"
              class="w-10 h-10 rounded-xl border border-edge/50 bg-panel/80 backdrop-blur-sm flex items-center justify-center text-ghost hover:text-mist hover:border-edge transition-all duration-200"
            >
              <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
            </button>
          </div>
          <ModelPreview :file="file" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active { transition: opacity 0.25s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
