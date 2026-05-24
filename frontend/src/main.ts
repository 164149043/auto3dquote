import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import QuoterPage from './pages/QuoterPage.vue'
import AdminPage from './pages/AdminPage.vue'
import QuotesHistoryPage from './pages/QuotesHistoryPage.vue'
import { useAuth } from './composables/useAuth'
import './assets/main.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: QuoterPage },
    { path: '/admin', component: AdminPage },
    { path: '/my-quotes', component: QuotesHistoryPage },
  ],
})

// 恢复用户会话 + 路由守卫
let sessionRestored = false
router.beforeEach(async (to) => {
  // 路由守卫：需要登录的页面
  if (to.path === '/my-quotes') {
    const token = localStorage.getItem('user_token')
    if (!token) return '/'
  }

  if (sessionRestored) return
  sessionRestored = true

  const { fetchCurrentUser } = useAuth()
  const token = localStorage.getItem('user_token')
  if (token) {
    try {
      await fetchCurrentUser()
    } catch {
      // token 过期，已自动清除
    }
  }
})

createApp(App).use(router).mount('#app')
