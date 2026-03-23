<template>
  <div class="stats-tabs">
    <div
      v-for="tab in tabs"
      :key="tab.key"
      class="stats-tab"
      :class="{ active: isActive(tab.path) }"
      @click="handleClick(tab)"
    >
      <span class="tab-label">{{ tab.label }}</span>
      <span v-if="tab.hasFilter && isActive(tab.path)" class="tab-filter-icon" :class="{ 'filter-active': filterActive }">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="7" y1="12" x2="17" y2="12"/><line x1="10" y1="18" x2="14" y2="18"/></svg>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const props = defineProps<{
  filterActive?: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle-filter'): void
}>()

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: 'overview', label: '总览', path: '/stats' },
  { key: 'content', label: '内容', path: '/stats/content', hasFilter: true },
  { key: 'users', label: '用户', path: '/stats/users' },
]

function isActive(path: string) {
  return route.path === path
}

function handleClick(tab: any) {
  if (isActive(tab.path) && tab.hasFilter) {
    emit('toggle-filter')
  } else {
    router.push(tab.path)
  }
}
</script>

<style scoped>
.stats-tabs {
  display: flex;
  gap: 0;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: 3px;
  margin-bottom: 1rem;
}
.stats-tab {
  flex: 1;
  text-align: center;
  padding: 0.5rem 0.25rem;
  border-radius: var(--radius);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.2s;
  cursor: pointer;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  user-select: none;
}
.stats-tab.active {
  background: var(--surface);
  color: var(--text);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.tab-filter-icon {
  opacity: 0.4;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
}
.tab-filter-icon.filter-active {
  opacity: 1;
  color: var(--brand);
}
.stats-tab:hover .tab-filter-icon {
  opacity: 0.7;
}
</style>
