<script setup lang="ts">
import { ref, computed } from 'vue'
import FileUpload from '../components/FileUpload.vue'
import QuoteCard from '../components/QuoteCard.vue'
import { formatPrice } from '../utils/format'
import { useAuth } from '../composables/useAuth'

const { isAuthenticated, openLoginModal } = useAuth()

type Stage = 'upload' | 'configure'
const stage = ref<Stage>('upload')

const files = ref<File[]>([])
const addFileInput = ref<HTMLInputElement | null>(null)

const ALLOWED_EXTENSIONS = ['.stl', '.obj', '.3mf', '.stp', '.step']
const MAX_SIZE_MB = 100

const priceMap = ref<Map<string, number | null>>(new Map())

function onUploadFilesSelected(newFiles: File[]) {
  files.value = newFiles
  for (const file of newFiles) {
    if (!priceMap.value.has(file.name)) {
      priceMap.value.set(file.name, null)
    }
  }
  if (newFiles.length > 0) {
    stage.value = 'configure'
  }
}

function onUploadFileRemoved(index: number) {
  const removed = files.value[index]
  if (removed) priceMap.value.delete(removed.name)
  files.value.splice(index, 1)
  if (files.value.length === 0) stage.value = 'upload'
}

function removeCard(index: number) {
  const removed = files.value[index]
  if (removed) priceMap.value.delete(removed.name)
  files.value.splice(index, 1)
  if (files.value.length === 0) stage.value = 'upload'
}

function onAddFiles(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return

  const toAdd: File[] = []
  for (const file of Array.from(input.files)) {
    if (files.value.length + toAdd.length >= 10) break
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) continue
    if (file.size > MAX_SIZE_MB * 1024 * 1024) continue
    if (files.value.some(f => f.name === file.name) || toAdd.some(f => f.name === file.name)) continue
    toAdd.push(file)
  }

  for (const file of toAdd) {
    priceMap.value.set(file.name, null)
  }
  files.value = [...files.value, ...toAdd]
  input.value = ''
}

function onPriceChanged(fileName: string, price: number | null) {
  priceMap.value.set(fileName, price)
}

const totalPrice = computed(() => {
  let sum = 0
  for (const price of priceMap.value.values()) {
    if (price !== null) sum += price
  }
  return sum
})

const quotedCount = computed(() => {
  let count = 0
  for (const price of priceMap.value.values()) {
    if (price !== null) count++
  }
  return count
})

function onReset() {
  files.value = []
  priceMap.value.clear()
  stage.value = 'upload'
}
</script>

