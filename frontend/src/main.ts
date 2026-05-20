import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import QuoterPage from './pages/QuoterPage.vue'
import AdminPage from './pages/AdminPage.vue'
import './assets/main.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: QuoterPage },
    { path: '/admin', component: AdminPage },
  ],
})

createApp(App).use(router).mount('#app')
