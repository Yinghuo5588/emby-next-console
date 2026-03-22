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
        <div class="more-panel card">
          <button class="more-item" @click="go('/notifications')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8C18 6.4087 17.3679 4.88258 16.2426 3.75736C15.1174 2.63214 13.5913 2 12 2C10.4087 2 8.88258 2.63214 7.75736 3.75736C6.63214 4.88258 6 6.4087 6 8C6 15 3 17 3 17H21C21 17 18 15 18 8Z"/><path d="M13.73 21C13.5542 21.3031 13.3019 21.5547 12.9982 21.7295C12.6946 21.9044 12.3504 21.9965 12 21.9965C11.6496 21.9965 11.3054 21.9044 11.0018 21.7295C10.6982 21.5547 10.4458 21.3031 10.27 21"/></svg>
            <span>通知</span>
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </button>
          <div class="more-group">
            <div class="more-group-label">用户管理</div>
            <button class="more-item" @click="go('/users')">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21"/><circle cx="9" cy="7" r="4"/><path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13"/><path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88"/></svg>
              <span>用户列表</span>
            </button>
            <button class="more-item" @click="go('/users/invites')">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9"/><polyline points="16 5 21 5 21 10"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              <span>邀请管理</span>
            </button>
            <button class="more-item" @click="go('/users/templates')">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"/><path d="M14 2V8H20"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H9H8"/></svg>
              <span>权限模板</span>
            </button>
          </div>
          <button class="more-item" @click="go('/media')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16L8.586 11.414C9.366 10.634 10.634 10.634 11.414 11.414L16 16M14 14L15.586 12.414C16.366 11.634 17.634 11.634 18.414 12.414L20 14M6 20H18C19.105 20 20 19.105 20 18V6C20 4.895 19.105 4 18 4H6C4.895 4 4 4.895 4 6V18C4 19.105 4.895 20 6 20Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            <span>媒体管理</span>
          </button>
          <button class="more-item" @click="go('/portal')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7L12 12L22 7L12 2Z"/><path d="M2 17L12 22L22 17"/><path d="M2 12L12 17L22 12"/></svg>
            <span>用户门户</span>
          </button>
          <button class="more-item" @click="go('/settings')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15C19.1278 15.6171 18.9788 16.3004 18.9788 17C18.9788 17.6996 19.1278 18.3829 19.4 19C19.5696 19.3875 19.8346 19.7229 20.1685 19.9674C20.5023 20.2119 20.8927 20.3568 21.3006 20.3872C21.7086 20.4175 22.1165 20.3322 22.4844 20.1404C22.8523 19.9486 23.1671 19.6571 23.3931 19.2971C23.6191 18.9371 23.7484 18.5214 23.7662 18.0939C23.784 17.6665 23.6898 17.2425 23.493 16.867C23.2963 16.4915 23.0038 16.1779 22.646 15.9573C22.2882 15.7368 21.8775 15.6171 21.4586 15.6115C21.0398 15.6059 20.6263 15.7146 20.2633 15.9254L19.4 15Z"/><path d="M4.6 9C4.87224 8.38295 5.02124 7.69964 5.02124 7C5.02124 6.30036 4.87224 5.61705 4.6 5C4.43042 4.61248 4.16536 4.27713 3.83153 4.03262C3.49769 3.78811 3.10732 3.64321 2.69938 3.61284C2.29144 3.58247 1.88354 3.66779 1.51562 3.85961C1.14769 4.05143 0.832935 4.34294 0.606918 4.70292C0.380901 5.0629 0.251564 5.4786 0.233775 5.90605C0.215985 6.3335 0.310175 6.75749 0.506953 7.133C0.703731 7.50852 0.996198 7.82213 1.35403 8.04272C1.71187 8.26331 2.12253 8.38295 2.5414 8.38855C2.96028 8.39415 3.37373 8.28544 3.73674 8.07465L4.6 9Z"/></svg>
            <span>设置</span>
          </button>
          <button class="more-item" @click="toggleTheme">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            <span>{{ isDark ? '浅色模式' : '深色模式' }}</span>
          </button>
          <button class="more-item logout" @click="handleLogout">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()
const authStore = useAuthStore()
const notifStore = useNotificationsStore()

const showMore = ref(false)
const isDark = computed(() => uiStore.isDark)
const unreadCount = computed(() => notifStore.unreadCount)

const tabs = [
  { id: 'dashboard', label: '仪表盘', path: '/dashboard' },
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
  -webkit-backdrop-filter: blur(var(--blur));
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 8px;
  padding-bottom: env(safe-area-inset-bottom, 0);
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
  padding: 6px 12px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-muted);
  transition: color 0.2s;
  -webkit-tap-highlight-color: transparent;
}

.tab-item.active {
  color: var(--brand);
}

.tab-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-label {
  font-size: 10px;
  font-weight: 500;
}

.more-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.more-panel {
  width: 100%;
  max-width: 400px;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: 8px 0;
  margin: 0;
  margin-bottom: var(--tab-height);
}

.more-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 20px;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text);
  font-size: 15px;
  transition: background 0.15s;
}

.more-item:hover {
  background: var(--bg-secondary);
}

.more-group {
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}

.more-group-label {
  padding: 8px 20px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.more-item.logout {
  color: var(--danger);
}

.badge {
  background: var(--danger);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
  margin-left: auto;
}

.panel-enter-active, .panel-leave-active {
  transition: opacity 0.25s;
}
.panel-enter-active .more-panel, .panel-leave-active .more-panel {
  transition: transform 0.25s ease;
}
.panel-enter-from, .panel-leave-to { opacity: 0; }
.panel-enter-from .more-panel { transform: translateY(100%); }
.panel-leave-to .more-panel { transform: translateY(100%); }
</style>
