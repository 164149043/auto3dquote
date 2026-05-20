<script setup lang="ts">
import { ref } from 'vue'
import { useAdminApi } from '../../composables/useAdminApi'

const emit = defineEmits<{ (e: 'authenticated'): void }>()

const { setToken, getToken, listMaterials } = useAdminApi()

const token = ref(getToken())
const error = ref('')
const verifying = ref(false)

async function onLogin() {
  if (!token.value.trim()) return
  error.value = ''
  verifying.value = true
  try {
    setToken(token.value.trim())
    await listMaterials() // 验证 token 是否有效
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
    <p class="text-sm text-gray-500 mb-6">请输入 Admin Token 以访问管理功能</p>

    <div class="space-y-4">
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

      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        {{ error }}
      </div>

      <button
        :disabled="verifying || !token.trim()"
        class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition"
        @click="onLogin"
      >
        {{ verifying ? '验证中...' : '登录' }}
      </button>
    </div>
  </div>
</template>
