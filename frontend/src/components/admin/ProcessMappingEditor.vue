<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { getProcessMapping, updateProcessMaterials, updateProcessPostProcesses, listMaterials, listPostProcesses } = useAdminApi()

const processMapping = ref<Record<string, unknown>>({})
const allMaterials = ref<Array<Record<string, unknown>>>([])
const allPostProcesses = ref<Array<Record<string, unknown>>>([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')

const PROCESSES = [
  { id: 'fdm', label: 'FDM' },
  { id: 'sla', label: 'SLA' },
  { id: 'sls', label: 'SLS' },
  { id: 'mjf', label: 'MJF' },
  { id: 'cnc', label: 'CNC' },
]

const selectedProcess = ref('fdm')

const processMaterials = computed<Record<string, string[]>>(() =>
  (processMapping.value.process_materials as Record<string, string[]>) || {}
)
const processPostProcesses = computed<Record<string, string[]>>(() =>
  (processMapping.value.process_post_processes as Record<string, string[]>) || {}
)

const currentMaterialIds = computed<string[]>(() => processMaterials.value[selectedProcess.value] || [])
const currentPostProcessIds = computed<string[]>(() => processPostProcesses.value[selectedProcess.value] || [])

// 可用的材料和后处理（用于勾选）
const materialsByProcess = computed(() => {
  const proc = selectedProcess.value
  return allMaterials.value.filter(m => m.process === proc)
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [mapping, mats, pps] = await Promise.all([
      getProcessMapping(),
      listMaterials(),
      listPostProcesses(),
    ])
    processMapping.value = mapping
    allMaterials.value = mats
    allPostProcesses.value = pps
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function toggleMaterial(matId: string) {
  const ids = [...currentMaterialIds.value]
  const idx = ids.indexOf(matId)
  if (idx >= 0) ids.splice(idx, 1)
  else ids.push(matId)
  // 直接更新本地映射
  const pm = { ...processMaterials.value, [selectedProcess.value]: ids }
  processMapping.value = { ...processMapping.value, process_materials: pm }
}

function togglePostProcess(ppId: string) {
  const ids = [...currentPostProcessIds.value]
  const idx = ids.indexOf(ppId)
  if (idx >= 0) ids.splice(idx, 1)
  else ids.push(ppId)
  const pp = { ...processPostProcesses.value, [selectedProcess.value]: ids }
  processMapping.value = { ...processMapping.value, process_post_processes: pp }
}

async function saveMaterials() {
  saving.value = true
  try {
    await updateProcessMaterials(selectedProcess.value, currentMaterialIds.value)
    error.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function savePostProcesses() {
  saving.value = true
  try {
    await updateProcessPostProcesses(selectedProcess.value, currentPostProcessIds.value)
    error.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h3 class="text-lg font-semibold text-gray-800 mb-4">工艺映射</h3>

    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
      {{ error }}
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">加载中...</div>

    <template v-else>
      <!-- 工艺选择 -->
      <div class="flex gap-2 mb-6">
        <button
          v-for="p in PROCESSES"
          :key="p.id"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition',
            selectedProcess === p.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
          @click="selectedProcess = p.id"
        >
          {{ p.label }}
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 材料 -->
        <div class="p-4 border border-gray-200 rounded-xl">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-700">关联材料</h4>
            <button
              :disabled="saving"
              class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg disabled:bg-gray-400"
              @click="saveMaterials"
            >
              保存
            </button>
          </div>
          <div class="space-y-2">
            <label
              v-for="m in materialsByProcess"
              :key="m.id as string"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="checkbox"
                :checked="currentMaterialIds.includes(m.id as string)"
                @change="toggleMaterial(m.id as string)"
              />
              <span>{{ m.label }}</span>
              <span class="text-gray-400 text-xs">({{ m.id }})</span>
            </label>
            <p v-if="materialsByProcess.length === 0" class="text-sm text-gray-400">该工艺暂无材料</p>
          </div>
        </div>

        <!-- 后处理 -->
        <div class="p-4 border border-gray-200 rounded-xl">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-medium text-gray-700">关联后处理</h4>
            <button
              :disabled="saving"
              class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg disabled:bg-gray-400"
              @click="savePostProcesses"
            >
              保存
            </button>
          </div>
          <div class="space-y-2">
            <label
              v-for="pp in allPostProcesses"
              :key="pp.id as string"
              class="flex items-center gap-2 text-sm"
            >
              <input
                type="checkbox"
                :checked="currentPostProcessIds.includes(pp.id as string)"
                @change="togglePostProcess(pp.id as string)"
              />
              <span>{{ pp.label }}</span>
              <span class="text-gray-400 text-xs">({{ pp.id }})</span>
            </label>
            <p v-if="allPostProcesses.length === 0" class="text-sm text-gray-400">暂无后处理选项</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