<template>
  <div class="relative">
    <!-- 未登录提示 -->
    <div v-if="!isAuthenticated" class="min-h-[calc(100vh-3.5rem)] flex flex-col items-center justify-center relative overflow-hidden">
      <div class="absolute inset-0 bg-blueprint opacity-40"></div>
      <div class="absolute inset-0" style="background: radial-gradient(ellipse at 50% 40%, rgba(0,229,199,0.06) 0%, transparent 60%);"></div>

      <div class="relative z-10 flex flex-col items-center text-center animate-fade-in-up">
        <div class="w-16 h-16 rounded-2xl bg-teal/10 flex items-center justify-center mb-6">
          <svg class="w-8 h-8 text-teal" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h2 class="font-display text-3xl md:text-4xl font-bold text-white mb-3 tracking-tight">
          请登录后使用报价服务
        </h2>
        <p class="text-silver/70 text-base max-w-md mx-auto leading-relaxed mb-8">
          登录您的账号即可上传 3D 模型，获取精确的打印报价
        </p>
        <button
          @click="openLoginModal"
          class="btn-primary px-8 py-3 text-sm font-medium"
        >
          立即登录
        </button>
      </div>
    </div>

    <!-- 已登录：正常报价流程 -->
    <template v-else>
    <!-- Stage 1: Upload Hero -->
    <div v-if="stage === 'upload'" class="min-h-[calc(100vh-3.5rem)] flex flex-col items-center justify-center relative overflow-hidden">
      <div class="absolute inset-0 bg-blueprint opacity-40"></div>
      <div class="absolute inset-0" style="background: radial-gradient(ellipse at 50% 40%, rgba(0,229,199,0.06) 0%, transparent 60%);"></div>

      <div class="relative z-10 flex flex-col items-center animate-fade-in-up">
        <div class="text-center mb-10 stagger-1">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-edge/50 bg-panel/50 mb-6">
            <span class="w-1.5 h-1.5 rounded-full bg-teal animate-pulse-teal"></span>
            <span class="text-xs font-mono text-ghost tracking-wider uppercase">系统就绪</span>
          </div>
          <h2 class="font-display text-4xl md:text-5xl font-bold text-white mb-3 tracking-tight">
            上传 3D 模型
          </h2>
          <p class="text-silver/70 text-base max-w-md mx-auto leading-relaxed">
            拖拽或选择文件，即刻获取精确的 3D 打印报价
          </p>
          <div class="flex items-center justify-center gap-3 mt-4">
            <span class="px-2.5 py-1 rounded-md bg-surface text-xs font-mono text-ghost">STL</span>
            <span class="px-2.5 py-1 rounded-md bg-surface text-xs font-mono text-ghost">OBJ</span>
            <span class="px-2.5 py-1 rounded-md bg-surface text-xs font-mono text-ghost">3MF</span>
            <span class="px-2.5 py-1 rounded-md bg-surface text-xs font-mono text-ghost">STEP</span>
            <span class="text-xs text-ghost/40">≤ 100MB</span>
          </div>
        </div>

        <FileUpload
          @files-selected="onUploadFilesSelected"
          @file-removed="onUploadFileRemoved"
        />
      </div>

      <div class="absolute top-20 left-8 w-20 h-20 border-t border-l border-edge/30"></div>
      <div class="absolute bottom-20 right-8 w-20 h-20 border-b border-r border-edge/30"></div>
    </div>

    <!-- Stage 2: Cards + Total -->
    <div v-else class="max-w-[1440px] mx-auto px-6 py-8 pb-32">
      <!-- Top bar -->
      <div class="flex items-center justify-between mb-6 animate-fade-in-up">
        <button
          @click="onReset"
          class="btn-ghost flex items-center gap-2 px-4 py-2 text-sm"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" /></svg>
          <span>返回上传</span>
        </button>
        <div class="flex items-center gap-4">
          <span class="text-xs font-mono text-ghost">{{ files.length }} 个文件</span>
          <span v-if="quotedCount > 0" class="text-xs font-mono text-amber">{{ quotedCount }} 已报价</span>
          <button
            @click="addFileInput?.click()"
            :disabled="files.length >= 10"
            class="px-3 py-1.5 rounded-lg border border-teal/30 text-teal text-xs font-mono hover:bg-teal/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            + 添加文件
          </button>
          <input
            ref="addFileInput"
            type="file"
            accept=".stl,.obj,.3mf,.stp,.step"
            multiple
            class="hidden"
            @change="onAddFiles"
          />
        </div>
      </div>

      <!-- Quote cards -->
      <div class="space-y-4">
        <QuoteCard
          v-for="(file, idx) in files"
          :key="file.name"
          :file="file"
          @remove="removeCard(idx)"
          @price-changed="onPriceChanged(file.name, $event)"
        />
      </div>
    </div>

    <!-- Sticky bottom: total price bar -->
    <Transition name="slide-up">
      <div
        v-if="stage === 'configure' && quotedCount > 0"
        class="fixed bottom-0 left-0 right-0 z-40 border-t border-edge/50"
        style="background: rgba(10,15,30,0.95); backdrop-filter: blur(12px);"
      >
        <div class="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-amber animate-pulse"></span>
              <span class="text-sm font-medium text-mist">合计报价</span>
            </div>
            <span class="text-xs text-ghost font-mono">{{ quotedCount }} 件</span>
          </div>
          <div>
            <p class="text-2xl font-display font-bold number-display" style="color: var(--color-amber);">
              {{ formatPrice(totalPrice) }}
            </p>
          </div>
        </div>
      </div>
    </Transition>
    </template>
  </div>
</template>

<style scoped>
.slide-up-enter-active { transition: all 0.3s ease; }
.slide-up-leave-active { transition: all 0.2s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); opacity: 0; }
</style>
