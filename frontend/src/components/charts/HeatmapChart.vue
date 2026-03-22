<template>
  <div class="heatmap-container">
    <canvas ref="canvasEl" :width="width" :height="height"></canvas>
    <div class="hm-legend">
      <span class="hm-legend-label">少</span>
      <div class="hm-legend-blocks">
        <span v-for="i in 5" :key="i" class="hm-block" :style="{ opacity: i * 0.2 }"></span>
      </div>
      <span class="hm-legend-label">多</span>
    </div>
    <div class="hm-labels-row">
      <span></span>
      <span v-for="d in weekDays" :key="d">{{ d }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps<{ data: number[][] }>() // 24 x 7

const canvasEl = ref<HTMLCanvasElement | null>(null)
const width = 320
const height = 200

const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const cellW = Math.floor((width - 40) / 7)
const cellH = Math.floor((height - 40) / 24)

function draw() {
  const canvas = canvasEl.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, width, height)

  // Find max
  let max = 0
  for (const row of props.data) for (const v of row) if (v > max) max = v
  if (max === 0) max = 1

  // Draw cells
  const offsetX = 30
  const offsetY = 5
  for (let h = 0; h < 24; h++) {
    // Hour label
    if (h % 3 === 0) {
      ctx.fillStyle = '#999'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(`${h}`, offsetX - 4, offsetY + h * cellH + cellH / 2 + 3)
    }
    for (let d = 0; d < 7; d++) {
      const val = props.data[h]?.[d] ?? 0
      const intensity = val / max
      const alpha = intensity === 0 ? 0.05 : 0.15 + intensity * 0.85
      ctx.fillStyle = `rgba(0, 122, 255, ${alpha})`
      ctx.fillRect(offsetX + d * cellW + 1, offsetY + h * cellH + 1, cellW - 2, cellH - 2)
    }
  }
}

onMounted(() => { nextTick(draw) })
watch(() => props.data, draw, { deep: true })
</script>

<style scoped>
.heatmap-container { position: relative; }
canvas { width: 100%; max-width: 320px; }
.hm-legend { display: flex; align-items: center; justify-content: flex-end; gap: 4px; margin-top: 4px; }
.hm-legend-label { font-size: 10px; color: var(--text-muted); }
.hm-legend-blocks { display: flex; gap: 2px; }
.hm-block { width: 12px; height: 12px; background: rgb(0, 122, 255); border-radius: 2px; }
.hm-labels-row { display: grid; grid-template-columns: 30px repeat(7, 1fr); font-size: 10px; color: var(--text-muted); text-align: center; margin-top: 4px; }
</style>