<template>
  <div class="error-state" :class="{ compact }">
    <div class="error-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" 
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="error-content">
      <h3 class="error-title">Something went wrong</h3>
      <p class="error-message">{{ message }}</p>
      <button class="retry-button" @click="$emit('retry')">
        <span>Try Again</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 4V9H4.58152M19.9381 11C19.446 7.05369 16.0796 4 12 4C8.64262 4 5.76829 6.06817 4.58152 9M4.58152 9H9M20 20V15H19.4185M19.4185 15C18.2317 17.9318 15.3574 20 12 20C7.92038 20 4.55399 16.9463 4.06189 13M19.4185 15H15" 
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string
  compact?: boolean
}>()

defineEmits<{
  retry: []
}>()
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 2rem;
  width: 100%;
  min-height: 300px;
}

.error-state.compact {
  padding: 2rem 1rem;
  min-height: 200px;
}

.error-icon {
  color: var(--danger);
  margin-bottom: 1.5rem;
}

.error-state.compact .error-icon {
  margin-bottom: 1rem;
}

.error-state.compact .error-icon svg {
  width: 32px;
  height: 32px;
}

.error-content {
  max-width: 400px;
}

.error-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.75rem 0;
}

.error-state.compact .error-title {
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
}

.error-message {
  font-size: 0.95rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0 0 1.5rem 0;
}

.error-state.compact .error-message {
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.retry-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: var(--brand);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-button:hover {
  background: var(--brand-dark);
  transform: translateY(-1px);
}

.retry-button:active {
  transform: translateY(0);
}

.error-state.compact .retry-button {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  border-radius: 10px;
}
</style>