<template>
  <v-chart :option="chartOption" :autoresize="true" :style="{ width: '100%', height: height }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { useUiStore } from '@/stores/ui'

use([HeatmapChart, CanvasRenderer, GridComponent, TooltipComponent, VisualMapComponent])

const props = withDefaults(defineProps<{
  data: number[][]
  xLabels?: string[]
  yLabels?: string[]
  height?: string
}>(), { height: '300px' })

const uiStore = useUiStore()

const defaultXLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`)
const defaultYLabels = ['一', '二', '三', '四', '五', '六', '日']

const chartOption = computed(() => {
  // data is grid[hour][dow], convert to [dow, hour, value] for ECharts
  const heatData: [number, number, number][] = []
  const grid = props.data
  let maxVal = 0
  for (let hour = 0; hour < 24; hour++) {
    for (let dow = 0; dow < 7; dow++) {
      const val = grid[hour]?.[dow] ?? 0
      heatData.push([hour, dow, val])
      if (val > maxVal) maxVal = val
    }
  }
  maxVal = Math.max(maxVal, 1)

  return {
    tooltip: {
      backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
      textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
      formatter: (p: any) => {
        const hour = p.data[0]
        const dow = p.data[1]
        const val = p.data[2]
        return `${defaultYLabels[dow]} ${hour}:00<br/>播放 <b>${val}</b> 次`
      },
    },
    grid: { left: 36, right: 16, top: 8, bottom: 28 },
    xAxis: {
      type: 'category',
      data: props.xLabels || defaultXLabels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: uiStore.isDark ? '#8e8e93' : '#8e8e93',
        fontSize: 10,
        interval: 3,
      },
      splitArea: { show: false },
    },
    yAxis: {
      type: 'category',
      data: props.yLabels || defaultYLabels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: uiStore.isDark ? '#8e8e93' : '#8e8e93', fontSize: 11 },
      splitArea: { show: false },
    },
    visualMap: { show: false, min: 0, max: maxVal },
    series: [{
      type: 'heatmap',
      data: heatData,
      itemStyle: { borderRadius: 3 },
      emphasis: {
        itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.2)' },
      },
      color: uiStore.isDark
        ? ['#000', '#0A84FF', '#34C759', '#FF9F0A', '#FF453A']
        : ['#f2f2f7', '#007AFF', '#34C759', '#FF9500', '#FF3B30'],
      itemStyle: { borderRadius: 4, borderWidth: 1, borderColor: uiStore.isDark ? '#1c1c1e' : '#fff' },
    }],
  }
})
</script>
