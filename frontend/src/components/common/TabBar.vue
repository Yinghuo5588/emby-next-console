<template>
  <div class="tab-bar">
    <button
      v-for="item in tabs"
      :key="item.id"
      class="tab-item"
      :class="{ active: isActive(item.path) }"
      @click="navigate(item)"
    >
      <div class="tab-icon">
        <svg v-if="item.id === 'dashboard'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z"/><path d="M9 22V12H15V22"/></svg>
        <svg v-else-if="item.id === 'users'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21"/><circle cx="9" cy="7" r="4"/><path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13"/><path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88"/></svg>
        <svg v-else-if="item.id === 'stats'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20V14"/></svg>
        <svg v-else-if="item.id === 'risk'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18C1.64 18.3 1.55 18.65 1.55 19C1.55 19.35 1.64 19.7 1.82 20C2 20.3 2.26 20.56 2.58 20.74C2.9 20.92 3.27 21.01 3.64 21.01H20.36C20.73 21.01 21.1 20.92 21.42 20.74C21.74 20.56 22 20.3 22.18 20C22.36 19.7 22.45 19.35 22.45 19C22.45 18.65 22.36 18.3 22.18 18L13.71 3.86C13.53 3.56 13.27 3.32 12.97 3.15C12.66 2.98 12.32 2.89 11.97 2.89C11.62 2.89 11.28 2.98 10.97 3.15C10.67 3.32 10.41 3.56 10.29 3.86Z"/><path d="M12 9V13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
      </div>
      <span class="tab-label">{{ item.label }}</span>
    </button>

    <!-- More Panel -->
    <Transition name="panel">
      <div v-if="showMore" class="more-overlay" @click.self="showMore = false">
        <n-card class="more-panel" size="small">
          <n-button text block class="more-item" @click="go('/notifications')">🔔 通知</n-button>
          <n-divider style="margin: 8px 0" />
          <div class="more-group-label">用户管理</div>
          <n-button text block class="more-item" @click="go('/users')">用户列表</n-button>
          <n-button text block class="more-item" @click="go('/users/invites')">邀请管理</n-button>
          <n-button text block class="more-item" @click="go('/users/templates')">权限模板</n-button>
          <n-divider style="margin: 8px 0" />
          <n-button text block class="more-item" @click="go('/media')">媒体管理</n-button>
          <n-button text block class="more-item" @click="go('/calendar')">追剧日历</n-button>
          <n-button text block class="more-item" @click="go('/portal')">用户门户</n-button>
          <n-button text block class="more-item" @click="go('/tasks')">任务中心</n-button>
          <n-button text block class="more-item" @click="go('/poster')">海报工坊</n-button>
          <n-button text block class="more-item" @click="go('/settings')">设置</n-button>
          <n-divider style="margin: 8px 0" />
          <n-button text block class="more-item" @click="toggleTheme">
            {{ uiStore.isDark ? '☀️ 浅色模式' : '🌙 深色模式' }}
          </n-button>
          <n-button text block class="more-item" type="error" @click="handleLogout">退出登录</n-button>
        </n-card>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NCard, NButton, NDivider } from 'naive-ui'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const authStore = useAuthStore()

const showMore = ref(false)

const tabs = [
  { id: 'dashboard', label: '仪表盘', path: '/' },
  { id: 'users', label: '用户管理', path: '/users' },
  { id: 'stats', label: '统计', path: '/stats' },
  { id: 'risk', label: '风控', path: '/risk' },
  { id: 'more', label: '更多', path: '' },
]

function isActive(path: string) {
  if (!path) return false
  return route.path === path || route.path.startsWith(path + '/')
}

function navigate(item: typeof tabs[0]) {
  if (item.id === 'more') { showMore.value = true; return }
  router.push(item.path)
}

function go(path: string) {
  showMore.value = false
  router.push(path)
}

function toggleTheme() {
  uiStore.toggleTheme()
  showMore.value = false
}

async function handleLogout() {
  showMore.value = false
  await authStore.logout()
}
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--tab-height);
  background: var(--surface-strong);
  backdrop-filter: blur(var(--blur));
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 8px;
  padding-bottom: env(safe-area-inset-bottom, 0);
  z-index: 100;
}
@media (min-width: 769px) { .tab-bar { display: none; } }
.tab-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 6px 12px; border: none; background: none; cursor: pointer;
  color: var(--text-muted); transition: color 0.2s;
}
.tab-item.active { color: var(--brand); }
.tab-icon { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; }
.tab-label { font-size: 10px; font-weight: 500; }
.more-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200;
  display: flex; align-items: flex-end; justify-content: center;
}
.more-panel {
  width: 100%; max-width: 400px; border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  margin-bottom: var(--tab-height); max-height: 70vh; overflow-y: auto;
}
.more-item { justify-content: flex-start; padding: 10px 16px; font-size: 14px; }
.more-group-label {
  padding: 4px 16px; font-size: 11px; color: var(--text-muted);
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}
.panel-enter-active, .panel-leave-active { transition: opacity 0.25s; }
.panel-enter-active .more-panel, .panel-leave-active .more-panel { transition: transform 0.25s ease; }
.panel-enter-from, .panel-leave-to { opacity: 0; }
.panel-enter-from .more-panel { transform: translateY(100%); }
.panel-leave-to .more-panel { transform: translateY(100%); }
</style>
