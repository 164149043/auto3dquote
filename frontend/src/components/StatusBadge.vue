<script setup lang="ts">
defineProps<{
  status: 'success' | 'warning' | 'partial'
}>()

const statusConfig: Record<string, { label: string; dotClass: string; textClass: string }> = {
  success: { label: '成功', dotClass: 'bg-teal', textClass: 'text-teal' },
  warning: { label: '有警告', dotClass: 'bg-amber', textClass: 'text-amber' },
  partial: { label: '部分结果', dotClass: 'bg-amber-dim', textClass: 'text-amber' },
}
</script>

<template>
  <span :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium', statusConfig[status]?.textClass]"
    style="background: rgba(0,0,0,0.3);">
    <span class="w-1.5 h-1.5 rounded-full" :class="statusConfig[status]?.dotClass"></span>
    {{ statusConfig[status]?.label }}
  </span>
</template>
