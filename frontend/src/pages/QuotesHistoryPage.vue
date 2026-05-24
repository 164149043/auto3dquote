<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useQuoteApi } from '../composables/useQuoteApi'
import { formatPrice } from '../utils/format'
import type { QuoteRecordItem, QuoteRecordDetail } from '../types/api'

const { fetchQuoteRecords, fetchQuoteRecordDetail, deleteQuoteRecord } = useQuoteApi()

const records = ref<QuoteRecordItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const error = ref('')

const expandedId = ref<number | null>(null)
const detail = ref<QuoteRecordDetail | null>(null)
const detailLoading = ref(false)

const deleteConfirmId = ref<number | null>(null)

const PROCESS_LABELS: Record<string, string> = {
  fdm: 'FDM', sla: 'SLA', sls: 'SLS', mjf: 'MJF', cnc: 'CNC',
}

const QUALITY_LABELS: Record<string, string> = {
  draft: '草稿', standard: '标准', high: '高质量',
}

const DELIVERY_LABELS: Record<string, string> = {
  standard: '标准 (3天)', express: '加急 (2天)', urgent: '特急 (1天)',
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchQuoteRecords(page.value, pageSize.value)
    records.value = res.records
    total.value = res.total
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function toggleDetail(id: number) {
  if (expandedId.value === id) {
    expandedId.value = null
    detail.value = null
    return
  }
  expandedId.value = id
  detailLoading.value = true
  try {
    detail.value = await fetchQuoteRecordDetail(id)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载详情失败'
    expandedId.value = null
  } finally {
    detailLoading.value = false
  }
}

async function confirmDelete(id: number) {
  try {
    await deleteQuoteRecord(id)
    deleteConfirmId.value = null
    if (expandedId.value === id) {
      expandedId.value = null
      detail.value = null
    }
    await loadData()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

function changePage(p: number) {
  page.value = p
  loadData()
}

function formatSize(bytes: number | null): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(seconds: number | null): string {
  if (!seconds) return '-'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

onMounted(() => {
  loadData()
})
</script>

<template>
  <main class="max-w-5xl mx-auto px-6 py-8 min-h-[calc(100vh-3.5rem)]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white tracking-tight">我的报价</h1>
        <p class="text-sm text-ghost mt-1">查看历史报价记录和详细信息</p>
      </div>
      <button
        @click="loadData"
        class="btn-ghost px-3 py-2 text-sm"
        :disabled="loading"
      >
        <svg class="w-4 h-4 inline-block mr-1" :class="{ 'animate-spin': loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 11-6.219-8.56"/>
        </svg>
        刷新
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-4 mb-4 text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg">
      {{ error }}
    </div>

    <!-- Empty state -->
    <div v-if="!loading && records.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
      <svg class="w-16 h-16 text-ghost/30 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
      <p class="text-ghost text-sm">暂无报价记录</p>
    </div>

    <!-- Records list -->
    <div v-else class="space-y-3">
      <div
        v-for="record in records"
        :key="record.id"
        class="glass-panel rounded-xl overflow-hidden"
      >
        <!-- Record row -->
        <div class="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-white/[0.02] transition-colors" @click="toggleDetail(record.id)">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium text-white truncate">{{ record.filename }}</span>
              <span class="px-2 py-0.5 rounded text-xs font-mono bg-teal/10 text-teal">{{ PROCESS_LABELS[record.process] || record.process }}</span>
              <span class="text-xs text-ghost">{{ record.material }}</span>
              <span v-if="record.quantity > 1" class="text-xs text-ghost">x{{ record.quantity }}</span>
            </div>
            <p class="text-xs text-ghost/60 mt-1">{{ formatDate(record.created_at) }}</p>
          </div>
          <div class="text-right flex-shrink-0">
            <p class="text-lg font-display font-bold number-display" style="color: var(--color-amber);">
              {{ formatPrice(record.total_price) }}
            </p>
            <p v-if="record.quantity > 1" class="text-xs text-ghost">{{ formatPrice(record.unit_price) }}/件</p>
          </div>
          <!-- Expand icon -->
          <svg
            class="w-5 h-5 text-ghost/40 transition-transform flex-shrink-0"
            :class="{ 'rotate-180': expandedId === record.id }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          >
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </div>

        <!-- Expanded detail -->
        <div v-if="expandedId === record.id" class="border-t border-edge/30 px-5 py-4">
          <div v-if="detailLoading" class="text-center text-sm text-ghost py-4">加载中...</div>
          <div v-else-if="detail" class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <!-- 订单参数 -->
            <div>
              <p class="text-ghost text-xs mb-1">质量</p>
              <p class="text-white font-medium">{{ QUALITY_LABELS[detail.quality] || detail.quality }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">交期</p>
              <p class="text-white font-medium">{{ DELIVERY_LABELS[detail.delivery] || detail.delivery }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">后处理选项</p>
              <p class="text-white font-medium">{{ detail.post_processing || '无' }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">处理耗时</p>
              <p class="text-white font-medium">{{ detail.processing_time_seconds.toFixed(1) }}s</p>
            </div>

            <!-- 成本明细 -->
            <div>
              <p class="text-ghost text-xs mb-1">材料成本</p>
              <p class="text-white font-medium">{{ formatPrice(detail.material_cost) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">时间成本</p>
              <p class="text-white font-medium">{{ formatPrice(detail.time_cost) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">后处理费用</p>
              <p class="text-white font-medium">{{ formatPrice(detail.post_process_cost) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">交期加急</p>
              <p class="text-white font-medium">{{ formatPrice(detail.delivery_surcharge) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">难度加价</p>
              <p class="text-white font-medium">{{ formatPrice(detail.difficulty_surcharge) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">支撑成本</p>
              <p class="text-white font-medium">{{ formatPrice(detail.support_cost) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">数量折扣</p>
              <p class="text-teal font-medium">-{{ formatPrice(detail.quantity_discount) }}</p>
            </div>

            <!-- 模型信息 -->
            <div>
              <p class="text-ghost text-xs mb-1">体积</p>
              <p class="text-white font-medium">{{ (detail.volume_mm3 / 1000).toFixed(2) }} cm³</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">表面积</p>
              <p class="text-white font-medium">{{ (detail.surface_area_mm2 / 100).toFixed(2) }} cm²</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">文件大小</p>
              <p class="text-white font-medium">{{ formatSize(detail.file_size_bytes) }}</p>
            </div>
            <div>
              <p class="text-ghost text-xs mb-1">打印时间</p>
              <p class="text-white font-medium">{{ formatTime(detail.print_time_seconds) }}</p>
            </div>
          </div>

          <!-- Delete button -->
          <div class="mt-4 pt-3 border-t border-edge/20 flex justify-end">
            <template v-if="deleteConfirmId === record.id">
              <span class="text-xs text-ghost mr-3 self-center">确认删除？</span>
              <button @click.stop="confirmDelete(record.id)" class="px-3 py-1.5 text-xs bg-danger/20 text-danger rounded-lg hover:bg-danger/30 transition-colors">确认</button>
              <button @click.stop="deleteConfirmId = null" class="ml-2 px-3 py-1.5 text-xs bg-surface text-ghost rounded-lg hover:bg-panel transition-colors">取消</button>
            </template>
            <button v-else @click.stop="deleteConfirmId = record.id" class="px-3 py-1.5 text-xs text-ghost hover:text-danger hover:bg-danger/10 rounded-lg transition-colors">
              删除记录
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-8">
      <button
        @click="changePage(page - 1)"
        :disabled="page <= 1"
        class="px-3 py-2 text-sm rounded-lg border border-edge/30 text-ghost hover:text-white hover:border-edge/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
      >
        上一页
      </button>
      <span class="text-sm text-ghost font-mono">{{ page }} / {{ totalPages }}</span>
      <button
        @click="changePage(page + 1)"
        :disabled="page >= totalPages"
        class="px-3 py-2 text-sm rounded-lg border border-edge/30 text-ghost hover:text-white hover:border-edge/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
      >
        下一页
      </button>
    </div>
  </main>
</template>
