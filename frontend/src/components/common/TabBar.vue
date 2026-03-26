<template>
  <nav class="tab-bar">
    <router-link
      v-for="item in tabs"
      :key="item.id"
      :to="item.path || '#'"
      class="tab-item"
      :class="{ active: isActive(item.path), 'more-btn': item.id === 'more' }"
      @click.prevent="item.id === 'more' ? (showMore = true) : undefined"
    >
      <div class="tab-icon">
        <svg v-if="item.id === 'dashboard'" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z"/><path d="M9 22V12H15V22"/></svg>
        <svg v-else-if="item.id === 'users'" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21"/><circle cx="9" cy="7" r="4"/><path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13"/><path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88"/></svg>
        <svg v-else-if="item.id === 'stats'" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20V14"/></svg>
        <svg v-else-if="item.id === 'risk'" width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18C1.64 18.3 1.55 18.65 1.55 19C1.55 19.35 1.64 19.7 1.82 20C2 20.3 2.26 20.56 2.58 20.74C2.9 20.92 3.27 21.01 3.64 21.01H20.36C20.73 21.01 21.1 20.92 21.42 20.74C21.74 20.56 22 20.3 22.18 20C22.36 19.7 22.45 19.35 22.45 19C22.45 18.65 22.36 18.3 22.18 18L13.71 3.86C13.53 3.56 13.27 3.32 12.97 3.15C12.66 2.98 12.32 2.89 11.97 2.89C11.62 2.89 11.28 2.98 10.97 3.15C10.67 3.32 10.41 3.56 10.29 3.86Z"/><path d="M12 9V13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <svg v-else width="25" height="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
      </div>
      <span class="tab-label">{{ item.label }}</span>
    </router-link>

    <!-- More Bottom Sheet -->
    <Teleport to="body">
      <Transition name="ios-modal-mask">
        <div v-if="showMore" class="ios-mask" @click.self="showMore = false" />
      </Transition>
      <Transition name="bottom-sheet">
        <div v-if="showMore" class="ios-bottom-sheet">
          <div class="sheet-handle" />
          <div class="sheet-content">
            <div class="sheet-section" v-for="section in moreSections" :key="section.title">
              <div class="sheet-section-label">{{ section.title }}</div>
              <div class="sheet-group">
                <button v-for="item in section.items" :key="item.label" class="sheet-item" @click="item.action(); showMore = false">
                  <span class="sheet-icon">{{ item.icon }}</span>
                  <span>{{ item.label }}</span>
                </button>
              </div>
            </div>
            <div class="sheet-section">
              <div class="sheet-group">
                <button class="sheet-item" @click="toggleTheme">
                  <span class="sheet-icon">{{ uiStore.isDark ? '☀️' : '🌙' }}</span>
                  <span>{{ uiStore.isDark ? '浅色模式' : '深色模式' }}</span>
                </button>
                <button class="sheet-item sheet-item-danger" @click="handleLogout">
                  <span class="sheet-icon">🚪</span>
                  <span>退出登录</span>
                </button>
              </div>
            </div>
            <div class="sheet-cancel">
              <button class="sheet-cancel-btn" @click="showMore = false">取消</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const authStore = useAuthStore()
const showMore = ref(false)

const tabs = [
  { id: 'dashboard', label: '仪表盘', path: '/' },
  { id: 'users', label: '用户', path: '/users' },
  { id: 'stats', label: '统计', path: '/stats' },
  { id: 'risk', label: '风控', path: '/risk' },
  { id: 'more', label: '更多', path: '' },
]

const moreSections = [
  {
    title: '',
    items: [
      { icon: '🔔', label: '通知', action: () => router.push('/notifications') },
    ],
  },
  {
    title: '用户管理',
    items: [
      { icon: '👥', label: '用户列表', action: () => router.push('/users') },
      { icon: '🎟️', label: '邀请管理', action: () => router.push('/users/invites') },
      { icon: '📋', label: '权限模板', action: () => router.push('/users/templates') },
    ],
  },
  {
    title: '其他',
    items: [
      { icon: '🎬', label: '媒体管理', action: () => router.push('/media') },
      { icon: '📊', label: '质量盘点', action: () => router.push('/quality') },
      { icon: '📅', label: '追剧日历', action: () => router.push('/calendar') },
      { icon: '🌐', label: '用户门户', action: () => router.push('/portal') },
      { icon: '⚡', label: '任务中心', action: () => router.push('/tasks') },
      { icon: '🎨', label: '海报工坊', action: () => router.push('/poster') },
      { icon: '⚙️', label: '设置', action: () => router.push('/settings') },
    ],
  },
]

function isActive(path: string) {
  if (!path) return false
  return route.path === path || (path !== '/' && route.path.startsWith(path + '/'))
}

function toggleTheme() { uiStore.toggleTheme() }
async function handleLogout() { await authStore.logout() }
</script>

<style scoped>
/* ── Tab Bar (iOS frosted glass) ── */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--tab-height);
  padding-bottom: var(--safe-bottom);
  background: var(--surface-strong);
  backdrop-filter: blur(var(--blur-heavy));
  -webkit-backdrop-filter: blur(var(--blur-heavy));
  border-top: 0.5px solid var(--separator);
  display: flex;
  align-items: flex-start;
  justify-content: space-around;
  z-index: 100;
}

@media (min-width: 769px) {
  .tab-bar { display: none; }
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0 2px;
  min-width: 64px;
  text-decoration: none;
  color: var(--text-muted);
  transition: color 0.2s;
  -webkit-tap-highlight-color: transparent;
}
.tab-item.active {
  color: var(--brand);
}
.tab-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tab-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

/* ── iOS Mask ── */
.ios-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.ios-modal-mask-enter-active,
.ios-modal-mask-leave-active {
  transition: opacity 0.3s;
}
.ios-modal-mask-enter-from,
.ios-modal-mask-leave-to {
  opacity: 0;
}

/* ── iOS Bottom Sheet ── */
.ios-bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 201;
  background: var(--surface-strong);
  backdrop-filter: blur(var(--blur-heavy));
  -webkit-backdrop-filter: blur(var(--blur-heavy));
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding-bottom: calc(var(--safe-bottom) + 8px);
  max-height: 80vh;
  overflow-y: auto;
}

.sheet-handle {
  width: 36px;
  height: 5px;
  border-radius: 2.5px;
  background: var(--text-tertiary);
  margin: 8px auto;
}

.sheet-content {
  padding: 0 8px;
}

.sheet-section {
  margin-bottom: 16px;
}

.sheet-section-label {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  padding: 4px 16px 6px;
}

.sheet-group {
  background: var(--surface-grouped);
  border-radius: var(--radius);
  overflow: hidden;
}

.sheet-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  color: var(--text);
  font-size: 16px;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
  border-bottom: 0.5px solid var(--separator);
}
.sheet-item:last-child {
  border-bottom: none;
}
.sheet-item:active {
  background: var(--bg-secondary);
}
.sheet-item-danger {
  color: var(--danger);
}

.sheet-icon {
  font-size: 20px;
  width: 28px;
  text-align: center;
}

.sheet-cancel {
  margin-top: 8px;
  background: var(--surface-grouped);
  border-radius: var(--radius);
  overflow: hidden;
}

.sheet-cancel-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 14px;
  border: none;
  background: none;
  color: var(--brand);
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
}
.sheet-cancel-btn:active {
  background: var(--bg-secondary);
}
</style>
