<template>
  <div class="ios-card-title">
    <IosIcon v-if="icon" :name="icon" :size="18" :color="iconColor || 'var(--brand)'" :stroke-width="1.8" />
    <span class="title-text">{{ title }}</span>
  </div>
</template>

<script setup lang="ts">
import IosIcon from './IosIcon.vue'

defineProps<{
  title: string
  icon?: string
  iconColor?: string
}>()
</script>

<style scoped>
.ios-card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}
.title-text {
  line-height: 1;
}
</style>
