<template>
 <div class="page-header">
 <div class="ph-left">
 <h1 class="ph-title">{{ title }}</h1>
 <p v-if="desc" class="ph-desc">{{ desc }}</p>
 </div>
 <div v-if="$slots.actions" class="ph-actions">
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
 align-items: flex-start;
 justify-content: space-between;
 margin-bottom: 24px;
}

.ph-left {
 flex: 1;
 min-width: 0;
}

.ph-title {
 font-size: 20px;
 font-weight: 700;
 color: var(--color-text);
 margin-bottom: 4px;
}

.ph-desc {
 font-size: 13px;
 color: var(--color-text-muted);
}

.ph-actions {
 display: flex;
 gap: 8px;
 flex-shrink: 0;
}
</style>