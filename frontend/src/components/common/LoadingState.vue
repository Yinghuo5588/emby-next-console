<template>
  <div class="loading-state" :class="{ compact }" :style="{ height }">
    <n-spin :size="compact ? 'small' : 'medium'" />
    <div v-if="!compact" class="loading-text">Loading...</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  height?: string
  compact?: boolean
}>()
</script>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
  gap: 1rem;
}
.loading-state.compact { min-height: 100px; }
.loading-text { font-size: 0.95rem; color: var(--text-muted); font-weight: 500; }
</style>
