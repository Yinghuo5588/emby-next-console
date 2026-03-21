<template>
  <div class="tab-bar">
    <div class="tab-items">
      <button
        v-for="item in tabItems"
        :key="item.id"
        class="tab-item"
        :class="{ active: activeTab === item.id }"
        @click="handleTabClick(item)"
      >
        <div class="tab-icon">
          <component :is="item.icon" />
        </div>
        <span class="tab-label">{{ item.label }}</span>
        <div v-if="activeTab === item.id" class="active-indicator"></div>
      </button>
    </div>
    
    <!-- More Panel -->
    <div v-if="showMorePanel" class="more-panel">
      <div class="panel-backdrop" @click="showMorePanel = false"></div>
      <div class="panel-content">
        <div class="panel-header">
          <h3>More</h3>
          <button class="close-button" @click="showMorePanel = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="panel-items">
          <button class="panel-item" @click="handleMoreClick('notifications')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M18 8C18 6.4087 17.3679 4.88258 16.2426 3.75736C15.1174 2.63214 13.5913 2 12 2C10.4087 2 8.88258 2.63214 7.75736 3.75736C6.63214 4.88258 6 6.4087 6 8C6 15 3 17 3 17H21C21 17 18 15 18 8Z" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13.73 21C13.5542 21.3031 13.3019 21.5547 12.9982 21.7295C12.6946 21.9044 12.3504 21.9965 12 21.9965C11.6496 21.9965 11.3054 21.9044 11.0018 21.7295C10.6982 21.5547 10.4458 21.3031 10.27 21" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Notifications</span>
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </button>
          <button class="panel-item" @click="handleMoreClick('settings')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M19.4 15C19.2661 15.3044 19.1334 15.6091 19.0018 15.9141C18.9499 16.0486 18.9216 16.1911 18.9183 16.3356C18.915 16.4801 18.9368 16.624 18.9826 16.7611C19.0284 16.8982 19.0974 17.0263 19.1863 17.1396C19.2752 17.2529 19.3825 17.3496 19.5033 17.425C19.6241 17.5004 19.7564 17.5532 19.8941 17.581C20.0318 17.6088 20.1727 17.6111 20.3111 17.5879C20.4495 17.5647 20.5831 17.5163 20.7053 17.445C20.8275 17.3737 20.9363 17.2807 21.0264 17.1706L21.0264 17.1706C21.1165 17.0605 21.1864 16.9352 21.2326 16.8006C21.2788 16.6661 21.3005 16.5246 21.2966 16.3827C21.2927 16.2408 21.2632 16.1009 21.2097 15.9699C21.1562 15.8389 21.0797 15.7191 20.9841 15.6163C20.8885 15.5135 20.7755 15.4295 20.6508 15.3684C20.5261 15.3073 20.3919 15.2702 20.2549 15.259H20.2549C20.1179 15.2478 19.9803 15.2627 19.8488 15.303C19.7173 15.3433 19.5943 15.4083 19.4866 15.4944L19.4 15Z" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M19.4 15C19.2219 14.6992 19.0441 14.3981 18.8667 14.0967C18.8116 13.9988 18.7774 13.8902 18.7665 13.7781C18.7556 13.666 18.7682 13.5531 18.8035 13.4465C18.8388 13.3399 18.8959 13.2421 18.9709 13.1596C19.0459 13.0771 19.137 13.0119 19.2383 12.9684C19.3396 12.9249 19.4487 12.9042 19.5584 12.9077C19.6681 12.9112 19.7758 12.9388 19.8742 12.9886C19.9726 13.0384 20.0594 13.1092 20.1288 13.1962L20.1288 13.1962C20.1982 13.2832 20.2486 13.3844 20.2766 13.4929C20.3046 13.6014 20.3095 13.7147 20.291 13.8255C20.2725 13.9363 20.231 14.0421 20.1692 14.1361C20.1074 14.2301 20.0268 14.3102 19.9325 14.3714C19.8382 14.4326 19.7323 14.4736 19.6214 14.4918C19.5105 14.51 19.3971 14.505 19.2885 14.4772C19.1799 14.4494 19.0785 14.3994 18.9908 14.3304L19.4 15Z" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Settings</span>
          </button>
          <button class="panel-item" @click="toggleTheme">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 12.79C20.8427 14.4922 20.2039 16.1144 19.1582 17.4668C18.1126 18.8192 16.7035 19.8458 15.0957 20.4265C13.4879 21.0073 11.748 21.1181 10.0795 20.7461C8.41104 20.3741 6.88299 19.5345 5.67422 18.3258C4.46545 17.117 3.62593 15.589 3.2539 13.9205C2.88187 12.252 2.99274 10.5121 3.57348 8.9043C4.15423 7.29651 5.18085 5.88737 6.53323 4.84175C7.88562 3.79614 9.50782 3.15731 11.21 3C10.2134 4.34827 9.73385 6.00945 9.85854 7.68141C9.98324 9.35338 10.7039 10.9251 11.8894 12.1106C13.0749 13.2961 14.6466 14.0168 16.3186 14.1415C17.9906 14.2662 19.6517 13.7866 21 12.79Z" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ uiStore.isDark ? 'Light Mode' : 'Dark Mode' }}</span>
          </button>
          <button class="panel-item logout" @click="handleLogout">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" 
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M16 17L21 12L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const router = useRouter()
const uiStore = useUiStore()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()

const activeTab = ref('dashboard')
const showMorePanel = ref(false)

const unreadCount = computed(() => notificationsStore.unreadCount)

const tabItems = [
  { id: 'dashboard', label: 'Dashboard', icon: DashboardIcon },
  { id: 'users', label: 'Users', icon: UsersIcon },
  { id: 'stats', label: 'Stats', icon: StatsIcon },
  { id: 'risk', label: 'Risk', icon: RiskIcon },
  { id: 'more', label: 'More', icon: MoreIcon },
]

function handleTabClick(item: any) {
  if (item.id === 'more') {
    showMorePanel.value = true
    return
  }
  
  activeTab.value = item.id
  router.push(`/${item.id}`)
}

function handleMoreClick(action: string) {
  showMorePanel.value = false
  
  switch (action) {
    case 'notifications':
      router.push('/notifications')
      break
    case 'settings':
      router.push('/settings')
      break
  }
}

function toggleTheme() {
  uiStore.toggleTheme()
  showMorePanel.value = false
}

async function handleLogout() {
  showMorePanel.value = false
  await authStore.logout()
}

// Icon components
function DashboardIcon() {
  return h('svg', { width: '24', height: '24', viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
    h('path', { d: 'M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    h('path', { d: 'M9 22V12H15V22', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
  ])
}

function UsersIcon() {
  return h('svg', { width: '24', height: '24', viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
    h('path', { d: 'M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    h('path', { d: 'M9 11C11.2091 11 13 9.20914 13 7C13 4.79086 11.2091 3 9 3C6.79086 3 5 4.79086 5 7C5 9.20914 6.79086 11 9 11Z', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    h('path', { d: 'M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    h('path', { d: 'M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })
  ])
}

function StatsIcon() {
  return h('svg', { width: '24', height: '24', viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, [
