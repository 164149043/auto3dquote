<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  loading: boolean
  error: string
  fetchCaptcha: () => Promise<{ captcha_id: string; captcha_image: string }>
}>()

const emit = defineEmits<{
  submit: [mode: 'login' | 'register', username: string, password: string, captchaId: string, captchaCode: string]
  'typing-change': [isTyping: boolean]
  'password-visibility-change': [visible: boolean]
  'has-password-change': [has: boolean]
  'clear-error': []
}>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const localError = ref('')

// 验证码
const captchaId = ref('')
const captchaImage = ref('')
const captchaCode = ref('')
const captchaLoading = ref(false)

watch(() => props.error, (val) => {
  localError.value = val
  // 注册失败后自动刷新验证码（旧验证码已被后端消耗）
  if (val && mode.value === 'register') {
    refreshCaptcha()
  }
})

watch(showPassword, (val) => {
  emit('password-visibility-change', val)
})

watch(() => password.value.length > 0, (val) => {
  emit('has-password-change', val)
})

function onInputFocus() {
  emit('typing-change', true)
}

function onInputBlur() {
  emit('typing-change', false)
}

function switchMode(newMode: 'login' | 'register') {
  mode.value = newMode
  localError.value = ''
  captchaCode.value = ''
  emit('clear-error')
  if (newMode === 'register') {
    refreshCaptcha()
  }
}

async function refreshCaptcha() {
  captchaLoading.value = true
  try {
    const data = await props.fetchCaptcha()
    captchaId.value = data.captcha_id
    captchaImage.value = data.captcha_image
    captchaCode.value = ''
  } catch {
    localError.value = '获取验证码失败'
  } finally {
    captchaLoading.value = false
  }
}

function handleSubmit(e: Event) {
  e.preventDefault()
  localError.value = ''

  if (!username.value.trim()) {
    localError.value = '请输入用户名'
    return
  }
  if (!password.value) {
    localError.value = '请输入密码'
    return
  }
  if (password.value.length < 6) {
    localError.value = '密码至少 6 个字符'
    return
  }
  if (mode.value === 'register') {
    if (!confirmPassword.value) {
      localError.value = '请确认密码'
      return
    }
    if (password.value !== confirmPassword.value) {
      localError.value = '两次输入的密码不一致'
      return
    }
    if (!captchaCode.value.trim()) {
      localError.value = '请输入验证码'
      return
    }
  }

  emit('submit', mode.value, username.value.trim(), password.value, captchaId.value, captchaCode.value.trim())
}
</script>

<template>
  <div class="w-full max-w-[380px] mx-auto">
    <!-- 移动端 Logo -->
    <div class="lg:hidden flex items-center justify-center gap-2 mb-10">
      <div class="w-8 h-8 rounded-lg bg-teal/10 flex items-center justify-center">
        <svg class="w-4 h-4 text-teal" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z"/>
        </svg>
      </div>
      <span class="font-display font-bold text-white text-sm">Auto3DQuote</span>
    </div>

    <!-- 标题 -->
    <div class="text-center mb-8">
      <h1 class="text-2xl font-bold text-white tracking-tight mb-2">
        {{ mode === 'login' ? '欢迎回来' : '创建账号' }}
      </h1>
      <p class="text-ghost text-sm">
        {{ mode === 'login' ? '请输入您的登录信息' : '填写信息注册新账号' }}
      </p>
    </div>

    <!-- Tab 切换 -->
    <div class="flex mb-6 bg-deep rounded-lg p-1">
      <button
        class="flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200"
        :class="mode === 'login' ? 'bg-panel text-teal shadow-sm' : 'text-ghost hover:text-silver'"
        @click="switchMode('login')"
      >
        登录
      </button>
      <button
        class="flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200"
        :class="mode === 'register' ? 'bg-panel text-teal shadow-sm' : 'text-ghost hover:text-silver'"
        @click="switchMode('register')"
      >
        注册
      </button>
    </div>

    <!-- 表单 -->
    <form @submit="handleSubmit" class="space-y-4">
      <!-- 用户名 -->
      <div class="space-y-1.5">
        <label class="text-sm font-medium text-silver">用户名</label>
        <input
          v-model="username"
          type="text"
          placeholder="请输入用户名"
          autocomplete="off"
          class="input-dark w-full h-11 px-4 text-sm"
          @focus="onInputFocus"
          @blur="onInputBlur"
        />
      </div>

      <!-- 密码 -->
      <div class="space-y-1.5">
        <label class="text-sm font-medium text-silver">密码</label>
        <div class="relative">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            class="input-dark w-full h-11 px-4 pr-10 text-sm"
            @focus="onInputFocus"
            @blur="onInputBlur"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-ghost hover:text-silver transition-colors"
            @click="showPassword = !showPassword"
          >
            <svg v-if="!showPassword" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
              <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 确认密码（注册模式） -->
      <div v-if="mode === 'register'" class="space-y-1.5">
        <label class="text-sm font-medium text-silver">确认密码</label>
        <div class="relative">
          <input
            v-model="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            placeholder="请再次输入密码"
            class="input-dark w-full h-11 px-4 pr-10 text-sm"
            @focus="onInputFocus"
            @blur="onInputBlur"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-ghost hover:text-silver transition-colors"
            @click="showConfirmPassword = !showConfirmPassword"
          >
            <svg v-if="!showConfirmPassword" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
              <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 验证码（注册模式） -->
      <div v-if="mode === 'register'" class="space-y-1.5">
        <label class="text-sm font-medium text-silver">验证码</label>
        <div class="flex gap-3">
          <input
            v-model="captchaCode"
            type="text"
            placeholder="请输入验证码"
            autocomplete="off"
            class="input-dark flex-1 h-11 px-4 text-sm"
            @focus="onInputFocus"
            @blur="onInputBlur"
          />
          <button
            type="button"
            class="h-11 rounded-lg overflow-hidden border border-edge flex-shrink-0"
            :disabled="captchaLoading"
            @click="refreshCaptcha"
          >
            <img
              v-if="captchaImage"
              :src="captchaImage"
              alt="验证码"
              class="h-full w-[120px] object-cover"
            />
            <span v-else class="px-4 text-xs text-ghost">加载中...</span>
          </button>
        </div>
      </div>

      <!-- 错误信息 -->
      <div
        v-if="localError"
        class="p-3 text-sm text-danger bg-danger/10 border border-danger/20 rounded-lg"
      >
        {{ localError }}
      </div>

      <!-- 提交按钮 -->
      <button
        type="submit"
        class="btn-primary w-full h-11 text-sm font-medium"
        :disabled="loading"
      >
        {{ loading ? (mode === 'login' ? '登录中...' : '注册中...') : (mode === 'login' ? '登录' : '注册') }}
      </button>
    </form>

    <!-- 底部切换链接 -->
    <div class="text-center text-sm text-ghost mt-6">
      {{ mode === 'login' ? '没有账号？' : '已有账号？' }}
      <button
        class="text-teal hover:underline font-medium"
        @click="switchMode(mode === 'login' ? 'register' : 'login')"
      >
        {{ mode === 'login' ? '立即注册' : '立即登录' }}
      </button>
    </div>
  </div>
</template>
