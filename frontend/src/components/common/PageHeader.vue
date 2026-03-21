<template>
  <div class="page-header">
    <div class="header-content">
      <div class="header-text">
        <h1 class="title">{{ title }}</h1>
        <p v-if="desc" class="desc">{{ desc }}</p>
      </div>
      <div v-if="$slots.actions" class="header-actions">
        <slot name="actions" />
      </div>
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
.page-header {
  background: var(--surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.header-text {
  flex: 1;
}

.title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.5rem 0;
  line-height: 1.2;
}

.desc {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Responsive */
@media (max-width: 767px) {
  .page-header {
    padding: 1.25rem;
    border-radius: 12px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .title {
    font-size: 1.5rem;
  }
  
  .header-actions {
    justify-content: flex-start;
  }
}
</style>