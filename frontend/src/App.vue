<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'

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
}
</style>
