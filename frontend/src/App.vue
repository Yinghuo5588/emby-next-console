<template>
  <n-config-provider :theme="uiStore.isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <!-- 登录页不带导航 -->
          <template v-if="isLoginPage">
            <router-view />
          </template>
          <!-- 主应用带底部导航 -->
          <template v-else>
            <div class="app-layout">
              <div class="app-content">
                <router-view v-slot="{ Component }">
                  <transition name="page-slide" mode="out-in">
                    <component :is="Component" />
                  </transition>
                </router-view>
              </div>
              <nav class="bottom-nav">
                <router-link v-for="tab in tabs" :key="tab.path" :to="tab.path" class="nav-item" :class="{ active: isActive(tab.path) }">
                  <span class="nav-icon" v-html="tab.icon"></span>
                  <span class="nav-label">{{ tab.label }}</span>
                </router-link>
              </nav>
            </div>
          </template>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
const route = useRoute()

const isLoginPage = computed(() => route.name === 'Login' || route.name === 'UserDetail')

const tabs = [
  { path: '/stats', label: '统计', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="12" width="4" height="9"/><rect x="10" y="7" width="4" height="14"/><rect x="17" y="3" width="4" height="18"/></svg>' },
  { path: '/users', label: '用户', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
  { path: '/settings', label: '设置', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

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
  Button: { borderRadiusMedium: '12px', borderRadiusSmall: '10px', fontWeight: '600' },
  Card: { borderRadius: '12px', borderColor: 'rgba(0, 0, 0, 0.04)', colorEmbedded: '#f2f2f7' },
  Tag: { borderRadius: '8px' },
  Input: { borderRadius: '10px', border: '1px solid rgba(0, 0, 0, 0.06)', borderHover: '1px solid #007AFF', borderFocus: '1px solid #007AFF' },
  Select: { peers: { InternalSelection: { borderRadius: '10px', border: '1px solid rgba(0, 0, 0, 0.06)', borderHover: '1px solid #007AFF', borderFocus: '1px solid #007AFF', borderActive: '1px solid #007AFF' } } },
  Modal: { borderRadius: '16px' },
  DataTable: { borderRadius: '12px', borderColor: 'rgba(0, 0, 0, 0.04)', thColor: 'transparent', tdColor: 'transparent', tdColorHover: 'rgba(0, 0, 0, 0.02)' },
  Tabs: { tabBorderRadius: '10px', tabFontWeight: '600' },
  Menu: { borderRadius: '8px', itemColorActive: 'rgba(0, 122, 255, 0.08)', itemColorActiveHover: 'rgba(0, 122, 255, 0.12)', itemTextColorActive: '#007AFF', itemIconColorActive: '#007AFF' },
  Alert: { borderRadius: '12px' },
}
</script>

<style>
#app {
  min-height: 100vh;
  background: var(--bg);
}
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.app-content {
  flex: 1;
  padding: 0 1rem;
  padding-bottom: 80px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 64px;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  z-index: 1000;
}
@media (prefers-color-scheme: dark) {
  .bottom-nav {
    background: rgba(28, 28, 30, 0.85);
  }
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 20px;
  text-decoration: none;
  color: var(--text-muted);
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}
.nav-item.active {
  color: var(--brand);
}
.nav-icon {
  width: 22px;
  height: 22px;
}
.nav-icon svg {
  width: 100%;
  height: 100%;
}
.nav-label {
  font-size: 0.65rem;
  font-weight: 500;
}
</style>
