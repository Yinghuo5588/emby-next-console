<template>
  <div class="stats-tabs">
    <router-link
      v-for="tab in tabs"
      :key="tab.key"
      :to="tab.path"
      class="stats-tab"
      :class="{ active: isActive(tab.path) }"
    >
      <span class="tab-label">{{ tab.label }}</span>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const tabs = [
  { key: 'overview', label: '总览', path: '/stats' },
  { key: 'content', label: '内容', path: '/stats/content' },
  { key: 'users', label: '用户', path: '/stats/users' },
]

function isActive(path: string) {
  return route.path === path
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
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  transition: all 0.2s;
  font-family: inherit;
}
.stats-tab.active {
  background: var(--surface);
  color: var(--text);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
</style>
