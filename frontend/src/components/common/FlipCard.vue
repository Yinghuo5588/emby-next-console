<template>
  <div class="flip-card" :class="{ flipped: isFlipped }" @click="isFlipped = !isFlipped">
    <div class="flip-inner">
      <div class="flip-front">
        <div class="flip-hint" v-if="showHint">点击翻转</div>
        <slot name="front" />
      </div>
      <div class="flip-back">
        <div class="flip-hint">点击翻回</div>
        <slot name="back" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

withDefaults(defineProps<{
  showHint?: boolean
}>(), {
  showHint: true,
})

const isFlipped = ref(false)
</script>

<style scoped>
.flip-card {
  perspective: 800px;
  cursor: pointer;
  margin-bottom: 1rem;
}
.flip-inner {
  position: relative;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}
.flip-card.flipped .flip-inner {
  transform: rotateY(180deg);
}
.flip-front, .flip-back {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}
.flip-back {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  transform: rotateY(180deg);
}
.flip-hint {
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 0.65rem;
  color: var(--text-muted);
  opacity: 0.4;
  z-index: 1;
  pointer-events: none;
}
</style>
