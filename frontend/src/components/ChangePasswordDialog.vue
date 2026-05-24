<script setup lang="ts">
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const emit = defineEmits<{ close: [] }>()

const { changePassword } = useAuth()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

async function handleSubmit(e: Event) {
  e.preventDefault()
  error.value = ''
  success.value = false

  if (!oldPassword.value) {
    error.value = '请输入旧密码'
    return
  }
  if (!newPassword.value || newPassword.value.length < 6) {
    error.value = '新密码至少 6 个字符'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的新密码不一致'
    return
  }

  loading.value = true
  try {
    await changePassword({
      old_password: oldPassword.value,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value,
    })
    success.value = true
    setTimeout(() => emit('close'), 1500)
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '修改密码失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center" @click.self="emit('close')">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

    <!-- Dialog -->
    <div class="relative glass-panel rounded-2xl p-6 w-full max-w-sm mx-4 animate-fade-in-up">
      <div class="flex items-center justify-between mb-5">
        <h3 class="text-lg font-bold text-white">修改密码</h3>
        <button @click="emit('close')" class="text-ghost hover:text-white transition-colors">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <form @submit="handleSubmit" class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-silver">旧密码</label>
          <input v-model="oldPassword" type="password" placeholder="请输入旧密码" class="input-dark w-full h-11 px-4 text-sm" />
        </div>

        <div class="space-y-1.5">
          <label class="text-sm font-medium text-silver">新密码</label>
          <input v-model="newPassword" type="password" placeholder="至少 6 个字符" class="input-dark w-full h-11 px-4 text-sm" />
        </div>

        <div class="space-y-1.5">
          <label class="text-sm font-medium text-silver">确认新密码</label>
          <input v-model="confirmPassword" type="password" placeholder="请再次输入新密码" class="input-dark w-full h-11 px-4 text-sm" />
        </div>

        <div v-if="error" class="p-3 text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg">
          {{ error }}
        </div>

        <div v-if="success" class="p-3 text-sm text-teal bg-teal/10 border border-teal/20 rounded-lg">
          密码修改成功
        </div>

        <button type="submit" class="btn-primary w-full h-11 text-sm font-medium" :disabled="loading">
          {{ loading ? '提交中...' : '确认修改' }}
        </button>
      </form>
    </div>
  </div>
</template>
