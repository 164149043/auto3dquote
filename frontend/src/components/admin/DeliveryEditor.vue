<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { listDeliveryOptions, updateDeliveryOption } = useAdminApi()

const options = ref<Array<Record<string, unknown>>>([])
const loading = ref(false)
const error = ref('')
const editingId = ref<string | null>(null)
const editForm = ref<Record<string, unknown>>({})

async function load() {
  loading.value = true
  error.value = ''
  try {
    options.value = await listDeliveryOptions()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function startEdit(opt: Record<string, unknown>) {
  editingId.value = opt.id as string
  editForm.value = { ...opt }
}

function cancelEdit() {
  editingId.value = null
  editForm.value = {}
}

async function saveEdit() {
  try {
    await updateDeliveryOption(editingId.value!, editForm.value)
    editingId.value = null
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h3 class="text-lg font-semibold text-gray-800 mb-4">交期选项</h3>

    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">加载中...</div>

    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 text-left text-gray-600">
            <th class="py-2 px-2">ID</th>
            <th class="py-2 px-2">显示名</th>
            <th class="py-2 px-2">加价倍率</th>
            <th class="py-2 px-2">天数</th>
            <th class="py-2 px-2">排序</th>
            <th class="py-2 px-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="opt in options" :key="opt.id as string" class="border-b border-gray-100 hover:bg-gray-50">
            <template v-if="editingId === opt.id">
              <td class="py-2 px-2 font-mono text-xs">{{ opt.id }}</td>
              <td class="py-2 px-2"><input v-model="editForm.label" class="w-full px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2"><input v-model.number="editForm.multiplier" type="number" step="0.01" class="w-24 px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2"><input v-model.number="editForm.days" type="number" class="w-20 px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2"><input v-model.number="editForm.sort_order" type="number" class="w-16 px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2 text-right space-x-2">
                <button class="text-green-600 hover:text-green-800 text-sm font-medium" @click="saveEdit">保存</button>
                <button class="text-gray-500 hover:text-gray-700 text-sm" @click="cancelEdit">取消</button>
              </td>
            </template>
            <template v-else>
              <td class="py-2 px-2 font-mono text-xs text-gray-500">{{ opt.id }}</td>
              <td class="py-2 px-2 font-medium">{{ opt.label }}</td>
              <td class="py-2 px-2">{{ opt.multiplier }}x</td>
              <td class="py-2 px-2 text-gray-500">{{ opt.days }} 天</td>
              <td class="py-2 px-2 text-gray-500">{{ opt.sort_order }}</td>
              <td class="py-2 px-2 text-right">
                <button class="text-blue-600 hover:text-blue-800 text-sm font-medium" @click="startEdit(opt)">编辑</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
