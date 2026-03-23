<template>
  <n-layout-sider
    v-if="isDesktop"
    bordered
    collapse-mode="width"
    :collapsed-width="64"
    :width="240"
    :collapsed="collapsed"
    show-trigger="arrow-circle"
    @collapse="collapsed = true"
    @expand="collapsed = false"
    class="app-sider"
  >
    <div class="sider-header">
      <div class="logo">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="var(--brand)"/>
          <path d="M12 10L20 16L12 22V10Z" fill="white"/>
        </svg>
        <span v-if="!collapsed" class="logo-text">Emby Next</span>
      </div>
    </div>

    <n-menu
      :collapsed="collapsed"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :options="menuOptions"
      :value="activeKey"
      @update:value="handleMenuChange"
    />

    <div class="sider-footer">
      <n-button quaternary block :size="collapsed ? 'tiny' : 'small'" @click="toggleTheme">
        {{ uiStore.isDark ? '☀️' : '🌙' }}{{ collapsed ? '' : (uiStore.isDark ? ' Light' : ' Dark') }}
      </n-button>
      <n-button quaternary block :size="collapsed ? 'tiny' : 'small'" type="error" @click="handleLogout">
        {{ collapsed ? '→' : 'Logout' }}
      </n-button>
    </div>
  </n-layout-sider>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useWindowSize } from '@vueuse/core'
import type { MenuOption } from 'naive-ui'
import { NLayoutSider, NMenu, NButton } from 'naive-ui'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import DashboardIcon from './icons/DashboardIcon.vue'
import UsersIcon from './icons/UsersIcon.vue'
import StatsIcon from './icons/StatsIcon.vue'
import MediaIcon from './icons/MediaIcon.vue'
import CalendarIcon from './icons/CalendarIcon.vue'
import RiskIcon from './icons/RiskIcon.vue'
import NotificationsIcon from './icons/NotificationsIcon.vue'
import SettingsIcon from './icons/SettingsIcon.vue'

const router = useRouter()
const route = useRoute()
const { width } = useWindowSize()
const uiStore = useUiStore()
const authStore = useAuthStore()

const collapsed = ref(false)
const isDesktop = computed(() => width.value >= 768)
const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/users/invites')) return '/users/invites'
  if (path.startsWith('/users/templates')) return '/users/templates'
  if (path.startsWith('/users')) return '/users'
  if (path.startsWith('/stats/content')) return '/stats/content'
  if (path.startsWith('/stats/users')) return '/stats/users'
  if (path.startsWith('/stats')) return '/stats'
  return path
})

function renderIcon(Icon: any) {
  return () => h(Icon, { style: 'width: 18px; height: 18px' })
}

const menuOptions: MenuOption[] = [
  { label: 'Dashboard', key: '/', icon: renderIcon(DashboardIcon) },
  {
    label: '用户管理',
    key: '/users',
    icon: renderIcon(UsersIcon),
    children: [
      { label: '用户列表', key: '/users' },
      { label: '邀请管理', key: '/users/invites' },
      { label: '权限模板', key: '/users/templates' },
    ],
  },
  { label: '分析总览', key: '/stats', icon: renderIcon(StatsIcon) },
  { label: '内容分析', key: '/stats/content', icon: renderIcon(StatsIcon) },
  { label: '用户分析', key: '/stats/users', icon: renderIcon(StatsIcon) },
  { label: '媒体管理', key: '/media', icon: renderIcon(MediaIcon) },
  { label: '追剧日历', key: '/calendar', icon: renderIcon(CalendarIcon) },
  { label: 'Risk', key: '/risk', icon: renderIcon(RiskIcon) },
  { label: 'Notifications', key: '/notifications', icon: renderIcon(NotificationsIcon) },
  { label: '任务中心', key: '/tasks', icon: renderIcon(SettingsIcon) },
  { label: '海报工坊', key: '/poster', icon: renderIcon(SettingsIcon) },
  { label: 'Settings', key: '/settings', icon: renderIcon(SettingsIcon) },
]

function handleMenuChange(key: string) { router.push(key) }
function toggleTheme() { uiStore.toggleTheme() }
async function handleLogout() { await authStore.logout() }
</script>

<style scoped>
.app-sider { background: var(--surface) !important; }
.sider-header { padding: 1rem 1.25rem; border-bottom: 1px solid var(--border); }
.logo { display: flex; align-items: center; gap: 0.5rem; }
.logo-text { font-size: 1.1rem; font-weight: 600; color: var(--text); white-space: nowrap; }
.sider-footer { padding: 0.5rem; display: flex; flex-direction: column; gap: 0.25rem; }
</style>
