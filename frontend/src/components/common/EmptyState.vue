<template>
 <div class="empty-state">
 <div class="empty-icon">{{ icon }}</div>
 <div class="empty-title">{{ title }}</div>
 <div v-if="desc" class="empty-desc">{{ desc }}</div>
 <slot />
 </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
 icon?: string
 title: string
 desc?: string
}>(), {
 icon: '◎',
})
</script>

<style scoped>
.empty-state {
 display: flex;
 flex-direction: column;
 align-items: center;
 padding: 48px 24px;
 text-align: center;
 color: var(--color-text-muted);
}

.empty-icon {
 font-size: 36px;
 margin-bottom: 14px;
 opacity: 0.4;
}

.empty-title {
 font-size: 15px;
 font-weight: 500;
 color: var(--color-text-muted);
 margin-bottom: 6px;
}

.empty-desc {
 font-size: 13px;
 opacity: 0.8;
}
</style>