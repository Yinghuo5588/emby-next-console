<template>
 <header class="header">
 <button class="toggle-btn" @click="ui.toggleSidebar()">☰</button>
 <span class="title">{{ route.meta.title ?? '' }}</span>
 <div class="header-right">
 <span class="user-info">{{ auth.user?.username }}</span>
 <span class="role-tag tag tag-purple">{{ auth.user?.role }}</span>
 </div>
 </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const route = useRoute()
const auth = useAuthStore()
const ui = useUiStore()
</script>

<style scoped>
.header {
 height: var(--header-height);
 background: var(--color-surface);
 border-bottom: 1px solid var(--color-border);
 display: flex;
 align-items: center;
 gap: 14px;
 padding: 0 20px;
 position: sticky;
 top: 0;
 z-index: 10;
}
.toggle-btn { color: var(--color-text-muted); font-size: 18px; padding: 4px 6px; }
.toggle-btn:hover { color: var(--color-text); }
.title { font-weight: 600; font-size: 15px; }
.header-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.user-info { color: var(--color-text-muted); }
</style>