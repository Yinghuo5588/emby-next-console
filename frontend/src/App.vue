<template>
  <n-config-provider :theme="uiStore.isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <router-view v-slot="{ Component }">
            <transition name="page-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
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

// iOS-style Naive UI theme overrides
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#007AFF',
    primaryColorHover: '#0A84FF',
    primaryColorPressed: '#0066D6',
    primaryColorSuppl: '#007AFF',
    successColor: '#34C759',
    warningColor: '#FF9500',
    errorColor: '#FF3B30',
    borderRadius: '12px',
    borderRadiusSmall: '8px',
    fontFamily: `-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC', sans-serif`,
    fontSize: '15px',
    fontSizeSmall: '13px',
    fontSizeMini: '11px',
  },
  Button: {
    borderRadiusMedium: '12px',
    borderRadiusSmall: '10px',
    fontWeight: '600',
  },
  Card: {
    borderRadius: '12px',
    borderColor: 'rgba(0, 0, 0, 0.04)',
    colorEmbedded: '#f2f2f7',
  },
  Tag: {
    borderRadius: '8px',
  },
  Input: {
    borderRadius: '10px',
    border: '1px solid rgba(0, 0, 0, 0.06)',
    borderHover: '1px solid #007AFF',
    borderFocus: '1px solid #007AFF',
  },
  Select: {
    peers: {
      InternalSelection: {
        borderRadius: '10px',
        border: '1px solid rgba(0, 0, 0, 0.06)',
        borderHover: '1px solid #007AFF',
        borderFocus: '1px solid #007AFF',
        borderActive: '1px solid #007AFF',
      }
    }
  },
  Modal: {
    borderRadius: '16px',
  },
  DataTable: {
    borderRadius: '12px',
    borderColor: 'rgba(0, 0, 0, 0.04)',
    thColor: 'transparent',
    tdColor: 'transparent',
    tdColorHover: 'rgba(0, 0, 0, 0.02)',
  },
  Tabs: {
    tabBorderRadius: '10px',
    tabFontWeight: '600',
  },
  Menu: {
    borderRadius: '8px',
    itemColorActive: 'rgba(0, 122, 255, 0.08)',
    itemColorActiveHover: 'rgba(0, 122, 255, 0.12)',
    itemTextColorActive: '#007AFF',
    itemIconColorActive: '#007AFF',
  },
  Alert: {
    borderRadius: '12px',
  },
}
</script>

<style>
#app {
  min-height: 100vh;
  background: var(--bg);
}
</style>
