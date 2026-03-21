<template>
  <div class="stat-card" :class="{ highlight, danger }">
    <div class="stat-content">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ formattedValue }}</div>
      <div v-if="sub" class="stat-sub">{{ sub }}</div>
    </div>
    <div v-if="highlight || danger" class="stat-indicator"></div>
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
  if (typeof props.value === 'number') {
    // Format large numbers with commas
    return props.value.toLocaleString()
  }
  return props.value
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-card.highlight {
  border-color: var(--brand);
}

.stat-card.danger {
  border-color: var(--danger);
}

.stat-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--brand);
  border-radius: 16px 16px 0 0;
}

.stat-card.danger .stat-indicator {
  background: var(--danger);
}

.stat-content {
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-card.highlight .stat-value {
  color: var(--brand);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

.stat-sub {
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Responsive */
@media (max-width: 767px) {
  .stat-card {
    padding: 1.25rem;
    border-radius: 12px;
  }
  
  .stat-value {
    font-size: 1.75rem;
  }
}
</style>