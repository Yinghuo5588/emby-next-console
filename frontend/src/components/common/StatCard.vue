<template>
  <div class="stat-card" :class="{ highlight, danger }">
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value" :style="{ color: danger ? 'var(--danger)' : highlight ? 'var(--brand)' : undefined }">
      {{ formattedValue }}
    </div>
    <div v-if="sub" class="stat-sub">{{ sub }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: string | number
  sub?: string
  highlight?: boolean
  danger?: boolean
}>()

const formattedValue = computed(() => {
  if (typeof props.value === 'number') return props.value.toLocaleString()
  return props.value
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  transition: all 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.stat-card.highlight { border-left: 3px solid var(--brand); }
.stat-card.danger { border-left: 3px solid var(--danger); }
.stat-label { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-value { font-size: 1.75rem; font-weight: 700; color: var(--text); line-height: 1; margin-bottom: 0.25rem; }
.stat-sub { font-size: 0.8rem; color: var(--text-muted); }
</style>
