<template>
  <n-result status="error" title="出错了" :description="message">
    <template #footer>
      <n-button type="primary" @click="$emit('retry')">重试</n-button>
    </template>
  </n-result>
</template>

<script setup lang="ts">
defineProps<{
  message: string
  compact?: boolean
}>()

defineEmits<{
  retry: []
}>()
</script>
