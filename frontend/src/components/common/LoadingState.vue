<template>
  <div class="loading-state" :class="{ compact }" :style="{ height: height }">
    <div class="loading-spinner">
      <div class="spinner"></div>
      <div v-if="!compact" class="loading-text">Loading...</div>
    </div>
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
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
}

.loading-state.compact {
  min-height: 100px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid var(--border);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-state.compact .spinner {
  width: 32px;
  height: 32px;
  border-width: 2px;
}

.loading-text {
  font-size: 0.95rem;
  color: var(--text-muted);
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>