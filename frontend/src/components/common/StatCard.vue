<template>
 <div class="stat-card card" :class="{ highlight, danger }">
 <div class="stat-label">{{ label }}</div>
 <div class="stat-value">{{ value }}</div>
 <div v-if="sub" class="stat-sub">{{ sub }}</div>
 </div>
</template>

<script setup lang="ts">
defineProps<{
 label: string
 value: string | number
 sub?: string
 highlight?: boolean
 danger?: boolean
}>()
</script>

<style scoped>
.stat-card {
 display: flex;
 flex-direction: column;
 gap: 8px;
 transition: border-color 0.2s;
}

.stat-card.highlight {
 border-color: rgba(99, 102, 241, 0.4);
 background: rgba(99, 102, 241, 0.04);
}

.stat-card.danger {
 border-color: rgba(239, 68, 68, 0.4);
 background: rgba(239, 68, 68, 0.04);
}

.stat-label {
 font-size: 12px;
 color: var(--color-text-muted);
}

.stat-value {
 font-size: 28px;
 font-weight: 700;
 line-height: 1.1;
 color: var(--color-text);
}

.stat-sub {
 font-size: 12px;
 color: var(--color-text-muted);
}
</style>