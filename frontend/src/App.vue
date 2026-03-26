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
                <template v-for="tab in tabs" :key="tab.path">
                  <router-link v-if="!tab.isMore" :to="tab.path" class="nav-item" :class="{ active: isActive(tab.path) }">
                    <span class="nav-icon" v-html="tab.icon"></span>
                    <span class="nav-label">{{ tab.label }}</span>
                  </router-link>
                  <button v-else class="nav-item" @click.prevent="showMore = !showMore">
                    <span class="nav-icon" v-html="tab.icon"></span>
                    <span class="nav-label">{{ tab.label }}</span>
                  </button>
                </template>
              </nav>
              <!-- More Bottom Sheet -->
              <Teleport to="body">
                <Transition name="fade">
                  <div v-if="showMore" class="more-overlay" @click="showMore = false" />
                </Transition>
                <Transition name="slide-up">
                  <div v-if="showMore" class="more-sheet">
                    <div class="more-handle" />
                    <button v-for="item in moreItems" :key="item.label" class="more-item" @click="$router.push(item.path); showMore = false">
                      <span class="more-item-icon">{{ item.icon }}</span>
                      <span>{{ item.label }}</span>
                    </button>
                    <button class="more-item more-item-cancel" @click="showMore = false">取消</button>
                  </div>
                </Transition>
              </Teleport>
            </div>
          </template>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
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
  { path: '/risk', label: '管控', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.76 3h16.94a2 2 0 0 0 1.76-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' },
  { path: '', label: '更多', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>', isMore: true },
]

const showMore = ref(false)
const moreItems = [
  { icon: '📊', label: '质量盘点', path: '/quality' },
  { icon: '⚙️', label: '设置', path: '/settings' },
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
.more-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 2000;
  backdrop-filter: blur(4px);
}
.more-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 2001;
  background: var(--surface, rgba(255,255,255,0.95));
  backdrop-filter: blur(20px);
  border-radius: 16px 16px 0 0;
  padding: 8px 8px calc(env(safe-area-inset-bottom, 0px) + 8px);
}
.more-handle {
  width: 36px;
  height: 5px;
  border-radius: 2.5px;
  background: var(--text-tertiary, #c7c7cc);
  margin: 4px auto 12px;
}
.more-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  border: none;
  background: none;
  color: var(--text, #1c1c1e);
  font-size: 16px;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  border-radius: 12px;
}
.more-item:active {
  background: var(--bg-secondary, #f2f2f7);
}
.more-item-icon {
  font-size: 20px;
  width: 28px;
  text-align: center;
}
.more-item-cancel {
  justify-content: center;
  color: var(--brand, #007AFF);
  font-weight: 600;
  margin-top: 8px;
  background: var(--bg-secondary, #f2f2f7);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.25s ease; }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
</style>
