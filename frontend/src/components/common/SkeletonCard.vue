<template>
  <div class="skeleton-card" :style="{ height, borderRadius: radius }">
    <div v-if="lines > 0" class="skel-lines">
      <div v-for="i in lines" :key="i" class="skel-line" :style="{ width: lineWidths[(i - 1) % lineWidths.length] }" />
    </div>
    <div v-if="block" class="skel-block" :style="{ height: blockHeight }" />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  lines?: number
  block?: boolean
  blockHeight?: string
  height?: string
  radius?: string
}>(), {
  lines: 2,
  block: false,
  blockHeight: '120px',
  height: 'auto',
  radius: '16px',
})

const lineWidths = ['60%', '40%', '80%', '50%']
</script>

<style scoped>
.skeleton-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 1.1rem;
  overflow: hidden;
}
.skel-lines {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}
.skel-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.skel-block {
  border-radius: 12px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
