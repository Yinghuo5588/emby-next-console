<template>
  <n-layout has-sider class="default-layout">
    <AppSidebar v-if="!uiStore.isMobile" />
    <n-layout-content class="main-content">
      <router-view />
    </n-layout-content>
    <TabBar v-if="uiStore.isMobile" />
  </n-layout>
</template>

<script setup lang="ts">
import { NLayout, NLayoutContent } from 'naive-ui'
import { useUiStore } from '@/stores/ui'
import AppSidebar from '@/components/common/AppSidebar.vue'
import TabBar from '@/components/common/TabBar.vue'

const uiStore = useUiStore()
</script>

<style scoped>
.default-layout {
  min-height: 100vh;
}
.main-content {
  padding: 20px;
  background: var(--bg);
}
@media (max-width: 767px) {
  .main-content {
    padding: 12px;
    padding-bottom: calc(var(--tab-height) + 12px);
  }
}
</style>
