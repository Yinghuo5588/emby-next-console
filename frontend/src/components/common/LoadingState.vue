<template>
 <div class="loading-state" :style="{ height }">
 <div class="spinner" />
 <p v-if="text" class="loading-text">{{ text }}</p>
 </div>
</template>

<script setup lang="ts">
defineProps<{
 height?: string
 text?: string
}>()
</script>

<style scoped>
.loading-state {
 display: flex;
 flex-direction: column;
 align-items: center;
 justify-content: center;
 background: var(--color-surface-2);
 border-radius: 8px;
}

.spinner {
 width: 32px;
 height: 32px;
 border: 3px solid var(--color-border);
 border-top-color: var(--color-primary);
 border-radius: 50%;
 animation: spin 0.8s linear infinite;
}

@keyframes spin {
 to { transform: rotate(360deg); }
}

.loading-text {
 margin-top: 10px;
 color: var(--color-text-muted);
 font-size: 13px;
}
</style>