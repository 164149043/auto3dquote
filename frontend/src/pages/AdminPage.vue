<script setup lang="ts">
import { ref } from 'vue'
import { useAdminApi } from '../composables/useAdminApi'
import { useAuth } from '../composables/useAuth'
import AdminLogin from '../components/admin/AdminLogin.vue'
import MaterialEditor from '../components/admin/MaterialEditor.vue'
import PostProcessEditor from '../components/admin/PostProcessEditor.vue'
import DeliveryEditor from '../components/admin/DeliveryEditor.vue'
import ProcessMappingEditor from '../components/admin/ProcessMappingEditor.vue'
import MachineLimitsEditor from '../components/admin/MachineLimitsEditor.vue'
import SettingsEditor from '../components/admin/SettingsEditor.vue'

const { getToken, clearToken, setToken } = useAdminApi()
const { isAdmin, isAuthenticated, token: userToken } = useAuth()

// 如果管理员已通过主页面登录但没有 admin_token，同步 JWT 到 admin_token
if (!getToken() && isAuthenticated.value && isAdmin.value && userToken.value) {
  setToken(userToken.value)
}

const authenticated = ref(!!getToken() && (!isAuthenticated.value || isAdmin.value))
const activeTab = ref('materials')

const TABS = [
  { id: 'materials', label: '材料' },
  { id: 'post-processes', label: '后处理' },
  { id: 'delivery', label: '交期' },
  { id: 'mapping', label: '映射' },
  { id: 'machine', label: '设备' },
  { id: 'settings', label: '设置' },
]

function onAuthenticated() {
  authenticated.value = true
}

function onLogout() {
  clearToken()
  authenticated.value = false
}
</script>

<template>
  <main class="max-w-6xl mx-auto px-6 py-8">
    <!-- 未认证 → 显示登录 -->
    <AdminLogin v-if="!authenticated" @authenticated="onAuthenticated" />

    <!-- 已认证 → 显示管理面板 -->
    <template v-else>
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-800">管理后台</h2>
        <button
          class="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm rounded-lg"
          @click="onLogout"
        >
          退出管理
        </button>
      </div>

      <!-- Tab 导航 -->
      <div class="flex gap-1 mb-6 border-b border-gray-200">
        <button
          v-for="tab in TABS"
          :key="tab.id"
          :class="[
            'px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px',
            activeTab === tab.id
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          ]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 内容 -->
      <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
        <MaterialEditor v-if="activeTab === 'materials'" />
        <PostProcessEditor v-else-if="activeTab === 'post-processes'" />
        <DeliveryEditor v-else-if="activeTab === 'delivery'" />
        <ProcessMappingEditor v-else-if="activeTab === 'mapping'" />
        <MachineLimitsEditor v-else-if="activeTab === 'machine'" />
        <SettingsEditor v-else-if="activeTab === 'settings'" />
      </div>
    </template>
  </main>
</template>
