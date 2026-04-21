import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const isDark = ref(false)
  const isMobile = ref(false)

  function init() {
    isMobile.value = window.innerWidth < 768
    window.addEventListener('resize', () => {
      isMobile.value = window.innerWidth < 768
    })
    const saved = localStorage.getItem('theme')
    isDark.value = saved === 'dark'
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : '')
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : '')
  }

  return { isDark, isMobile, init, toggleTheme }
})
