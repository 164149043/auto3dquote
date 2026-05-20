<script setup lang="ts">
import { ref } from 'vue'
import { COLOR_PALETTE, type ColorSwatch } from '../data/pantone-colors'

const props = defineProps<{
  selectedColor: string | null
}>()

const emit = defineEmits<{
  select: [color: { hex: string; name: string; pantoneCode?: string }]
}>()

const customHex = ref('')

function selectColor(swatch: ColorSwatch) {
  emit('select', { hex: swatch.hex, name: swatch.nameZh, pantoneCode: swatch.pantoneCode })
}

function selectCustom() {
  if (customHex.value) {
    emit('select', { hex: customHex.value, name: customHex.value })
  }
}

const basicColors = COLOR_PALETTE.filter(c => c.category === 'basic')
const industrialColors = COLOR_PALETTE.filter(c => c.category === 'industrial')
const metallicColors = COLOR_PALETTE.filter(c => c.category === 'metallic')
</script>

<template>
  <div class="space-y-4">
    <!-- Basic colors -->
    <div>
      <p class="text-[10px] text-ghost uppercase tracking-wider mb-2 font-mono">基础色</p>
      <div class="grid grid-cols-8 gap-1.5">
        <button
          v-for="c in basicColors"
          :key="c.hex"
          @click="selectColor(c)"
          :class="[
            'w-8 h-8 rounded-lg border-2 transition-all duration-200 hover:scale-110',
            selectedColor?.toLowerCase() === c.hex.toLowerCase()
              ? 'border-teal ring-1 ring-teal/40 scale-110'
              : 'border-edge/50 hover:border-edge'
          ]"
          :style="{ backgroundColor: c.hex }"
          :title="`${c.nameZh} (${c.nameEn})`"
        >
          <svg
            v-if="selectedColor?.toLowerCase() === c.hex.toLowerCase()"
            class="w-4 h-4 mx-auto"
            :class="['#FFFFFF', '#FFFF00', '#FFC0CB', '#C0C0C0', '#E8E8E8'].includes(c.hex) ? 'text-void' : 'text-white'"
            viewBox="0 0 20 20"
            fill="currentColor"
          ><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
        </button>
      </div>
    </div>

    <!-- Industrial colors -->
    <div>
      <p class="text-[10px] text-ghost uppercase tracking-wider mb-2 font-mono">工业色</p>
      <div class="grid grid-cols-8 gap-1.5">
        <button
          v-for="c in industrialColors"
          :key="c.hex"
          @click="selectColor(c)"
          :class="[
            'w-8 h-8 rounded-lg border-2 transition-all duration-200 hover:scale-110',
            selectedColor?.toLowerCase() === c.hex.toLowerCase()
              ? 'border-teal ring-1 ring-teal/40 scale-110'
              : 'border-edge/50 hover:border-edge'
          ]"
          :style="{ backgroundColor: c.hex }"
          :title="`${c.nameZh} (${c.nameEn})`"
        >
          <svg
            v-if="selectedColor?.toLowerCase() === c.hex.toLowerCase()"
            class="w-4 h-4 mx-auto text-white"
            viewBox="0 0 20 20"
            fill="currentColor"
          ><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
        </button>
      </div>
    </div>

    <!-- Metallic colors -->
    <div>
      <p class="text-[10px] text-ghost uppercase tracking-wider mb-2 font-mono">金属色</p>
      <div class="grid grid-cols-8 gap-1.5">
        <button
          v-for="c in metallicColors"
          :key="c.hex"
          @click="selectColor(c)"
          :class="[
            'w-8 h-8 rounded-lg border-2 transition-all duration-200 hover:scale-110',
            selectedColor?.toLowerCase() === c.hex.toLowerCase()
              ? 'border-teal ring-1 ring-teal/40 scale-110'
              : 'border-edge/50 hover:border-edge'
          ]"
          :style="{ backgroundColor: c.hex }"
          :title="`${c.nameZh} (${c.nameEn})`"
        >
          <svg
            v-if="selectedColor?.toLowerCase() === c.hex.toLowerCase()"
            class="w-4 h-4 mx-auto text-white"
            viewBox="0 0 20 20"
            fill="currentColor"
          ><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
        </button>
      </div>
    </div>

    <!-- Custom color -->
    <div class="flex items-center gap-3 pt-1">
      <p class="text-[10px] text-ghost uppercase tracking-wider font-mono">自定义</p>
      <input
        type="color"
        v-model="customHex"
        class="w-8 h-8 rounded-lg border border-edge/50 cursor-pointer bg-transparent"
        @change="selectCustom"
      />
      <span v-if="customHex" class="text-xs text-ghost font-mono">{{ customHex }}</span>
    </div>
  </div>
</template>
