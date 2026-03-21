<template>
  <div class="empty-state">
    <div class="empty-icon">
      <slot name="icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3 7V5C3 3.89543 3.89543 3 5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V17M12 12C13.6569 12 15 10.6569 15 9C15 7.34315 13.6569 6 12 6C10.3431 6 9 7.34315 9 9C9 10.6569 10.3431 12 12 12ZM12 12C9.79086 12 8 13.7909 8 16V17H16V16C16 13.7909 14.2091 12 12 12Z" 
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </slot>
    </div>
    <div class="empty-content">
      <h3 class="empty-title">{{ title }}</h3>
      <p v-if="desc" class="empty-desc">{{ desc }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  desc?: string
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4rem 2rem;
  width: 100%;
  min-height: 400px;
}

.empty-icon {
  color: var(--text-muted);
  opacity: 0.5;
  margin-bottom: 2rem;
}

.empty-icon svg {
  stroke-width: 1.5;
}

.empty-content {
  max-width: 400px;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 1rem 0;
}

.empty-desc {
  font-size: 1rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

/* Responsive */
@media (max-width: 767px) {
  .empty-state {
    padding: 3rem 1.5rem;
    min-height: 300px;
  }
  
  .empty-icon {
    margin-bottom: 1.5rem;
  }
  
  .empty-icon svg {
    width: 48px;
    height: 48px;
  }
  
  .empty-title {
    font-size: 1.25rem;
  }
  
  .empty-desc {
    font-size: 0.95rem;
  }
}
</style>