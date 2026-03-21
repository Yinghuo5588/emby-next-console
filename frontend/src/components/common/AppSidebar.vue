<template>
  <aside class="sidebar" :class="{ 'sidebar-hidden': !isDesktop }">
    <div class="sidebar-header">
      <div class="logo">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="32" height="32" rx="8" fill="var(--brand)"/>
          <path d="M12 10L20 16L12 22V10Z" fill="white"/>
        </svg>
        <span class="logo-text">Emby Next</span>
      </div>
    </div>
    
    <nav class="sidebar-nav">
      <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item" active-class="active">
        <component :is="item.icon" class="nav-icon" />
        <span class="nav-text">{{ item.label }}</span>
      </router-link>
    </nav>
    
    <div class="sidebar-footer">
      <button class="theme-toggle" @click="toggleTheme">
        <svg v-if="isDark" class="theme-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" fill="currentColor"/>
          <path d="M12 4V2M12 22V20M4 12H2M22 12H20M19.0711 19.0711L17.6569 17.6569M6.34315 6.34315L4.92893 4.92893M19.0711 4.92893L17.6569 6.34315M6.34315 17.6569L4.92893 19.0711" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <svg v-else class="theme-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 12.79C20.8427 14.4922 20.2039 16.1144 19.1582 17.4668C18.1125 18.8192 16.7035 19.8458 15.0957 20.4265C13.4879 21.0073 11.748 21.1181 10.0795 20.7461C8.41102 20.3741 6.88299 19.5345 5.67422 18.3258C4.46545 17.117 3.62594 15.589 3.2539 13.9205C2.88186 12.252 2.99274 10.5121 3.57348 8.9043C4.15423 7.29651 5.18085 5.8875 6.53323 4.84182C7.88562 3.79614 9.50779 3.15731 11.21 3C10.2134 4.34827 9.73385 6.00945 9.85849 7.68141C9.98314 9.35338 10.7039 10.9251 11.8894 12.1106C13.0749 13.2961 14.6466 14.0169 16.3186 14.1415C17.9906 14.2662 19.6517 13.7866 21 12.79Z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ isDark ? 'Light' : 'Dark' }}</span>
      </button>
      <button class="logout-btn" @click="handleLogout">
        <svg class="logout-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M16 17L21 12L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Logout</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useWindowSize } from '@vueuse/core'
import DashboardIcon from './icons/DashboardIcon.vue'
import UsersIcon from './icons/UsersIcon.vue'
import StatsIcon from './icons/StatsIcon.vue'
import RiskIcon from './icons/RiskIcon.vue'
import NotificationsIcon from './icons/NotificationsIcon.vue'
import SettingsIcon from './icons/SettingsIcon.vue'

const router = useRouter()
const { width } = useWindowSize()

const isDark = ref(false)
const isDesktop = computed(() => width.value >= 768)

const navItems = [
  { to: '/', label: 'Dashboard', icon: DashboardIcon },
  { to: '/users', label: 'Users', icon: UsersIcon },
  { to: '/stats', label: 'Stats', icon: StatsIcon },
  { to: '/risk', label: 'Risk', icon: RiskIcon },
  { to: '/notifications', label: 'Notifications', icon: NotificationsIcon },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const handleLogout = () => {
  // TODO: Implement logout logic
  router.push('/login')
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--surface);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: transform 0.3s ease;
}

.sidebar-hidden {
  transform: translateX(-100%);
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
}

.sidebar-nav {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  color: var(--text-muted);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.nav-item.active {
  background: var(--brand-light);
  color: var(--brand);
  font-weight: 500;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.nav-text {
  font-size: 0.95rem;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.theme-toggle,
.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.theme-toggle:hover,
.logout-btn:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.theme-icon,
.logout-icon {
  width: 20px;
  height: 20px;
}

@media (max-width: 767px) {
  .sidebar {
    transform: translateX(-100%);
  }
  
  .sidebar-hidden {
    transform: translateX(0);
  }
}
</style>