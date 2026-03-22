<template>
  <div class="page-header">
    <div class="header-text">
      <h1 class="title">{{ title }}</h1>
      <p v-if="desc" class="desc">{{ desc }}</p>
    </div>
    <div v-if="$slots.actions" class="header-actions">
      <slot name="actions" />
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.header-text { flex: 1; }
.title { font-size: 1.5rem; font-weight: 600; color: var(--text); margin: 0; }
.desc { font-size: 0.9rem; color: var(--text-muted); margin: 0.25rem 0 0; }
.header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
@media (max-width: 767px) {
  .page-header { flex-direction: column; align-items: stretch; }
  .title { font-size: 1.25rem; }
}
</style>
