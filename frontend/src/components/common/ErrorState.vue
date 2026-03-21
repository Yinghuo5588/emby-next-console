<template>
 <div class="error-state" :class="{ compact }">
 <div class="error-icon">⚠</div>
 <p class="error-message">{{ message }}</p>
 <button v-if="onRetry" class="btn btn-ghost retry-btn" @click="onRetry">
 重试
 </button>
 </div>
</template>

<script setup lang="ts">
defineProps<{
 message: string
 compact?: boolean
 onRetry?: () => void
}>()
</script>

<style scoped>
.error-state {
 display: flex;
 flex-direction: column;
 align-items: center;
 justify-content: center;
 padding: 40px 20px;
 text-align: center;
}

.error-state.compact {
 padding: 20px;
}

.error-icon {
 font-size: 28px;
 margin-bottom: 12px;
 color: var(--color-danger);
}

.error-message {
 color: var(--color-text-muted);
 font-size: 13px;
 margin-bottom: 16px;
}

.error-state.compact .error-message {
 margin-bottom: 10px;
}

.retry-btn {
 padding: 6px 14px;
 font-size: 12px;
}
</style>