<script setup lang="ts">
import { ref } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'
import { useAuth } from '../../composables/useAuth'

const emit = defineEmits<{ (e: 'authenticated'): void }>()

const { setToken, getToken, listMaterials } = useAdminApi()
const { login: userLogin } = useAuth()

const mode = ref<'token' | 'account'>('account')
const token = ref(getToken())
const username = ref('')
const password = ref('')
const error = ref('')
const verifying = ref(false)

async function onLogin() {
  error.value = ''
  verifying.value = true

  try {
    if (mode.value === 'token') {
      // 静态 Token 登录
      if (!token.value.trim()) {
        error.value = '请输入 Token'
        return
      }
      setToken(token.value.trim())
      await listMaterials()
    } else {
      // 管理员账号登录
      if (!username.value.trim() || !password.value) {
        error.value = '请输入用户名和密码'
        return
      }
      const data = await userLogin(username.value.trim(), password.value)
      // 检查是否是管理员
      if (data.user.role !== 'admin') {
        error.value = '该账号没有管理员权限'
        return
      }
      // 将 JWT 也存为 admin_token 以便管理 API 使用
      setToken(data.access_token)
      await listMaterials()
    }
    emit('authenticated')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '验证失败'
  } finally {
    verifying.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto mt-20 p-8 bg-white rounded-2xl border border-gray-200 shadow-sm">
    <h2 class="text-xl font-bold text-gray-800 mb-2">管理后台登录</h2>
    <p class="text-sm text-gray-500 mb-6">管理员账号或 Token 验证</p>

    <!-- 模式切换 -->
    <div class="flex mb-6 bg-gray-100 rounded-lg p-1">
      <button
        class="flex-1 py-2 text-sm font-medium rounded-md transition-all"
        :class="mode === 'account' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="mode = 'account'"
      >
        账号登录
      </button>
      <button
        class="flex-1 py-2 text-sm font-medium rounded-md transition-all"
        :class="mode === 'token' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="mode = 'token'"
      >
        Token 登录
      </button>
    </div>

    <div class="space-y-4">
      <!-- 账号登录 -->
      <template v-if="mode === 'account'">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="管理员账号"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            @keydown.enter="onLogin"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="管理员密码"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            @keydown.enter="onLogin"
          />
        </div>
      </template>

      <!-- Token 登录 -->
      <template v-else>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Admin Token</label>
          <input
            v-model="token"
            type="password"
            placeholder="输入 Token..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            @keydown.enter="onLogin"
          />
        </div>
      </template>

      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        {{ error }}
      </div>

      <button
        :disabled="verifying || (mode === 'token' ? !token.trim() : !username.trim() || !password)"
        class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition"
        @click="onLogin"
      >
        {{ verifying ? '验证中...' : '登录' }}
      </button>
    </div>
  </div>
</template>
