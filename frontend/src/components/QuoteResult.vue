<script setup lang="ts">
import type { QuoteResponse } from '../types/api'
import { formatPrice, formatFileSize, formatDimensions } from '../utils/format'
import StatusBadge from './StatusBadge.vue'

defineProps<{
  result: QuoteResponse
}>()

defineEmits<{
  reset: []
}>()
</script>

<template>
  <div class="glass-panel overflow-hidden">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-edge/50 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <StatusBadge :status="result.status" />
        <span class="text-xs text-ghost font-mono">{{ result.processing_time_seconds }}s</span>
      </div>
      <button
        @click="$emit('reset')"
        class="btn-ghost px-3 py-1.5 text-xs flex items-center gap-1.5"
      >
        <svg class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg>
        重新报价
      </button>
    </div>

    <!-- Price hero section -->
    <div v-if="result.quote" class="px-6 pt-8 pb-6">
      <div class="text-center mb-8">
        <p class="text-xs text-ghost uppercase tracking-widest mb-3 font-mono">总报价</p>
        <div class="glow-amber inline-block px-8 py-4 rounded-2xl" style="background: linear-gradient(135deg, rgba(245,158,11,0.08) 0%, rgba(245,158,11,0.03) 100%); border: 1px solid rgba(245,158,11,0.15);">
          <p class="text-5xl font-display font-bold number-display" style="color: var(--color-amber);">
            {{ formatPrice(result.quote.total_price) }}
          </p>
        </div>
        <p v-if="result.quote.quantity > 1" class="text-sm text-ghost mt-3 font-mono">
          单价 <span class="text-mist">{{ formatPrice(result.quote.unit_price) }}</span>
          <span v-if="result.quote.quantity_discount > 0" class="text-xs text-ghost/60 line-through ml-1">
            {{ formatPrice(result.quote.unit_price + result.quote.quantity_discount) }}
          </span>
          × {{ result.quote.quantity }}
        </p>
      </div>

      <!-- Cost breakdown -->
      <div class="bg-deep rounded-xl p-4 border border-edge/50 space-y-3">
        <div class="flex justify-between items-center py-1">
          <span class="text-sm text-ghost">材料成本</span>
          <div class="text-right">
            <span class="text-sm font-mono text-mist">{{ formatPrice(result.quote.material_cost.subtotal) }}</span>
            <span class="text-[10px] text-ghost/60 block font-mono">{{ result.quote.material_cost.quantity }}{{ result.quote.material_cost.unit }} × ¥{{ result.quote.material_cost.unit_price }}/{{ result.quote.material_cost.unit }}</span>
          </div>
        </div>
        <div class="flex justify-between items-center py-1">
          <span class="text-sm text-ghost">时间成本</span>
          <div class="text-right">
            <span class="text-sm font-mono text-mist">{{ formatPrice(result.quote.time_cost.subtotal) }}</span>
            <span class="text-[10px] text-ghost/60 block font-mono">{{ result.quote.time_cost.hours }}h × ¥{{ result.quote.time_cost.rate_per_hour }}/h</span>
          </div>
        </div>
        <div v-for="pp in result.quote.post_process_costs" :key="pp.type" class="flex justify-between items-center py-1">
          <span class="text-sm text-ghost">{{ pp.name }}</span>
          <span class="text-sm font-mono text-mist">{{ formatPrice(pp.subtotal) }}</span>
        </div>
        <div v-if="result.quote.delivery_surcharge > 0" class="flex justify-between items-center py-1">
          <span class="text-sm text-ghost">交期加急费</span>
          <span class="text-sm font-mono text-amber">{{ formatPrice(result.quote.delivery_surcharge) }}</span>
        </div>
        <div v-if="result.quote.quantity_discount > 0" class="flex justify-between items-center py-1">
          <span class="text-sm text-ghost">数量折扣 ({{ (result.quote.quantity_discount_rate * 100).toFixed(0) }}% off)</span>
          <span class="text-sm font-mono text-teal">-{{ formatPrice(result.quote.quantity_discount) }}</span>
        </div>

        <div class="border-t border-edge/50 pt-3 mt-2">
          <div class="flex justify-between items-center py-1">
            <span class="text-sm text-ghost">基础价格</span>
            <span class="text-sm font-mono text-mist">{{ formatPrice(result.quote.base_price) }}</span>
          </div>
          <div class="flex justify-between items-center py-1">
            <span class="text-sm text-ghost">加价率</span>
            <span class="text-sm font-mono text-teal">×{{ result.quote.markup_rate }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Partial status notice -->
    <div v-if="result.status === 'partial'" class="px-6 py-3 bg-amber/10 border-t border-amber/20 text-amber text-sm flex items-center gap-2">
      <svg class="w-4 h-4 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
      切片服务暂不可用，仅展示模型分析结果
    </div>

    <!-- Info grid -->
    <div class="grid grid-cols-2 gap-4 p-6 border-t border-edge/30">
      <!-- Model info -->
      <div class="bg-deep rounded-xl p-4 border border-edge/40">
        <h3 class="text-xs font-medium text-teal/80 uppercase tracking-wider mb-3 flex items-center gap-2">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6z"/></svg>
          模型信息
        </h3>
        <dl class="space-y-2.5">
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">尺寸</dt>
            <dd class="text-xs font-mono text-mist number-display">{{ formatDimensions(result.analysis.bounding_box) }}</dd>
          </div>
          <div class="flex justify-between items-center">
            <dt class="text-xs text-ghost">水密</dt>
            <dd :class="result.analysis.is_watertight ? 'text-teal' : 'text-danger'" class="text-xs font-medium flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full" :class="result.analysis.is_watertight ? 'bg-teal' : 'bg-danger'"></span>
              {{ result.analysis.is_watertight ? '是' : '否' }}
            </dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">三角面片</dt>
            <dd class="text-xs font-mono text-mist number-display">{{ result.analysis.triangle_count.toLocaleString() }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">文件大小</dt>
            <dd class="text-xs font-mono text-mist">{{ formatFileSize(result.analysis.file_size_bytes) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Print info -->
      <div class="bg-deep rounded-xl p-4 border border-edge/40">
        <h3 class="text-xs font-medium text-amber/80 uppercase tracking-wider mb-3 flex items-center gap-2">
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5 2a2 2 0 00-2 2v14l3.5-2 3.5 2 3.5-2 3.5 2V4a2 2 0 00-2-2H5zm4.707 3.707a1 1 0 00-1.414-1.414l-3 3a1 1 0 000 1.414l3 3a1 1 0 001.414-1.414L8.414 9H10a3 3 0 013 3v1a1 1 0 102 0v-1a5 5 0 00-5-5H8.414l1.293-1.293z" clip-rule="evenodd" /></svg>
          打印信息
        </h3>
        <dl v-if="result.slicing" class="space-y-2.5">
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">打印时间</dt>
            <dd class="text-xs font-mono text-mist">{{ result.slicing.print_time_formatted }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">耗材重量</dt>
            <dd class="text-xs font-mono text-mist">{{ result.slicing.filament_used_grams }}g</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">层数</dt>
            <dd class="text-xs font-mono text-mist number-display">{{ result.slicing.layer_count }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-xs text-ghost">切片器</dt>
            <dd class="text-xs font-mono text-mist">{{ result.slicing.slicer_version }}</dd>
          </div>
        </dl>
        <p v-else class="text-xs text-ghost/50 italic mt-2">切片数据不可用</p>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="result.warnings.length > 0" class="px-6 pb-4">
      <div v-for="(w, i) in result.warnings" :key="i" class="text-xs text-amber mb-1 flex items-center gap-2">
        <svg class="w-3.5 h-3.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
        {{ w }}
      </div>
    </div>
  </div>
</template>
