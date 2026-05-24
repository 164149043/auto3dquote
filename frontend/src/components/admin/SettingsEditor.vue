<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const { listSettings, updateSetting, refreshCache } = useAdminApi()

const loading = ref(false)
const saving = ref(false)
const message = ref('')
const error = ref('')

// 全局设置原始数据
const settingsMap = ref<Record<string, { value: unknown; description?: string }>>({})

// 标量设置编辑状态
const scalarEdits = reactive<Record<string, number>>({})
const scalarDirty = reactive<Record<string, boolean>>({})

// 最低起订价编辑
const minimumOrders = reactive<Record<string, number>>({})
const minimumOrdersDirty = ref(false)

// 折扣阶梯编辑
interface DiscountTier {
  min_qty: number
  discount: number
  label: string
}
const discountTiers = reactive<DiscountTier[]>([])
const discountTiersDirty = ref(false)

// 难度系数编辑
const difficulty = reactive({
  enabled: true,
  ratio_low: 0.3,
  ratio_high: 2.0,
  coefficient: 0.30,
  cnc_coefficient: 0.10,
})
const difficultyDirty = ref(false)

// 支撑成本编辑
const support = reactive({
  enabled: true,
  support_percent: 15.0,
  support_price_per_gram: 0.0,
})
const supportDirty = ref(false)

// 工艺名映射
const PROCESS_LABELS: Record<string, string> = {
  fdm: 'FDM 熔融沉积',
  sla: 'SLA 光固化',
  sls: 'SLS 激光烧结',
  mjf: 'MJF 多射流熔融',
  cnc: 'CNC 数控加工',
}

