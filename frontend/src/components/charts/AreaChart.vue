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

const colors = ['#007AFF', '#34C759', '#FF9500', '#AF52DE', '#5AC8FA']

const chartOption = computed(() => ({
  color: colors,
  tooltip: {
    trigger: 'axis',
    backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
    borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
    textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
    axisPointer: { type: 'cross', crossStyle: { color: uiStore.isDark ? '#48484a' : '#c7c7cc' } },
  },
  legend: {
    show: props.series.length > 1,
    bottom: 0,
    textStyle: { color: uiStore.isDark ? '#8e8e93' : '#8e8e93', fontSize: 12 },
    icon: 'roundRect',
    itemWidth: 16, itemHeight: 4,
  },
  grid: { left: 40, right: 12, top: 16, bottom: props.series.length > 1 ? 36 : 8 },
  xAxis: {
    type: 'category',
    data: props.xData,
    boundaryGap: false,
    axisLine: { lineStyle: { color: uiStore.isDark ? '#48484a' : '#e5e5ea' } },
    axisTick: { show: false },
    axisLabel: { color: uiStore.isDark ? '#8e8e93' : '#8e8e93', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: uiStore.isDark ? '#2c2c2e' : '#f2f2f7', type: 'dashed' } },
    axisLabel: { color: uiStore.isDark ? '#8e8e93' : '#8e8e93', fontSize: 11 },
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
          { offset: 0, color: (s.color || colors[i]) + '30' },
          { offset: 1, color: (s.color || colors[i]) + '05' },
        ],
      },
    } : undefined,
  })),
}))
</script>
