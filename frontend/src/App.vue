<template>
  <n-config-provider :theme="uiStore.isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#3b82f6',
    primaryColorHover: '#2563eb',
    primaryColorPressed: '#1d4ed8',
    primaryColorSuppl: '#3b82f6',
  },
}
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
