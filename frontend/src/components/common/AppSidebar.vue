<template>
 <aside class="sidebar" :class="{ collapsed: ui.sidebarCollapsed }">
 <div class="logo">
 <span class="logo-icon">▶</span>
 <span v-if="!ui.sidebarCollapsed" class="logo-text">Emby Console</span>
 </div>
 <nav class="nav">
 <RouterLink
 v-for="item in navItems"
 :key="item.name"
 :to="item.to"
 class="nav-item"
 active-class="active"
 >
 <span class="nav-icon">{{ item.icon }}</span>
 <span v-if="!ui.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
 <span v-if="item.badge && !ui.sidebarCollapsed" class="nav-badge">{{ item.badge }}</span>
 </RouterLink>
 </nav>
 <div class="sidebar-footer">
 <button class="nav-item" @click="handleLogout">
 <span class="nav-icon">⏻</span>
 <span v-if="!ui.sidebarCollapsed">退出</span>
 </button>
 </div>
 </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useNotificationsStore } from '@/stores/notifications'

const auth = useAuthStore()
const ui = useUiStore()
const notif = useNotificationsStore()
const router = useRouter()

const navItems = computed(() => [
 { name: 'dashboard', to: '/dashboard', icon: '⬡', label: '仪表盘' },
 { name: 'stats', to: '/stats', icon: '◈', label: '播放统计' },
 { name: 'users', to: '/users', icon: '◉', label: '用户管理' },
 { name: 'risk', to: '/risk', icon: '⚠', label: '风控' },
 {
 name: 'notifications',
 to: '/notifications',
 icon: '◎',
 label: '通知中心',
 badge: notif.unreadCount > 0 ? notif.unreadCount : undefined,
 },
 { name: 'settings', to: '/settings', icon: '⚙', label: '系统设置' },
])

async function handleLogout() {
 await auth.logout()
 router.push('/login')
}
</script>

<style scoped>
.sidebar {
 width: var(--sidebar-width);
 height: 100vh;
 background: var(--color-surface);
 border-right: 1px solid var(--color-border);
 display: flex;
 flex-direction: column;
 flex-shrink: 0;
 transition: width 0.2s;
 position: sticky;
 top: 0;
}
.sidebar.collapsed { width: 56px; }

.logo {
 height: var(--header-height);
 display: flex;
 align-items: center;
 gap: 10px;
 padding: 0 16px;
 font-weight: 700;
 font-size: 15px;
 border-bottom: 1px solid var(--color-border);
 color: var(--color-primary);
}
.logo-icon { font-size: 18px; }

.nav { flex: 1; padding: 8px 0; overflow-y: auto; }

.nav-item {
 display: flex;
 align-items: center;
 gap: 10px;
 padding: 9px 16px;
 color: var(--color-text-muted);
 border-radius: 0;
 width: 100%;
 font-size: 13.5px;
 transition: color 0.15s, background 0.15s;
 position: relative;
}
.nav-item:hover { color: var(--color-text); background: var(--color-surface-2); }
.nav-item.active { color: var(--color-primary); background: rgba(99,102,241,.1); }

.nav-icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }

.nav-badge {
 margin-left: auto;
 background: var(--color-danger);
 color: #fff;
 border-radius: 10px;
 font-size: 11px;
 padding: 1px 6px;
 min-width: 18px;
 text-align: center;
}

.sidebar-footer {
 border-top: 1px solid var(--color-border);
 padding: 8px 0;
}
</style>