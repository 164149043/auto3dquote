<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isAdmin = computed(() => route.path.startsWith('/admin'))
</script>

<template>
  <div class="min-h-screen bg-void relative">
    <!-- Noise texture overlay -->
    <div class="noise-overlay"></div>

    <!-- Top navigation bar -->
    <header class="fixed top-0 left-0 right-0 z-50 border-b border-edge/50" style="background: rgba(6,10,19,0.8); backdrop-filter: blur(20px);">
      <div class="max-w-[1440px] mx-auto px-6 h-14 flex items-center justify-between">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-3 no-underline group">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-teal to-teal-dim flex items-center justify-center shadow-lg" style="box-shadow: 0 0 12px rgba(0,229,199,0.3);">
            <svg class="w-4 h-4 text-void" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z"/>
            </svg>
          </div>
          <span class="font-display font-bold text-white text-sm tracking-wide group-hover:text-teal transition-colors duration-300">Auto3DQuote</span>
        </router-link>

        <!-- Nav links -->
        <div class="flex items-center gap-6">
          <router-link
            v-if="!isAdmin"
            to="/admin"
            class="text-xs font-medium text-ghost hover:text-teal no-underline transition-colors duration-200 tracking-wide uppercase"
          >
            管理后台
          </router-link>
          <router-link
            v-else
            to="/"
            class="text-xs font-medium text-ghost hover:text-teal no-underline transition-colors duration-200 tracking-wide uppercase"
          >
            返回报价
          </router-link>
          <div class="w-px h-4 bg-edge"></div>
          <span class="text-xs text-ghost/60 font-mono">v1.0</span>
        </div>
      </div>
    </header>

    <!-- Main content area -->
    <main class="pt-14 min-h-screen">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="border-t border-edge/30 py-6">
      <div class="max-w-[1440px] mx-auto px-6 flex items-center justify-between">
        <span class="text-xs text-ghost/40 font-mono">Auto3DQuote &mdash; 3D 打印自动报价系统</span>
        <span class="text-xs text-ghost/30 font-mono">Powered by PrusaSlicer</span>
      </div>
    </footer>
  </div>
</template>
