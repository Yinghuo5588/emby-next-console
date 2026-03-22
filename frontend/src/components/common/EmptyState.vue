<template>
  <n-empty :description="title" size="large">
    <template #icon>
      <slot name="icon" />
    </template>
    <template v-if="desc" #extra>
      <p class="empty-desc">{{ desc }}</p>
    </template>
  </n-empty>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  desc?: string
}>()
</script>

<style scoped>
.empty-desc { font-size: 0.95rem; color: var(--text-muted); line-height: 1.5; margin: 0; }
</style>
