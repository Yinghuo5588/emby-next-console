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
  // data is grid[dow][hour] = 7×24, ECharts heatmap [x,y,val] maps to [col,row,val]
  // xAxis = 24小时 (cols), yAxis = 7天 (rows)
  // 所以 xIndex = hour, yIndex = dow; invert yAxis 让周一在上方
  const heatData: [number, number, number][] = []
  const grid = props.data
  let maxVal = 0
  for (let dow = 0; dow < 7; dow++) {
    for (let hour = 0; hour < 24; hour++) {
      const val = grid[dow]?.[hour] ?? 0
      heatData.push([hour, dow, val])  // x=hour(0-23), y=dow(0-6)
      if (val > maxVal) maxVal = val
    }
  }
  maxVal = Math.max(maxVal, 1)
  // 颜色梯度起点不用接近背景的深色，改用「低值也清晰可见」的配色
  // maxVal 较小时（如1-3），颜色仍保持可辨识

  return {
    tooltip: {
      ...chartTooltipStyle(uiStore.isDark),
      formatter: (p: any) => {
        const hour = p.data[0]  // x轴：小时（0-23）
        const dow = p.data[1]   // y轴：星期（0-6）
        const val = p.data[2]
        return `${defaultYLabels[dow]} ${String(hour).padStart(2, '0')}:00<br/>播放 <b>${val}</b> 次`
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
      inverse: true,  // dow=0（周一）在上方
    },
    visualMap: {
      show: false,
      min: 0,
      max: Math.max(maxVal, 3),   // 保证至少有3档，低值也清晰
      inRange: {
        color: uiStore.isDark
          ? ['#1e3a5f', '#0066CC', '#00AA55', '#FFCC00', '#FF3333']
          : ['#dce8f5', '#007AFF', '#34C759', '#FF9500', '#FF3B30'],
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
