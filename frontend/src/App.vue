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
                <router-link
                  v-for="tab in mainTabs"
                  :key="tab.path"
                  :to="tab.path"
                  class="nav-item"
                  :class="{ active: isActive(tab.path) }"
                >
                  <IosIcon :name="isActive(tab.path) ? tab.activeIcon || tab.icon : tab.icon" :size="22" :color="isActive(tab.path) ? 'var(--brand)' : 'var(--text-muted)'" :stroke-width="isActive(tab.path) ? 2.2 : 1.8" />
                  <span class="nav-label">{{ tab.label }}</span>
                </router-link>
                <button class="nav-item" :class="{ active: isMoreActive }" @click.prevent="showMore = !showMore">
                  <IosIcon name="more" :size="22" :color="isMoreActive ? 'var(--brand)' : 'var(--text-muted)'" :stroke-width="isMoreActive ? 2.2 : 1.8" />
                  <span class="nav-label">更多</span>
                </button>
              </nav>
              <!-- More Bottom Sheet -->
              <Teleport to="body">
                <Transition name="fade">
                  <div v-if="showMore" class="more-overlay" @click="showMore = false" />
                </Transition>
                <Transition name="slide-up">
                  <div v-if="showMore" class="more-sheet">
                    <div class="more-handle" />
                    <div class="more-section">
                      <div class="more-section-label">工具</div>
                      <button v-for="item in moreItems" :key="item.label" class="more-item" @click="$router.push(item.path); showMore = false">
                        <span class="more-item-icon"><IosIcon :name="item.icon" :size="20" color="var(--brand)" /></span>
                        <span>{{ item.label }}</span>
                        <span class="more-item-arrow">›</span>
                      </button>
                    </div>
                    <div class="more-divider" />
                    <div class="more-section">
                      <button class="more-item" @click="toggleDark(); showMore = false">
                        <span class="more-item-icon">{{ uiStore.isDark ? '🌙' : '☀️' }}</span>
                        <span>{{ uiStore.isDark ? '浅色模式' : '深色模式' }}</span>
                        <span class="more-item-check">{{ uiStore.isDark ? '✓' : '' }}</span>
                      </button>
                      <button class="more-item" @click="$router.push(settingsItem.path); showMore = false">
                        <span class="more-item-icon"><IosIcon :name="settingsItem.icon" :size="20" color="var(--text-muted)" /></span>
                        <span>{{ settingsItem.label }}</span>
                        <span class="more-item-arrow">›</span>
                      </button>
                    </div>
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
import IosIcon from '@/components/common/IosIcon.vue'

const uiStore = useUiStore()
const route = useRoute()

const isLoginPage = computed(() => route.name === 'Login' || route.name === 'UserDetail')

const mainTabs = [
  { path: '/stats', label: '统计', icon: 'chart', activeIcon: 'chart' },
  { path: '/users', label: '用户', icon: 'users', activeIcon: 'users' },
  { path: '/risk', label: '管控', icon: 'shield', activeIcon: 'shield' },
]

const morePaths = ['/calendar', '/quality', '/settings']
const isMoreActive = computed(() => morePaths.some(p => route.path.startsWith(p)))

const showMore = ref(false)
const moreItems = [
  { icon: 'calendar', label: '追剧日历', path: '/calendar' },
  { icon: 'palette', label: '质量盘点', path: '/quality' },
  { icon: 'bell', label: '通知', path: '/notify' },
  { icon: 'link', label: 'API 密钥', path: '/api-keys' },
]
const settingsItem = { icon: 'settings', label: '设置', path: '/settings' }

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function toggleDark() {
  uiStore.toggleTheme()
  showMore.value = false
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
#app { min-height: 100vh; background: var(--bg); }
.app-layout { display: flex; flex-direction: column; min-height: 100vh; }
.app-content { flex: 1; padding: 0 1rem; padding-bottom: 80px; overflow-y: auto; -webkit-overflow-scrolling: touch; }

/* ── 底部导航 ── */
.bottom-nav {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; justify-content: space-around; align-items: center;
  height: 64px;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border-top: 0.5px solid var(--border);
  z-index: 1000;
}
@media (prefers-color-scheme: dark) {
  .bottom-nav { background: rgba(28, 28, 30, 0.82); }
}
.nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 6px 20px; text-decoration: none;
  color: var(--text-muted);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
  position: relative; border: none; background: none; cursor: pointer;
  font-family: inherit;
}
.nav-item.active {
  color: var(--brand);
  transform: scale(1.05);
}
.nav-item:active { transform: scale(0.92); }
.nav-item.active::after {
  content: '';
  position: absolute; bottom: -1px; left: 50%;
  transform: translateX(-50%);
  width: 18px; height: 3px; border-radius: 2px;
  background: var(--brand);
}
.nav-label { font-size: 0.65rem; font-weight: 500; transition: font-weight 0.2s; }
.nav-item.active .nav-label { font-weight: 700; }

/* ── More 底部弹出 ── */
.more-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4); z-index: 2000;
  backdrop-filter: blur(4px);
}
.more-sheet {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 2001;
  background: var(--surface, rgba(255,255,255,0.95));
  backdrop-filter: blur(20px);
  border-radius: 20px 20px 0 0;
  padding: 8px 12px calc(env(safe-area-inset-bottom, 0px) + 12px);
}
.more-handle {
  width: 36px; height: 5px; border-radius: 2.5px;
  background: var(--text-tertiary, #c7c7cc);
  margin: 4px auto 12px;
}
.more-section-label {
  font-size: 0.7rem; font-weight: 600;
  color: var(--text-muted, #8e8e93);
  text-transform: uppercase; letter-spacing: 0.06em;
  padding: 6px 12px 4px;
}
.more-divider {
  height: 0.5px; background: var(--border, rgba(0,0,0,0.06));
  margin: 4px 12px;
}
.more-item {
  display: flex; align-items: center; gap: 12px;
  width: 100%; padding: 14px 12px;
  border: none; background: none;
  color: var(--text, #1c1c1e);
  font-size: 16px; font-family: inherit;
  cursor: pointer; text-align: left; border-radius: 12px;
  transition: background 0.15s;
}
.more-item:active { background: var(--bg-secondary, #f2f2f7); }
.more-item-icon { font-size: 20px; width: 28px; text-align: center; }
.more-item-arrow { margin-left: auto; font-size: 1.2rem; color: var(--text-muted); opacity: 0.3; }
.more-item-check { margin-left: auto; font-size: 1rem; color: var(--brand); font-weight: 700; }
.more-item-cancel {
  justify-content: center;
  color: var(--brand, #007AFF); font-weight: 600;
  margin-top: 8px; background: var(--bg-secondary, #f2f2f7);
  border-radius: 14px;
}
.more-item-cancel .more-item-arrow { display: none; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-up-enter-active, .slide-up-leave-active { transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1); }
.slide-up-enter-from, .slide-up-leave-to { transform: translateY(100%); }
</style>
