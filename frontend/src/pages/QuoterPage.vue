<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { QuoteResponse, QuoteParams, MeshDimensions } from '../types/api'
import { useQuoteApi } from '../composables/useQuoteApi'
import FileUpload from '../components/FileUpload.vue'
import FilePreviewCard from '../components/FilePreviewCard.vue'
import PreviewModal from '../components/PreviewModal.vue'
import ParameterPanel from '../components/ParameterPanel.vue'
import QuoteResult from '../components/QuoteResult.vue'

const { submitQuote, convertToStl } = useQuoteApi()

type Stage = 'upload' | 'configure'
const stage = ref<Stage>('upload')

const selectedFile = ref<File | null>(null)
const previewFile = ref<File | Blob | null>(null)
const modelInfo = ref<{ vertices: number; triangles: number } | null>(null)
const meshAnalysis = ref<MeshDimensions | null>(null)
const params = reactive<QuoteParams>({
  process: 'fdm',
  material: 'PLA',
  quality: 'standard',
  quantity: 1,
  post_processing: [],
  delivery: 'express',
})
const quoteResult = ref<QuoteResponse | null>(null)
const isLoading = ref(false)
const isConverting = ref(false)
const error = ref('')

const showPreviewModal = ref(false)
const modelDimensions = ref<MeshDimensions | null>(null)

const CAD_EXTENSIONS = ['.stp', '.step']

function isCadFile(file: File): boolean {
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  return CAD_EXTENSIONS.includes(ext)
}

async function onFileSelected(file: File) {
  selectedFile.value = file
  quoteResult.value = null
  error.value = ''
  stage.value = 'configure'

  if (isCadFile(file)) {
    isConverting.value = true
    try {
      const stlBlob = await convertToStl(file)
      previewFile.value = new File([stlBlob], file.name.replace(/\.\w+$/, '.stl'), { type: 'application/octet-stream' })
    } catch (e: unknown) {
      previewFile.value = null
      error.value = `STEP 预览转换失败: ${e instanceof Error ? e.message : '未知错误'}，仍可获取报价`
    } finally {
      isConverting.value = false
    }
  } else {
    previewFile.value = file
  }
}

function onParamsChanged(newParams: QuoteParams) {
  Object.assign(params, newParams)
}

async function onSubmit() {
  if (!selectedFile.value) return
  isLoading.value = true
  error.value = ''

  try {
    const result = await submitQuote(selectedFile.value, { ...params })
    quoteResult.value = result
    if (result.analysis?.bounding_box) {
      modelDimensions.value = result.analysis.bounding_box
    }
    if (result.analysis) {
      modelInfo.value = {
        vertices: result.analysis.vertex_count,
        triangles: result.analysis.triangle_count,
      }
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '报价请求失败'
  } finally {
    isLoading.value = false
  }
}

function onReset() {
  selectedFile.value = null
  previewFile.value = null
  quoteResult.value = null
  modelInfo.value = null
  modelDimensions.value = null
  error.value = ''
  stage.value = 'upload'
}
</script>

<template>
  <div class="relative">
    <!-- Stage 1: Upload Hero -->
    <div v-if="stage === 'upload'" class="min-h-[calc(100vh-3.5rem)] flex flex-col items-center justify-center relative overflow-hidden">
      <!-- Background grid -->
      <div class="absolute inset-0 bg-blueprint opacity-40"></div>
      <!-- Radial glow -->
      <div class="absolute inset-0" style="background: radial-gradient(ellipse at 50% 40%, rgba(0,229,199,0.06) 0%, transparent 60%);"></div>

      <div class="relative z-10 flex flex-col items-center animate-fade-in-up">
        <!-- Title area -->
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

        <FileUpload @file-selected="onFileSelected" />
      </div>

      <!-- Decorative corner elements -->
      <div class="absolute top-20 left-8 w-20 h-20 border-t border-l border-edge/30"></div>
      <div class="absolute bottom-20 right-8 w-20 h-20 border-b border-r border-edge/30"></div>
    </div>

    <!-- Stage 2: Configure + Quote -->
    <div v-else class="max-w-[1440px] mx-auto px-6 py-8">
      <!-- Top bar: back + filename -->
      <div class="flex items-center justify-between mb-8 animate-fade-in-up">
        <button
          @click="onReset"
          class="btn-ghost flex items-center gap-2 px-4 py-2 text-sm"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" /></svg>
          <span>返回上传</span>
        </button>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-edge/50">
          <svg class="w-3.5 h-3.5 text-teal" viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/></svg>
          <span class="text-xs font-mono text-mist">{{ selectedFile?.name }}</span>
        </div>
      </div>

      <!-- Main grid: Preview + Config -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: File preview + results -->
        <div class="lg:col-span-8 space-y-6">
          <!-- File preview card -->
          <div class="animate-fade-in-up stagger-1">
            <FilePreviewCard
              :fileName="selectedFile?.name || ''"
              :file="previewFile"
              :dimensions="modelDimensions ? { x: modelDimensions.x_mm, y: modelDimensions.y_mm, z: modelDimensions.z_mm } : null"
              :volume="quoteResult?.analysis?.volume_mm3 ?? null"
              :vertices="modelInfo?.vertices ?? null"
              :triangles="modelInfo?.triangles ?? null"
              @preview-click="showPreviewModal = true"
              @reset="onReset"
            />
          </div>

          <!-- STEP conversion indicator -->
          <div v-if="isConverting" class="flex items-center justify-center gap-3 py-4 glass-panel-sm px-4 animate-fade-in-up">
            <div class="w-5 h-5 border-2 border-teal border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm font-medium text-teal font-mono">正在转换 STEP 文件...</span>
          </div>

          <!-- Error display -->
          <div v-if="error" class="p-4 rounded-xl border border-danger/30 bg-danger/5 text-danger text-sm animate-fade-in-up flex items-start gap-3">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
            <span>{{ error }}</span>
          </div>

          <!-- Loading state -->
          <div v-if="isLoading" class="glass-panel p-8 flex flex-col items-center justify-center gap-4 animate-fade-in-up">
            <div class="relative">
              <div class="w-12 h-12 border-2 border-teal/20 rounded-full"></div>
              <div class="w-12 h-12 border-2 border-teal border-t-transparent rounded-full animate-spin absolute inset-0"></div>
            </div>
            <div class="text-center">
              <p class="text-sm font-medium text-mist">正在分析模型</p>
              <p class="text-xs text-ghost mt-1 font-mono">计算报价中...</p>
            </div>
          </div>

          <!-- Quote result -->
          <div v-if="quoteResult && !isLoading" class="animate-fade-in-up">
            <QuoteResult :result="quoteResult" @reset="onReset" />
          </div>
        </div>

        <!-- Right: Parameter panel (sticky) -->
        <div class="lg:col-span-4">
          <div class="sticky top-20">
            <div class="glass-panel p-6 glow-teal animate-slide-in-right stagger-3">
              <div class="flex items-center gap-2 mb-5">
                <div class="w-1 h-4 rounded-full bg-teal"></div>
                <h3 class="font-display font-semibold text-white text-sm tracking-wide">报价配置</h3>
              </div>
              <ParameterPanel
                :disabled="isLoading"
                @params-changed="onParamsChanged"
                @submit="onSubmit"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Fullscreen preview modal -->
      <PreviewModal
        :visible="showPreviewModal"
        :file="previewFile"
        @close="showPreviewModal = false"
      />
    </div>
  </div>
</template>
