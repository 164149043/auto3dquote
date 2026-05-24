<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useAuth } from '../../composables/useAuth'
import CharacterScene from './CharacterScene.vue'
import AuthForm from './AuthForm.vue'

const emit = defineEmits<{
  close: []
}>()

const { login, register, loading, error, closeLoginModal, clearError, fetchCaptcha } = useAuth()

const isTyping = ref(false)
const passwordVisible = ref(false)
const hasPassword = ref(false)

function onTypingChange(val: boolean) {
  isTyping.value = val
}

function onPasswordVisibilityChange(val: boolean) {
  passwordVisible.value = val
}

function onHasPasswordChange(val: boolean) {
  hasPassword.value = val
}

async function onSubmit(mode: 'login' | 'register', username: string, password: string, captchaId: string, captchaCode: string) {
  try {
    if (mode === 'login') {
      await login(username, password)
    } else {
      await register(username, password, captchaId, captchaCode)
    }
    closeLoginModal()
  } catch {
    // error is already set in composable
  }
}

function onOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    closeLoginModal()
  }
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
})

onUnmounted(() => {
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
        @click="onOverlayClick"
      >
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <!-- 弹窗 -->
        <div class="relative w-full max-w-[900px] glass-panel overflow-hidden animate-fade-in-scale" style="border-radius: 16px;">
          <!-- 关闭按钮 -->
          <button
            class="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-surface/80 text-ghost hover:text-white hover:bg-elevated transition-colors"
            @click="closeLoginModal"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <!-- 双栏布局 -->
          <div class="grid lg:grid-cols-2 min-h-[520px]">
            <!-- 左侧：动画角色 -->
            <div class="hidden lg:block">
              <CharacterScene
                :is-typing="isTyping"
                :password-visible="passwordVisible"
                :has-password="hasPassword"
              />
            </div>

            <!-- 右侧：认证表单 -->
            <div class="flex items-center justify-center p-8 bg-abyss">
              <AuthForm
                :loading="loading"
                :error="error"
                :fetch-captcha="fetchCaptcha"
                @submit="onSubmit"
                @typing-change="onTypingChange"
                @password-visibility-change="onPasswordVisibilityChange"
                @has-password-change="onHasPasswordChange"
                @clear-error="clearError"
              />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-leave-active {
  transition: all 0.25s ease-in;
}
.modal-enter-from {
  opacity: 0;
}
.modal-enter-from > div:last-child {
  transform: scale(0.95);
}
.modal-leave-to {
  opacity: 0;
}
.modal-leave-to > div:last-child {
  transform: scale(0.95);
}
</style>
