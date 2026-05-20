<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { listPostProcesses, createPostProcess, updatePostProcess, deletePostProcess } = useAdminApi()

const postProcesses = ref<Array<Record<string, unknown>>>([])
const loading = ref(false)
const error = ref('')
const editingId = ref<string | null>(null)
const editForm = ref<Record<string, unknown>>({})

const showAdd = ref(false)
const addForm = ref({ id: '', label: '', mode: 'fixed', value: 0, description: '' })

async function load() {
  loading.value = true
  error.value = ''
  try {
    postProcesses.value = await listPostProcesses()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function startEdit(pp: Record<string, unknown>) {
  editingId.value = pp.id as string
  editForm.value = { ...pp }
}

function cancelEdit() {
  editingId.value = null
  editForm.value = {}
}

async function saveEdit() {
  try {
    await updatePostProcess(editingId.value!, editForm.value)
    editingId.value = null
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  }
}

async function remove(id: string) {
  if (!confirm(`确认删除后处理 ${id}？`)) return
  try {
    await deletePostProcess(id)
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function add() {
  try {
    await createPostProcess(addForm.value)
    showAdd.value = false
    addForm.value = { id: '', label: '', mode: 'fixed', value: 0, description: '' }
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '创建失败'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-800">后处理管理</h3>
      <button
        class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg"
        @click="showAdd = !showAdd"
      >
        {{ showAdd ? '取消' : '+ 新增' }}
      </button>
    </div>

    <div v-if="showAdd" class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <label class="block text-xs text-gray-600 mb-1">ID</label>
          <input v-model="addForm.id" class="w-full px-2 py-1.5 border rounded text-sm" placeholder="sanding" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">显示名</label>
          <input v-model="addForm.label" class="w-full px-2 py-1.5 border rounded text-sm" placeholder="打磨" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">计费模式</label>
          <select v-model="addForm.mode" class="w-full px-2 py-1.5 border rounded text-sm">
            <option value="fixed">固定金额</option>
            <option value="percentage">百分比</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">值 {{ addForm.mode === 'percentage' ? '(如 0.15 = 15%)' : '(元)' }}</label>
          <input v-model.number="addForm.value" type="number" step="0.01" class="w-full px-2 py-1.5 border rounded text-sm" />
        </div>
        <div class="flex items-end">
          <button class="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg" @click="add">确认</button>
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-gray-600 mb-1">说明介绍</label>
          <textarea v-model="addForm.description" class="w-full px-2 py-1.5 border rounded text-sm" rows="2" placeholder="可选，填写处理方式说明"></textarea>
        </div>
      </div>
    </div>

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
            <th class="py-2 px-2">计费模式</th>
            <th class="py-2 px-2">值</th>
            <th class="py-2 px-2">说明</th>
            <th class="py-2 px-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pp in postProcesses" :key="pp.id as string" class="border-b border-gray-100 hover:bg-gray-50">
            <template v-if="editingId === pp.id">
              <td class="py-2 px-2 font-mono text-xs">{{ pp.id }}</td>
              <td class="py-2 px-2"><input v-model="editForm.label" class="w-full px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2">
                <select v-model="editForm.mode" class="px-2 py-1 border rounded text-sm">
                  <option value="fixed">固定金额</option>
                  <option value="percentage">百分比</option>
                </select>
              </td>
              <td class="py-2 px-2">
                <div class="flex items-center gap-1">
                  <input v-model.number="editForm.value" type="number" step="0.01" class="w-24 px-2 py-1 border rounded text-sm" />
                  <span class="text-xs text-gray-400">{{ editForm.mode === 'percentage' ? '(如 0.15 = 15%)' : '元' }}</span>
                </div>
              </td>
              <td class="py-2 px-2"><input v-model="editForm.description" class="w-full px-2 py-1 border rounded text-sm" placeholder="说明" /></td>
              <td class="py-2 px-2 text-right space-x-2">
                <button class="text-green-600 hover:text-green-800 text-sm font-medium" @click="saveEdit">保存</button>
                <button class="text-gray-500 hover:text-gray-700 text-sm" @click="cancelEdit">取消</button>
              </td>
            </template>
            <template v-else>
              <td class="py-2 px-2 font-mono text-xs text-gray-500">{{ pp.id }}</td>
              <td class="py-2 px-2 font-medium">{{ pp.label }}</td>
              <td class="py-2 px-2">
                <span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                  {{ pp.mode === 'fixed' ? '固定金额' : '百分比' }}
                </span>
              </td>
              <td class="py-2 px-2">{{ pp.mode === 'percentage' ? `${(pp.value as number * 100).toFixed(0)}%` : `¥${pp.value}` }}</td>
              <td class="py-2 px-2 text-gray-500 text-xs max-w-32 truncate">{{ (pp.description as string) || '-' }}</td>
              <td class="py-2 px-2 text-right space-x-2">
                <button class="text-blue-600 hover:text-blue-800 text-sm font-medium" @click="startEdit(pp)">编辑</button>
                <button class="text-red-600 hover:text-red-800 text-sm font-medium" @click="remove(pp.id as string)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
