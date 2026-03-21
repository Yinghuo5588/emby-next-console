import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

type Theme = 'light' | 'dark'

export const useUiStore = defineStore('ui', () => {
  // State
  const theme = ref<Theme>((localStorage.getItem('theme') as Theme) || 'light')
  const sidebarOpen = ref(true)
  const isMobile = ref(false)

  // Computed
  const isDark = computed(() => theme.value === 'dark')

  // Actions
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
  }

  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
  }

  const openSidebar = () => {
    sidebarOpen.value = true
  }

  const closeSidebar = () => {
    sidebarOpen.value = false
  }

  const checkMobile = () => {
    isMobile.value = window.innerWidth < 768
    if (isMobile.value) {
      sidebarOpen.value = false
    }
  }

  // Watch theme changes and update localStorage
  watch(theme, (newTheme) => {
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }, { immediate: true })

  // Initialize
  const init = () => {
    checkMobile()
    window.addEventListener('resize', checkMobile)
    
    // Set initial theme on document
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  // Cleanup
  const cleanup = () => {
    window.removeEventListener('resize', checkMobile)
  }

  return {
    // State
    theme,
    sidebarOpen,
    isMobile,
    
    // Computed
    isDark,
    
    // Actions
    toggleTheme,
    setTheme,
    toggleSidebar,
    openSidebar,
    closeSidebar,
    checkMobile,
    init,
    cleanup,
  }
})