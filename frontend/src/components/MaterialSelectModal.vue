<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ProcessOption, MaterialOption } from '../types/api'
import { MATERIAL_CATEGORIES } from '../data/material-categories'
import MaterialCard from './MaterialCard.vue'

const props = defineProps<{
  visible: boolean
  processes: ProcessOption[]
  selectedProcess: string
  selectedMaterial: string
}>()

const emit = defineEmits<{
  select: [payload: { processId: string; materialId: string }]
  close: []
}>()

const activeCategory = ref('all')
const previewMaterial = ref<(MaterialOption & { processId?: string }) | null>(null)

const allMaterials = computed(() => {
  const materials: (MaterialOption & { processId?: string })[] = []
  for (const proc of props.processes) {
    for (const mat of proc.materials) {
      if (!materials.find(m => m.id === mat.id)) {
        materials.push({ ...mat, processId: proc.id })
      }
    }
  }
  return materials
})

const filteredMaterials = computed(() => {
  if (activeCategory.value === 'all') return allMaterials.value
  return allMaterials.value.filter(m => m.category === activeCategory.value)
})

const categories = computed(() => {
  return [{ id: 'all', labelZh: '全部', labelEn: 'All' }, ...MATERIAL_CATEGORIES]
})

function clickMaterial(mat: MaterialOption & { processId?: string }) {
  previewMaterial.value = mat
}

function confirm() {
  if (!previewMaterial.value) return
  const processId = previewMaterial.value.processId || props.selectedProcess
  emit('select', { processId, materialId: previewMaterial.value.id })
}

watch(() => props.visible, (v) => {
  if (v) {
    activeCategory.value = 'all'
    const currentMat = allMaterials.value.find(m => m.id === props.selectedMaterial)
    previewMaterial.value = currentMat || null
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-void/80 backdrop-blur-sm" @click="$emit('close')"></div>

        <!-- Modal -->
        <div class="relative w-full max-w-4xl max-h-[85vh] flex flex-col z-10 rounded-2xl border border-edge/50 overflow-hidden animate-fade-in-scale"
          style="background: linear-gradient(135deg, rgba(17,24,39,0.97) 0%, rgba(22,29,47,0.97) 100%); backdrop-filter: blur(20px);">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-edge/40">
            <div class="flex items-center gap-2">
              <div class="w-1 h-4 rounded-full bg-teal"></div>
              <h2 class="font-display font-bold text-white text-base tracking-wide">选择材料</h2>
            </div>
            <button @click="$emit('close')" class="w-8 h-8 rounded-lg border border-edge/50 flex items-center justify-center text-ghost hover:text-mist hover:border-edge transition-all duration-200">
              <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
            </button>
          </div>

          <div class="flex-1 flex overflow-hidden">
            <!-- Left: Categories + Grid -->
            <div class="flex-1 flex flex-col overflow-hidden">
              <!-- Category tabs -->
              <div class="flex gap-1 px-6 pt-4 pb-2 overflow-x-auto flex-shrink-0">
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  @click="activeCategory = cat.id"
                  :class="[
                    'px-4 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200',
                    activeCategory === cat.id
                      ? 'bg-teal text-void'
                      : 'bg-surface text-ghost hover:text-silver hover:bg-elevated border border-edge/30'
                  ]"
                >{{ cat.labelZh }}</button>
              </div>

              <!-- Material grid -->
              <div class="flex-1 overflow-y-auto px-6 py-4">
                <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-4 gap-2.5">
                  <MaterialCard
                    v-for="mat in filteredMaterials"
                    :key="mat.id"
                    :material="mat"
                    :selected="previewMaterial?.id === mat.id"
                    @click="clickMaterial(mat)"
                  />
                </div>

                <div v-if="filteredMaterials.length === 0" class="text-center py-12 text-ghost/50">
                  <p class="text-sm">该分类暂无材料</p>
                </div>
              </div>
            </div>

            <!-- Right: Material detail panel -->
            <div class="w-64 border-l border-edge/30 bg-panel/50 flex flex-col overflow-hidden flex-shrink-0">
              <div v-if="previewMaterial" class="flex-1 flex flex-col p-4 overflow-y-auto">
                <!-- Image -->
                <div class="w-full h-32 rounded-xl bg-abyss border border-edge/30 overflow-hidden mb-3 flex items-center justify-center">
                  <img
                    v-if="previewMaterial.image_url"
                    :src="previewMaterial.image_url"
                    :alt="previewMaterial.label"
                    class="w-full h-full object-cover"
                  />
                  <svg v-else class="w-10 h-10 text-edge-light" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h16c1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 2.75c1.24 0 2.25 1.01 2.25 2.25s-1.01 2.25-2.25 2.25S9.75 8.24 9.75 7s1.01-2.25 2.25-2.25zM17 17H7v-1.5c0-1.67 3.33-2.5 5-2.5s5 .83 5 2.5V17z"/>
                  </svg>
                </div>

                <!-- Name -->
                <h3 class="font-display font-semibold text-mist text-sm">{{ previewMaterial.label }}</h3>

                <!-- Price -->
                <p class="text-amber font-bold text-sm font-mono mt-1.5">¥{{ previewMaterial.price }}/{{ previewMaterial.unit }}</p>

                <!-- Category tag -->
                <span
                  v-if="previewMaterial.category"
                  class="inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-mono text-teal border border-teal/20 bg-teal/8"
                >{{ MATERIAL_CATEGORIES.find(c => c.id === previewMaterial!.category)?.labelZh || previewMaterial!.category }}</span>

                <!-- Description -->
                <p v-if="previewMaterial.description" class="text-xs text-ghost/70 mt-3 leading-relaxed">
                  {{ previewMaterial.description }}
                </p>
                <p v-else class="text-xs text-ghost/30 mt-3 italic">暂无材料介绍</p>
              </div>

              <!-- Empty state -->
              <div v-else class="flex-1 flex items-center justify-center p-4">
                <p class="text-xs text-ghost/30 text-center">点击左侧材料查看详情</p>
              </div>

              <!-- Confirm button -->
              <div class="p-4 border-t border-edge/30 flex-shrink-0">
                <button
                  @click="confirm"
                  :disabled="!previewMaterial"
                  :class="[
                    'w-full py-2.5 rounded-xl text-sm font-display font-semibold transition-all duration-300',
                    previewMaterial
                      ? 'btn-primary'
                      : 'bg-elevated text-ghost/40 cursor-not-allowed'
                  ]"
                >确认选择</button>
              </div>
            </div>
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
