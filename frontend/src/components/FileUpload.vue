<script setup lang="ts">
import { ref } from 'vue'
import { formatFileSize } from '../utils/format'

const MAX_FILES = 10

const emit = defineEmits<{
  'files-selected': [files: File[]]
  'file-removed': [index: number]
}>()

const files = ref<File[]>([])
const isDragging = ref(false)
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

function addFiles(newFiles: FileList | File[]) {
  error.value = ''
  const toAdd: File[] = []

  for (const file of Array.from(newFiles)) {
    if (files.value.length + toAdd.length >= MAX_FILES) {
      error.value = `最多同时上传 ${MAX_FILES} 个文件`
      break
    }
    const err = validateFile(file)
    if (err) {
      error.value = err
      continue
    }
    // 避免重复文件名
    if (files.value.some(f => f.name === file.name) || toAdd.some(f => f.name === file.name)) {
      error.value = `文件已存在: ${file.name}`
      continue
    }
    toAdd.push(file)
  }

  if (toAdd.length > 0) {
    files.value = [...files.value, ...toAdd]
    emit('files-selected', files.value)
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  emit('file-removed', index)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files.length) addFiles(e.dataTransfer.files)
}

function onDragOver() { isDragging.value = true }
function onDragLeave() { isDragging.value = false }

function onFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) addFiles(input.files)
  input.value = ''
}

</script>

<template>
  <div class="w-full max-w-2xl mx-auto">
    <!-- Upload zone -->
    <div
      @drop.prevent="onDrop"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      :class="[
        'relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 group',
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

      <div class="mb-4 transition-transform duration-300"
        :class="isDragging ? 'scale-110' : 'group-hover:scale-105'">
        <svg class="w-12 h-12 mx-auto" :class="isDragging ? 'text-teal' : 'text-edge-light group-hover:text-teal/70'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>

      <p class="text-base font-display font-semibold text-mist mb-1">
        {{ isDragging ? '释放文件以上传' : '拖拽文件到此处' }}
      </p>
      <p v-if="!isDragging" class="text-sm text-ghost">
        或 <span class="text-teal underline underline-offset-4 decoration-teal/40">点击选择文件</span>
        <span class="text-ghost/50 ml-2">支持多选，最多 {{ MAX_FILES }} 个</span>
      </p>

      <input
        ref="fileInput"
        type="file"
        accept=".stl,.obj,.3mf,.stp,.step"
        multiple
        class="hidden"
        @change="onFileInput"
      />
    </div>

    <!-- File list -->
    <div v-if="files.length > 0" class="mt-4 space-y-2">
      <div
        v-for="(file, idx) in files"
        :key="file.name + idx"
        class="glass-panel-sm px-4 py-3 flex items-center gap-3"
      >
        <div class="w-8 h-8 rounded-lg bg-teal/10 border border-teal/20 flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-teal" viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/></svg>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-medium text-mist text-sm truncate">{{ file.name }}</p>
          <p class="text-xs text-ghost font-mono">{{ formatFileSize(file.size) }}</p>
        </div>
        <button
          @click.stop="removeFile(idx)"
          class="w-7 h-7 rounded-lg flex items-center justify-center text-ghost hover:text-danger hover:bg-danger/10 transition-all"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mt-3 text-sm text-danger text-center flex items-center justify-center gap-2">
      <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
      {{ error }}
    </div>
  </div>
</template>
