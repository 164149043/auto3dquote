/**
 * 用户认证状态管理 composable
 */

import { computed, ref } from 'vue'
import type { CaptchaResponse, ChangePasswordRequest, TokenResponse, UserResponse } from '../types/api'

const API_BASE = '/api/v1/auth'

interface UserInfo {
  id: number
  username: string
  role: string
  is_active: number
  created_at: string
}

// 模块级单例状态
const user = ref<UserInfo | null>(null)
const token = ref(localStorage.getItem('user_token') || '')
const loading = ref(false)
const error = ref('')
const showLoginModal = ref(false)

function authHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options?.headers || {}) },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `请求失败 (${res.status})`)
  }
  return res.json()
}

function setUserFromResponse(data: TokenResponse) {
  token.value = data.access_token
  localStorage.setItem('user_token', data.access_token)
  user.value = {
    id: data.user.id,
    username: data.user.username,
    role: data.user.role,
    is_active: data.user.is_active,
    created_at: data.user.created_at,
  }
}

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value && user.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function fetchCaptcha() {
    const res = await fetch(`${API_BASE}/captcha`)
    if (!res.ok) throw new Error('获取验证码失败')
    return res.json() as Promise<CaptchaResponse>
  }

  async function register(username: string, password: string, captchaId: string, captchaCode: string) {
    loading.value = true
    error.value = ''
    try {
      const data = await request<TokenResponse>('/register', {
        method: 'POST',
        body: JSON.stringify({
          username,
          password,
          confirm_password: password,
          captcha_id: captchaId,
          captcha_code: captchaCode,
        }),
      })
      setUserFromResponse(data)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '注册失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string): Promise<TokenResponse> {
    loading.value = true
    error.value = ''
    try {
      const data = await request<TokenResponse>('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      })
      setUserFromResponse(data)
      return data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '登录失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    try {
      const data = await request<UserResponse>('/me')
      user.value = {
        id: data.id,
        username: data.username,
        role: data.role,
        is_active: data.is_active,
        created_at: data.created_at,
      }
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('user_token')
    user.value = null
  }

  function openLoginModal() {
    error.value = ''
    showLoginModal.value = true
  }

  function closeLoginModal() {
    showLoginModal.value = false
    error.value = ''
  }

  function clearError() {
    error.value = ''
  }

  async function changePassword(data: ChangePasswordRequest): Promise<void> {
    await request('/password', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    showLoginModal,
    fetchCaptcha,
    register,
    login,
    fetchCurrentUser,
    logout,
    openLoginModal,
    closeLoginModal,
    clearError,
    changePassword,
  }
}
