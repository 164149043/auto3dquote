<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { listMaterials, createMaterial, updateMaterial, deleteMaterial, uploadMaterialImage } = useAdminApi()

const materials = ref<Array<Record<string, unknown>>>([])
const loading = ref(false)
const error = ref('')
const editingId = ref<string | null>(null)
const editForm = ref<Record<string, unknown>>({})

const showAdd = ref(false)
const addForm = ref<Record<string, unknown>>({
  id: '', label: '', price: 0, unit: 'g', density: 1, process: 'fdm', machine_rate: null, sort_order: 0,
  category: 'other', description: '',
})

const CATEGORY_OPTIONS = [
  { value: 'resin', label: '树脂' },
  { value: 'nylon', label: '尼龙' },
  { value: 'engineering_resin', label: '工程树脂' },
  { value: 'metal', label: '金属' },
  { value: 'high_perf', label: '高性能材料' },
  { value: 'other', label: '其他' },
]

const PROCESS_OPTIONS = [
  { value: 'fdm', label: 'FDM' },
  { value: 'sla', label: 'SLA' },
  { value: 'sls', label: 'SLS' },
  { value: 'mjf', label: 'MJF' },
  { value: 'cnc', label: 'CNC' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    materials.value = await listMaterials()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function startEdit(m: Record<string, unknown>) {
  editingId.value = m.id as string
  editForm.value = { ...m }
}

function cancelEdit() {
  editingId.value = null
  editForm.value = {}
}

async function saveEdit() {
  try {
    await updateMaterial(editingId.value!, editForm.value)
    editingId.value = null
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  }
}

async function remove(id: string) {
  if (!confirm(`确认删除材料 ${id}？`)) return
  try {
    await deleteMaterial(id)
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '删除失败'
  }
}

async function addMaterial() {
  try {
    await createMaterial(addForm.value)
    showAdd.value = false
    addForm.value = { id: '', label: '', price: 0, unit: 'g', density: 1, process: 'fdm', machine_rate: null, sort_order: 0, category: 'other', description: '' }
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '创建失败'
  }
}

async function onImageUpload(event: Event, materialId: string) {
  const input = event.target as HTMLInputElement
  if (!input.files?.[0]) return
  try {
    await uploadMaterialImage(materialId, input.files[0])
    await load()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '图片上传失败'
  }
}

function getCategoryLabel(cat: string) {
  return CATEGORY_OPTIONS.find(c => c.value === cat)?.label || cat
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-800">材料管理</h3>
      <button
        class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg"
        @click="showAdd = !showAdd"
      >
        {{ showAdd ? '取消' : '+ 新增材料' }}
      </button>
    </div>

    <!-- 新增表单 -->
    <div v-if="showAdd" class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label class="block text-xs text-gray-600 mb-1">ID</label>
          <input v-model="addForm.id" class="w-full px-2 py-1.5 border rounded text-sm" placeholder="PLA" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">显示名</label>
          <input v-model="addForm.label" class="w-full px-2 py-1.5 border rounded text-sm" placeholder="PLA" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">单价</label>
          <input v-model.number="addForm.price" type="number" step="0.01" class="w-full px-2 py-1.5 border rounded text-sm" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">单位</label>
          <select v-model="addForm.unit" class="w-full px-2 py-1.5 border rounded text-sm">
            <option value="g">g (克)</option>
            <option value="cm3">cm³</option>
            <option value="kg">kg</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">密度 (g/cm³)</label>
          <input v-model.number="addForm.density" type="number" step="0.01" class="w-full px-2 py-1.5 border rounded text-sm" />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">工艺</label>
          <select v-model="addForm.process" class="w-full px-2 py-1.5 border rounded text-sm">
            <option v-for="p in PROCESS_OPTIONS" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">分类</label>
          <select v-model="addForm.category" class="w-full px-2 py-1.5 border rounded text-sm">
            <option v-for="c in CATEGORY_OPTIONS" :key="c.value" :value="c.value">{{ c.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">机床费率 (CNC)</label>
          <input v-model.number="addForm.machine_rate" type="number" step="0.01" class="w-full px-2 py-1.5 border rounded text-sm" />
        </div>
        <div class="col-span-2">
          <label class="block text-xs text-gray-600 mb-1">材料介绍</label>
          <textarea v-model="addForm.description" class="w-full px-2 py-1.5 border rounded text-sm" rows="2" placeholder="可选，填写材料特性描述"></textarea>
        </div>
        <div class="flex items-end">
          <button class="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg" @click="addMaterial">
            确认新增
          </button>
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
            <th class="py-2 px-2">工艺</th>
            <th class="py-2 px-2">分类</th>
            <th class="py-2 px-2">单价</th>
            <th class="py-2 px-2">图片</th>
            <th class="py-2 px-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in materials" :key="m.id as string" class="border-b border-gray-100 hover:bg-gray-50">
            <template v-if="editingId === m.id">
              <td class="py-2 px-2 font-mono text-xs">{{ m.id }}</td>
              <td class="py-2 px-2"><input v-model="editForm.label" class="w-full px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2 text-gray-500">{{ m.process }}</td>
              <td class="py-2 px-2">
                <select v-model="editForm.category" class="px-2 py-1 border rounded text-sm">
                  <option v-for="c in CATEGORY_OPTIONS" :key="c.value" :value="c.value">{{ c.label }}</option>
                </select>
              </td>
              <td class="py-2 px-2"><input v-model.number="editForm.price" type="number" step="0.01" class="w-20 px-2 py-1 border rounded text-sm" /></td>
              <td class="py-2 px-2">{{ m.image_url ? 'Yes' : '-' }}</td>
              <td class="py-2 px-2 text-right space-x-2">
                <button class="text-green-600 hover:text-green-800 text-sm font-medium" @click="saveEdit">保存</button>
                <button class="text-gray-500 hover:text-gray-700 text-sm" @click="cancelEdit">取消</button>
              </td>
            </template>
            <template v-else>
              <td class="py-2 px-2 font-mono text-xs text-gray-500">{{ m.id }}</td>
              <td class="py-2 px-2 font-medium">{{ m.label }}</td>
              <td class="py-2 px-2">
                <span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs uppercase">{{ m.process }}</span>
              </td>
              <td class="py-2 px-2">
                <span class="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">{{ getCategoryLabel((m.category as string) || 'other') }}</span>
              </td>
              <td class="py-2 px-2">{{ m.price }}/{{ m.unit }}</td>
              <td class="py-2 px-2">
                <div v-if="m.image_url" class="w-10 h-8 rounded bg-gray-100 overflow-hidden">
                  <img :src="m.image_url as string" class="w-full h-full object-cover" />
                </div>
                <label v-else class="cursor-pointer text-blue-500 hover:text-blue-700 text-xs">
                  上传
                  <input type="file" accept="image/*" class="hidden" @change="onImageUpload($event, m.id as string)" />
                </label>
              </td>
              <td class="py-2 px-2 text-right space-x-2">
                <button class="text-blue-600 hover:text-blue-800 text-sm font-medium" @click="startEdit(m)">编辑</button>
                <label class="text-purple-600 hover:text-purple-800 text-sm font-medium cursor-pointer">
                  图片
                  <input type="file" accept="image/*" class="hidden" @change="onImageUpload($event, m.id as string)" />
                </label>
                <button class="text-red-600 hover:text-red-800 text-sm font-medium" @click="remove(m.id as string)">删除</button>
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
