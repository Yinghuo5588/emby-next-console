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
import { chartTextStyle, chartMutedStyle, chartTooltipStyle } from './theme'

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
  // data is grid[dow][hour], convert to [dow, hour, value] for ECharts
  const heatData: [number, number, number][] = []
  const grid = props.data
  let maxVal = 0
  for (let hour = 0; hour < 24; hour++) {
    for (let dow = 0; dow < 7; dow++) {
      const val = grid[dow]?.[hour] ?? 0
      heatData.push([dow, hour, val])
      if (val > maxVal) maxVal = val
    }
  }
  maxVal = Math.max(maxVal, 1)

  return {
    tooltip: {
      ...chartTooltipStyle(uiStore.isDark),
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
      axisLabel: { ...chartMutedStyle(), fontSize: 10, interval: 3 },
      splitArea: { show: false },
    },
    yAxis: {
      type: 'category',
      data: props.yLabels || defaultYLabels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: chartMutedStyle(),
      splitArea: { show: false },
    },
    visualMap: {
      show: false,
      min: 0,
      max: maxVal,
      inRange: {
        color: uiStore.isDark
          ? ['#1c1c1e', '#0A84FF', '#34C759', '#FF9F0A', '#FF453A']
          : ['#f2f2f7', '#007AFF', '#34C759', '#FF9500', '#FF3B30'],
      },
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      itemStyle: { borderRadius: 4, borderWidth: 1, borderColor: uiStore.isDark ? '#1c1c1e' : '#fff' },
      emphasis: {
        itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.2)' },
      },
    }],
  }
})
</script>
