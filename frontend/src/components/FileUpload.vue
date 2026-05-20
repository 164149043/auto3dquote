<script setup lang="ts">
import { ref } from 'vue'
import { formatFileSize } from '../utils/format'

const emit = defineEmits<{
  'file-selected': [file: File]
}>()

const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const error = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const ALLOWED_EXTENSIONS = ['.stl', '.obj', '.3mf', '.stp', '.step']
const MAX_SIZE_MB = 100

function validateFile(file: File): string | null {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `不支持的文件格式: ${ext}，支持: ${ALLOWED_EXTENSIONS.join(', ')}`
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `文件过大: ${(file.size / 1024 / 1024).toFixed(1)}MB，上限: ${MAX_SIZE_MB}MB`
  }
  return null
}

function handleFile(file: File) {
  error.value = ''
  const err = validateFile(file)
  if (err) {
    error.value = err
    return
  }
  selectedFile.value = file
  emit('file-selected', file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

function onDragOver() { isDragging.value = true }
function onDragLeave() { isDragging.value = false }

function onFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) handleFile(file)
}

function reset() {
  selectedFile.value = null
  error.value = ''
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<template>
  <div class="w-full max-w-xl mx-auto">
    <!-- Upload zone -->
    <div
      v-if="!selectedFile"
      @drop.prevent="onDrop"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      :class="[
        'relative border-2 border-dashed rounded-2xl p-16 text-center cursor-pointer transition-all duration-300 group',
        isDragging
          ? 'border-teal bg-teal-glass scale-[1.01]'
          : 'border-edge/50 bg-panel/40 hover:border-teal/50 hover:bg-teal-glass'
      ]"
      @click="fileInput?.click()"
    >
      <!-- Corner markers -->
      <div class="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 transition-colors duration-300"
        :class="isDragging ? 'border-teal' : 'border-edge/40 group-hover:border-teal/50'"></div>
      <div class="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 transition-colors duration-300"
        :class="isDragging ? 'border-teal' : 'border-edge/40 group-hover:border-teal/50'"></div>
      <div class="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 transition-colors duration-300"
        :class="isDragging ? 'border-teal' : 'border-edge/40 group-hover:border-teal/50'"></div>
      <div class="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 transition-colors duration-300"
        :class="isDragging ? 'border-teal' : 'border-edge/40 group-hover:border-teal/50'"></div>

      <!-- Icon -->
      <div class="mb-5 transition-transform duration-300"
        :class="isDragging ? 'scale-110' : 'group-hover:scale-105'">
        <svg class="w-14 h-14 mx-auto" :class="isDragging ? 'text-teal' : 'text-edge-light group-hover:text-teal/70'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>

      <p class="text-lg font-display font-semibold text-mist mb-2">
        {{ isDragging ? '释放文件以上传' : '拖拽文件到此处' }}
      </p>
      <p v-if="!isDragging" class="text-sm text-ghost mb-4">
        或 <span class="text-teal underline underline-offset-4 decoration-teal/40">点击选择文件</span>
      </p>

      <input
        ref="fileInput"
        type="file"
        accept=".stl,.obj,.3mf,.stp,.step"
        class="hidden"
        @change="onFileInput"
      />
    </div>

    <!-- File selected state -->
    <div v-else class="glass-panel-sm p-5 flex items-center gap-4">
      <div class="w-10 h-10 rounded-lg bg-teal/10 border border-teal/20 flex items-center justify-center flex-shrink-0">
        <svg class="w-5 h-5 text-teal" viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/></svg>
      </div>
      <div class="flex-1 min-w-0">
        <p class="font-medium text-mist text-sm truncate">{{ selectedFile.name }}</p>
        <p class="text-xs text-ghost font-mono mt-0.5">{{ formatFileSize(selectedFile.size) }}</p>
      </div>
      <button
        @click="reset"
        class="btn-ghost px-3 py-1.5 text-xs"
      >
        重新选择
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-4 text-sm text-danger text-center flex items-center justify-center gap-2">
      <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
      {{ error }}
    </div>
  </div>
</template>