const SCALAR_SETTINGS: Record<string, { label: string; unit: string; step: number; min?: number }> = {
  time_cost_per_hour: { label: '机器时间费率', unit: '元/小时', step: 1, min: 0 },
  base_markup_rate: { label: '基础加价率', unit: '倍', step: 0.05, min: 1.0 },
  cnc_setup_fee: { label: 'CNC 装夹费', unit: '元', step: 5, min: 0 },
  cnc_minimum_order: { label: 'CNC 最低订单', unit: '元', step: 10, min: 0 },
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const list = await listSettings()
    const map: Record<string, { value: unknown; description?: string }> = {}
    for (const s of list) {
      map[s.key as string] = { value: s.value, description: s.description as string | undefined }
    }
    settingsMap.value = map

    // 初始化标量编辑
    for (const key of Object.keys(SCALAR_SETTINGS)) {
      if (map[key]) {
        scalarEdits[key] = map[key].value as number
        scalarDirty[key] = false
      }
    }

    // 初始化最低起订价
    if (map['minimum_order_per_process']) {
      const raw = map['minimum_order_per_process'].value as Record<string, number>
      for (const k of Object.keys(raw)) {
        minimumOrders[k] = raw[k]
      }
      minimumOrdersDirty.value = false
    }

    // 初始化折扣阶梯
    if (map['quantity_discount_tiers']) {
      const raw = map['quantity_discount_tiers'].value as DiscountTier[]
      discountTiers.splice(0, discountTiers.length, ...raw.map(t => ({ ...t })))
      discountTiersDirty.value = false
    }

    // 初始化难度系数
    if (map['difficulty_pricing']) {
      const raw = map['difficulty_pricing'].value as typeof difficulty
      difficulty.enabled = raw.enabled ?? true
      difficulty.ratio_low = raw.ratio_low ?? 0.3
      difficulty.ratio_high = raw.ratio_high ?? 2.0
      difficulty.coefficient = raw.coefficient ?? 0.30
      difficulty.cnc_coefficient = raw.cnc_coefficient ?? 0.10
      difficultyDirty.value = false
    }

    // 初始化支撑成本
    if (map['support_pricing']) {
      const raw = map['support_pricing'].value as typeof support
      support.enabled = raw.enabled ?? true
      support.support_percent = raw.support_percent ?? 15.0
      support.support_price_per_gram = raw.support_price_per_gram ?? 0.0
      supportDirty.value = false
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

// 标量设置修改追踪
function onScalarChange(key: string) {
  scalarDirty[key] = scalarEdits[key] !== (settingsMap.value[key]?.value as number)
}

async function saveScalar(key: string) {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    await updateSetting(key, scalarEdits[key], settingsMap.value[key]?.description)
    settingsMap.value[key] = { ...settingsMap.value[key]!, value: scalarEdits[key] }
    scalarDirty[key] = false
    message.value = `${SCALAR_SETTINGS[key].label} 已保存`
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

// 最低起订价
function onMinimumOrderChange() {
  const original = (settingsMap.value['minimum_order_per_process']?.value ?? {}) as Record<string, number>
  minimumOrdersDirty.value = Object.keys(minimumOrders).some(
    k => minimumOrders[k] !== original[k]
  )
}

async function saveMinimumOrders() {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    await updateSetting('minimum_order_per_process', { ...minimumOrders }, '各工艺最低起订金额 (¥)')
    settingsMap.value['minimum_order_per_process'] = { value: { ...minimumOrders }, description: '各工艺最低起订金额 (¥)' }
    minimumOrdersDirty.value = false
    message.value = '最低起订价已保存'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

// 折扣阶梯
function onTierChange() {
  const original = (settingsMap.value['quantity_discount_tiers']?.value ?? []) as DiscountTier[]
  discountTiersDirty.value = JSON.stringify(discountTiers) !== JSON.stringify(original)
}

function addTier() {
  discountTiers.push({ min_qty: 100, discount: 0.15, label: '100+件 (-15%)' })
  onTierChange()
}

function removeTier(index: number) {
  discountTiers.splice(index, 1)
  onTierChange()
}

function updateTierLabel(index: number) {
  const tier = discountTiers[index]
  const pct = (tier.discount * 100).toFixed(0)
  tier.label = `${tier.min_qty}+件 (-${pct}%)`
  onTierChange()
}

async function saveDiscountTiers() {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const sorted = [...discountTiers].sort((a, b) => a.min_qty - b.min_qty)
    discountTiers.splice(0, discountTiers.length, ...sorted)
    await updateSetting('quantity_discount_tiers', sorted, '数量折扣阶梯配置')
    settingsMap.value['quantity_discount_tiers'] = { value: sorted, description: '数量折扣阶梯配置' }
    discountTiersDirty.value = false
    message.value = '折扣阶梯已保存'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

// 难度系数
function onDifficultyChange() {
  const original = (settingsMap.value['difficulty_pricing']?.value ?? {
    enabled: true, ratio_low: 0.3, ratio_high: 2.0, coefficient: 0.30, cnc_coefficient: 0.10,
  }) as typeof difficulty
  difficultyDirty.value = (
    difficulty.enabled !== original.enabled
    || difficulty.ratio_low !== original.ratio_low
    || difficulty.ratio_high !== original.ratio_high
    || difficulty.coefficient !== original.coefficient
    || difficulty.cnc_coefficient !== original.cnc_coefficient
  )
}

async function saveDifficulty() {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const payload = { ...difficulty }
    await updateSetting('difficulty_pricing', payload, '难度系数定价配置 (SA/V比 → 加价系数)')
    settingsMap.value['difficulty_pricing'] = { value: payload, description: '难度系数定价配置 (SA/V比 → 加价系数)' }
    difficultyDirty.value = false
    message.value = '难度系数已保存'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

// 支撑成本
function onSupportChange() {
  const original = (settingsMap.value['support_pricing']?.value ?? {
    enabled: true, support_percent: 15.0, support_price_per_gram: 0.0,
  }) as typeof support
  supportDirty.value = (
    support.enabled !== original.enabled
    || support.support_percent !== original.support_percent
    || support.support_price_per_gram !== original.support_price_per_gram
  )
}

async function saveSupport() {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    const payload = { ...support }
    await updateSetting('support_pricing', payload, '支撑成本配置 (估算比例 × 单价)')
    settingsMap.value['support_pricing'] = { value: payload, description: '支撑成本配置 (估算比例 × 单价)' }
    supportDirty.value = false
    message.value = '支撑成本配置已保存'
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function onRefreshCache() {
  try {
    await refreshCache()
    message.value = '缓存已刷新'
    error.value = ''
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '刷新失败'
  }
}

// 检查是否有折扣预览
function getDiscountPreview(qty: number): string {
  let rate = 0
  for (const tier of discountTiers) {
    if (qty >= tier.min_qty) rate = tier.discount
  }
  return rate > 0 ? `-${(rate * 100).toFixed(0)}%` : '无折扣'
}

onMounted(load)
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold text-gray-800">全局设置</h3>
      <button
        class="px-3 py-1.5 bg-orange-500 hover:bg-orange-600 text-white text-sm rounded-lg transition"
        @click="onRefreshCache"
      >
        刷新缓存
      </button>
    </div>

    <!-- Messages -->
    <div v-if="message" class="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex justify-between items-center">
      {{ message }}
      <button class="text-green-500 hover:text-green-700" @click="message = ''">✕</button>
    </div>
    <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex justify-between items-center">
      {{ error }}
      <button class="text-red-500 hover:text-red-700" @click="error = ''">✕</button>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-400">加载中...</div>

    <template v-else>
      <!-- ====== 基础费率 ====== -->
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div class="bg-gray-50 px-4 py-2.5 border-b border-gray-200">
          <h4 class="text-sm font-semibold text-gray-700">基础费率</h4>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="(cfg, key) in SCALAR_SETTINGS"
            :key="key"
            class="flex items-center justify-between px-4 py-3"
          >
            <div class="flex-1">
              <span class="text-sm font-medium text-gray-700">{{ cfg.label }}</span>
              <span class="ml-2 text-xs text-gray-400">{{ cfg.unit }}</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="relative">
                <input
                  type="number"
                  v-model.number="scalarEdits[key]"
                  :step="cfg.step"
                  :min="cfg.min"
                  class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  :class="scalarDirty[key] ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
                  @input="onScalarChange(key)"
                />
              </div>
              <button
                v-if="scalarDirty[key]"
                :disabled="saving"
                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition disabled:opacity-50"
                @click="saveScalar(key)"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 最低起订价 ====== -->
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div class="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-gray-700">各工艺最低起订价</h4>
            <p class="text-xs text-gray-400 mt-0.5">低于此金额的订单将按最低价收取</p>
          </div>
          <button
            v-if="minimumOrdersDirty"
            :disabled="saving"
            class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition disabled:opacity-50"
            @click="saveMinimumOrders"
          >
            保存
          </button>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="(label, process) in PROCESS_LABELS"
            :key="process"
            class="flex items-center justify-between px-4 py-3"
          >
            <div>
              <span class="text-sm font-medium text-gray-700">{{ label }}</span>
              <span class="ml-2 text-xs text-gray-400 font-mono">{{ process }}</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="text-xs text-gray-400">¥</span>
              <input
                type="number"
                v-model.number="minimumOrders[process]"
                step="5"
                min="0"
                class="w-24 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                :class="minimumOrdersDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
                @input="onMinimumOrderChange"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 数量折扣阶梯 ====== -->
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div class="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-gray-700">数量折扣阶梯</h4>
            <p class="text-xs text-gray-400 mt-0.5">根据订购数量自动应用折扣率</p>
          </div>
          <div class="flex gap-2">
            <button
              class="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs rounded-lg transition"
              @click="addTier"
            >
              + 添加阶梯
            </button>
            <button
              v-if="discountTiersDirty"
              :disabled="saving"
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition disabled:opacity-50"
              @click="saveDiscountTiers"
            >
              保存
            </button>
          </div>
        </div>

        <!-- Table header -->
        <div class="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 px-4 py-2 bg-gray-50/50 border-b border-gray-100 text-xs font-medium text-gray-500 uppercase tracking-wider">
          <span>最低数量</span>
          <span>折扣率</span>
          <span>显示标签</span>
          <span class="w-8"></span>
        </div>

        <!-- Tier rows -->
        <div
          v-for="(tier, idx) in discountTiers"
          :key="idx"
          class="grid grid-cols-[1fr_1fr_1fr_auto] gap-2 px-4 py-2.5 border-b border-gray-50 items-center"
        >
          <div>
            <input
              type="number"
              v-model.number="tier.min_qty"
              min="1"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              @input="onTierChange()"
            />
          </div>
          <div class="flex items-center gap-1">
            <input
              type="number"
              :value="tier.discount"
              @input="($event: Event) => { tier.discount = parseFloat(($event.target as HTMLInputElement).value) || 0; updateTierLabel(idx) }"
              step="0.01"
              min="0"
              max="1"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <span class="text-xs text-gray-400 whitespace-nowrap">
              {{ (tier.discount * 100).toFixed(0) }}%
            </span>
          </div>
          <div>
            <input
              type="text"
              v-model="tier.label"
              class="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              @input="onTierChange()"
            />
          </div>
          <button
            class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
            title="删除阶梯"
            @click="removeTier(idx)"
          >
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
          </button>
        </div>

        <!-- Discount preview -->
        <div class="px-4 py-3 bg-gray-50/30">
          <p class="text-xs text-gray-500 mb-2 font-medium">折扣预览</p>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="qty in [1, 5, 10, 20, 50, 100]"
              :key="qty"
              class="px-2.5 py-1 rounded-md text-xs font-mono"
              :class="getDiscountPreview(qty) !== '无折扣' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-gray-100 text-gray-500 border border-gray-200'"
            >
              {{ qty }}件: {{ getDiscountPreview(qty) }}
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 难度系数定价 ====== -->
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div class="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-gray-700">难度系数定价</h4>
            <p class="text-xs text-gray-400 mt-0.5">基于表面积/体积(SA/V)比自动加价，薄壁精细件难度更高</p>
          </div>
          <div class="flex items-center gap-3">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="difficulty.enabled"
                class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                @change="onDifficultyChange()"
              />
              <span class="text-xs text-gray-600">启用</span>
            </label>
            <button
              v-if="difficultyDirty"
              :disabled="saving"
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition disabled:opacity-50"
              @click="saveDifficulty"
            >
              保存
            </button>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">SA/V 低阈值</span>
              <span class="ml-2 text-xs text-gray-400">低于此值不加价</span>
            </div>
            <input
              type="number"
              v-model.number="difficulty.ratio_low"
              step="0.05"
              min="0"
              class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              :class="difficultyDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
              @input="onDifficultyChange()"
            />
          </div>
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">SA/V 高阈值</span>
              <span class="ml-2 text-xs text-gray-400">高于此值按最高加价</span>
            </div>
            <input
              type="number"
              v-model.number="difficulty.ratio_high"
              step="0.1"
              min="0"
              class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              :class="difficultyDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
              @input="onDifficultyChange()"
            />
          </div>
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">最大加价系数 (3D打印)</span>
              <span class="ml-2 text-xs text-gray-400">FDM/SLA/SLS/MJF，如 0.3 = 最高 30%</span>
            </div>
            <input
              type="number"
              v-model.number="difficulty.coefficient"
              step="0.05"
              min="0"
              max="1"
              class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              :class="difficultyDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
              @input="onDifficultyChange()"
            />
          </div>
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">CNC 专用系数</span>
              <span class="ml-2 text-xs text-gray-400">SA/V 对 CNC 相关性弱，建议更低</span>
            </div>
            <input
              type="number"
              v-model.number="difficulty.cnc_coefficient"
              step="0.05"
              min="0"
              max="1"
              class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              :class="difficultyDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
              @input="onDifficultyChange()"
            />
          </div>
        </div>
        <!-- Difficulty effect preview -->
        <div class="px-4 py-3 bg-gray-50/30">
          <p class="text-xs text-gray-500 mb-2 font-medium">效果预览</p>
          <div class="flex flex-wrap gap-2">
            <div class="px-2.5 py-1 rounded-md text-xs font-mono bg-gray-100 text-gray-500 border border-gray-200">
              实心方块: ×1.00 (不加价)
            </div>
            <div class="px-2.5 py-1 rounded-md text-xs font-mono bg-amber-50 text-amber-700 border border-amber-200">
              中等复杂: ×{{ (1 + difficulty.coefficient * 0.5).toFixed(2) }} ({{ (difficulty.coefficient * 0.5 * 100).toFixed(0) }}%)
            </div>
            <div class="px-2.5 py-1 rounded-md text-xs font-mono bg-red-50 text-red-700 border border-red-200">
              高难度: ×{{ (1 + difficulty.coefficient).toFixed(2) }} ({{ (difficulty.coefficient * 100).toFixed(0) }}%)
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 支撑成本 ====== -->
      <div class="border border-gray-200 rounded-xl overflow-hidden">
        <div class="bg-gray-50 px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h4 class="text-sm font-semibold text-gray-700">支撑成本 (FDM)</h4>
            <p class="text-xs text-gray-400 mt-0.5">基于几何特征估算支撑材料重量，独立计费</p>
          </div>
          <div class="flex items-center gap-3">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="support.enabled"
                class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                @change="onSupportChange()"
              />
              <span class="text-xs text-gray-600">启用</span>
            </label>
            <button
              v-if="supportDirty"
              :disabled="saving"
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition disabled:opacity-50"
              @click="saveSupport"
            >
              保存
            </button>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">支撑比例</span>
              <span class="ml-2 text-xs text-gray-400">占模型重量的 %</span>
            </div>
            <div class="flex items-center gap-1">
              <input
                type="number"
                v-model.number="support.support_percent"
                step="1"
                min="0"
                max="100"
                class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                :class="supportDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
                @input="onSupportChange()"
              />
              <span class="text-xs text-gray-400">%</span>
            </div>
          </div>
          <div class="flex items-center justify-between px-4 py-3">
            <div>
              <span class="text-sm font-medium text-gray-700">支撑单价</span>
              <span class="ml-2 text-xs text-gray-400">¥/g，留 0 则与主材同价</span>
            </div>
            <div class="flex items-center gap-1">
              <span class="text-xs text-gray-400">¥</span>
              <input
                type="number"
                v-model.number="support.support_price_per_gram"
                step="0.01"
                min="0"
                class="w-28 px-3 py-1.5 border rounded-lg text-sm text-right font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                :class="supportDirty ? 'border-blue-400 bg-blue-50/50' : 'border-gray-300'"
                @input="onSupportChange()"
              />
            </div>
          </div>
        </div>
        <div class="px-4 py-3 bg-gray-50/30">
          <p class="text-xs text-gray-500 mb-2 font-medium">示例 (100g PLA 模型, 高度 100mm)</p>
          <div class="flex flex-wrap gap-2">
            <div class="px-2.5 py-1 rounded-md text-xs font-mono bg-amber-50 text-amber-700 border border-amber-200">
              支撑约 {{ (100 * support.support_percent / 100).toFixed(0) }}g → {{ support.support_price_per_gram > 0
                ? '¥' + (100 * support.support_percent / 100 * support.support_price_per_gram).toFixed(2)
                : '与主材同价'
              }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
