<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { listMachineLimits, updateMachineLimits } = useAdminApi()

const limits = ref<Array<Record<string, unknown>>>([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const editingId = ref<string | null>(null)
const editForm = ref({ max_x: 0, max_y: 0, max_z: 0 })

const PROCESSES = [
  { id: 'fdm', label: 'FDM' },
  { id: 'sla', label: 'SLA' },
  { id: 'sls', label: 'SLS' },
  { id: 'mjf', label: 'MJF' },
  { id: 'cnc', label: 'CNC' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    limits.value = await listMachineLimits()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function startEdit(limit: Record<string, unknown>) {
  editingId.value = limit.process_id as string
  editForm.value = {
    max_x: limit.max_x as number,
    max_y: limit.max_y as number,
    max_z: limit.max_z as number,
  }
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(processId: string) {
  saving.value = true
  try {
    await updateMachineLimits(processId, editForm.value)
    editingId.value = null
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

function processLabel(id: string): string {
  return PROCESSES.find(p => p.id === id)?.label || id
}

onMounted(load)
</script>

<template>
  <div>
    <h3 class="text-lg font-semibold text-gray-800 mb-4">设备体积限制</h3>

    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">加载中...</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="limit in limits"
        :key="limit.process_id as string"
        class="p-4 border border-gray-200 rounded-xl"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="font-medium text-gray-700">{{ processLabel(limit.process_id as string) }}</span>
          <button
            v-if="editingId !== limit.process_id"
            class="text-blue-600 hover:text-blue-800 text-sm font-medium"
            @click="startEdit(limit)"
          >
            编辑
          </button>
        </div>

        <template v-if="editingId === limit.process_id">
          <div class="space-y-2">
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-500 w-12">X:</span>
              <input v-model.number="editForm.max_x" type="number" class="flex-1 px-2 py-1 border rounded text-sm" /> mm
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-500 w-12">Y:</span>
              <input v-model.number="editForm.max_y" type="number" class="flex-1 px-2 py-1 border rounded text-sm" /> mm
            </div>
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-500 w-12">Z:</span>
              <input v-model.number="editForm.max_z" type="number" class="flex-1 px-2 py-1 border rounded text-sm" /> mm
            </div>
            <div class="flex gap-2 pt-1">
              <button
                :disabled="saving"
                class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg disabled:bg-gray-400"
                @click="saveEdit(limit.process_id as string)"
              >
                保存
              </button>
              <button class="px-3 py-1 bg-gray-200 text-gray-600 text-xs rounded-lg" @click="cancelEdit">取消</button>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="text-sm text-gray-600 space-y-1">
            <div>X: {{ limit.max_x }} mm</div>
            <div>Y: {{ limit.max_y }} mm</div>
            <div>Z: {{ limit.max_z }} mm</div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
