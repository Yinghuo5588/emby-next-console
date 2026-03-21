<template>
  <div class="default-layout">
    <!-- Desktop Sidebar -->
    <AppSidebar v-if="!uiStore.isMobile" class="sidebar-desktop" />
    
    <!-- Main Content -->
    <main class="main-content" :class="{ 'with-sidebar': !uiStore.isMobile }">
      <router-view />
    </main>
    
    <!-- Mobile Tab Bar -->
    <TabBar v-if="uiStore.isMobile" class="tabbar-mobile" />
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import AppSidebar from '@/components/common/AppSidebar.vue'
import TabBar from '@/components/common/TabBar.vue'

const uiStore = useUiStore()
</script>

<style scoped>
.default-layout {
  min-height: 100vh;
  display: flex;
  background: var(--bg);
}

.sidebar-desktop {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 240px;
  z-index: 100;
}

.main-content {
  flex: 1;
  min-height: 100vh;
  padding: 20px;
  transition: margin-left 0.3s ease;
}

.main-content.with-sidebar {
  margin-left: 240px;
}

@media (max-width: 767px) {
  .main-content {
    padding: 12px;
    padding-bottom: calc(var(--tab-height) + 12px);
  }
}

.tabbar-mobile {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
}
</style>
