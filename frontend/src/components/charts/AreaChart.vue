<template>
  <v-chart :option="chartOption" :autoresize="true" :style="{ width: '100%', height: height }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { useUiStore } from '@/stores/ui'
import { chartColors, chartTextStyle, chartMutedStyle, chartTooltipStyle, chartGridStyle, chartSplitLineStyle, chartAxisLineStyle } from './theme'

use([LineChart, CanvasRenderer, GridComponent, TooltipComponent, LegendComponent])

const props = withDefaults(defineProps<{
  xData: string[]
  series: { name: string; data: number[]; color?: string }[]
  title?: string
  height?: string
  area?: boolean
  smooth?: boolean
}>(), { height: '280px', area: true, smooth: true })

const uiStore = useUiStore()

const chartOption = computed(() => ({
  color: chartColors,
  tooltip: {
    trigger: 'axis',
    ...chartTooltipStyle(uiStore.isDark),
    axisPointer: { type: 'cross', crossStyle: { color: uiStore.isDark ? '#48484a' : '#c7c7cc' } },
  },
  legend: {
    show: props.series.length > 1,
    bottom: 0,
    textStyle: { ...chartMutedStyle(), fontSize: 12 },
    icon: 'roundRect',
    itemWidth: 16, itemHeight: 4,
  },
  grid: { ...chartGridStyle(), bottom: props.series.length > 1 ? 36 : 8 },
  xAxis: {
    type: 'category',
    data: props.xData,
    boundaryGap: false,
    axisLine: { lineStyle: chartAxisLineStyle(uiStore.isDark) },
    axisTick: { show: false },
    axisLabel: chartMutedStyle(),
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: chartSplitLineStyle(uiStore.isDark) },
    axisLabel: chartMutedStyle(),
  },
  series: props.series.map((s, i) => ({
    name: s.name,
    type: 'line',
    data: s.data,
    smooth: props.smooth,
    symbol: 'circle',
    symbolSize: 4,
    lineStyle: { width: 2.5 },
    areaStyle: props.area ? {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: (s.color || chartColors[i]) + '30' },
          { offset: 1, color: (s.color || chartColors[i]) + '05' },
        ],
      },
    } : undefined,
  })),
}))
</script>
