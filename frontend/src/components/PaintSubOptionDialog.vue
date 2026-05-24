<script setup lang="ts">
import { ref, watch } from 'vue'
import PantoneColorPicker from './PantoneColorPicker.vue'

export interface PaintSelection {
  finishType: 'matte' | 'glossy'
  color: string
  colorName?: string
}

const props = defineProps<{
  visible: boolean
  currentSelection: PaintSelection | null
}>()

const emit = defineEmits<{
  confirm: [selection: PaintSelection]
  cancel: []
}>()

const step = ref<1 | 2>(1)
const finishType = ref<'matte' | 'glossy'>('matte')
const selectedColor = ref<string | null>(null)
const selectedColorName = ref('')

function onColorSelect(color: { hex: string; name: string }) {
  selectedColor.value = color.hex
  selectedColorName.value = color.name
}

function confirm() {
  if (selectedColor.value) {
    emit('confirm', {
      finishType: finishType.value,
      color: selectedColor.value,
      colorName: selectedColorName.value,
    })
  }
}

watch(() => props.visible, (v) => {
  if (v) {
    step.value = 1
    if (props.currentSelection) {
      finishType.value = props.currentSelection.finishType
      selectedColor.value = props.currentSelection.color
      selectedColorName.value = props.currentSelection.colorName || ''
    } else {
      finishType.value = 'matte'
      selectedColor.value = null
      selectedColorName.value = ''
    }
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-void/80 backdrop-blur-sm" @click="$emit('cancel')"></div>

        <div class="relative w-full max-w-lg max-h-[80vh] flex flex-col z-10 rounded-2xl border border-edge/50 overflow-hidden animate-fade-in-scale"
          style="background: linear-gradient(135deg, rgba(17,24,39,0.97) 0%, rgba(22,29,47,0.97) 100%); backdrop-filter: blur(20px);">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-edge/40">
            <div class="flex items-center gap-2">
              <div class="w-1 h-4 rounded-full bg-amber"></div>
              <h2 class="font-display font-bold text-white text-base">喷漆设置</h2>
            </div>
            <button @click="$emit('cancel')" class="w-8 h-8 rounded-lg border border-edge/50 flex items-center justify-center text-ghost hover:text-mist hover:border-edge transition-all duration-200">
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
            </button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-4">
            <!-- Finish type -->
            <div class="mb-6">
              <p class="text-xs font-medium text-ghost uppercase tracking-wider mb-3">颜色类型</p>
              <div class="flex gap-3">
                <button
                  @click="finishType = 'matte'"
                  :class="[
                    'flex-1 py-3 px-4 rounded-xl border text-center transition-all duration-200',
                    finishType === 'matte'
                      ? 'border-teal/50 bg-teal/10 glow-teal'
                      : 'border-edge/50 bg-deep hover:border-edge'
                  ]"
                >
                  <div class="w-10 h-10 rounded-lg bg-edge mx-auto mb-2"></div>
                  <div class="text-sm font-medium text-mist">哑光</div>
                  <div class="text-[10px] text-ghost font-mono">MATTE</div>
                </button>
                <button
                  @click="finishType = 'glossy'"
                  :class="[
                    'flex-1 py-3 px-4 rounded-xl border text-center transition-all duration-200',
                    finishType === 'glossy'
                      ? 'border-teal/50 bg-teal/10 glow-teal'
                      : 'border-edge/50 bg-deep hover:border-edge'
                  ]"
                >
                  <div class="w-10 h-10 rounded-lg mx-auto mb-2" style="background: linear-gradient(135deg, #3a4f6e 0%, #94a3b8 100%);"></div>
                  <div class="text-sm font-medium text-mist">高光</div>
                  <div class="text-[10px] text-ghost font-mono">GLOSSY</div>
                </button>
              </div>
            </div>

            <!-- Color picker -->
            <div>
              <p class="text-xs font-medium text-ghost uppercase tracking-wider mb-3">选择颜色</p>
              <PantoneColorPicker
                :selectedColor="selectedColor"
                @select="onColorSelect"
              />
            </div>

            <!-- Selected color preview -->
            <div v-if="selectedColor" class="mt-4 flex items-center gap-3 p-3 rounded-xl bg-deep border border-edge/50">
              <div class="w-8 h-8 rounded-lg border border-edge" :style="{ backgroundColor: selectedColor }"></div>
              <div>
                <p class="text-sm font-medium text-mist">{{ selectedColorName || selectedColor }}</p>
                <p class="text-[10px] text-ghost font-mono">{{ finishType === 'matte' ? 'MATTE' : 'GLOSSY' }}</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-edge/40 flex justify-end gap-3">
            <button
              @click="$emit('cancel')"
              class="btn-ghost px-4 py-2 text-sm"
            >取消</button>
            <button
              @click="confirm"
              :disabled="!selectedColor"
              :class="[
                'px-6 py-2 rounded-xl text-sm font-display font-semibold transition-all duration-300',
                selectedColor ? 'btn-primary' : 'bg-elevated text-ghost/40 cursor-not-allowed'
              ]"
            >确认</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active { transition: opacity 0.2s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
