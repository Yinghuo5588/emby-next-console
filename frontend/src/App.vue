<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'

<<<<<<< HEAD
const route = useRoute()
const layout = computed(() =>
 route.meta.layout === 'auth' ? AuthLayout : DefaultLayout
)
</script>
=======
const uiStore = useUiStore()

onMounted(() => {
  uiStore.init()
})

onUnmounted(() => {
  uiStore.cleanup()
})
</script>

<style>
#app {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Apply theme to document root */
:root[data-theme="light"] {
  color-scheme: light;
}

:root[data-theme="dark"] {
  color-scheme: dark;
}
</style>
>>>>>>> 4960502 (feat: 前端全面重写 - iOS glassmorphism 风格 + 移动端适配)
