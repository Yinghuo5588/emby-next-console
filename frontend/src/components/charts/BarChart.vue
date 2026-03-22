<template>
  <v-chart :option="chartOption" :autoresize="true" :style="{ width: '100%', height: height }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { useUiStore } from '@/stores/ui'

use([BarChart, CanvasRenderer, GridComponent, TooltipComponent])

const props = withDefaults(defineProps<{
  yData: string[]
  data: number[]
  horizontal?: boolean
  color?: string
  max?: number
  height?: string
  barColorStart?: string
  barColorEnd?: string
}>(), { height: '260px', horizontal: true, color: '#007AFF' })

const uiStore = useUiStore()

const chartOption = computed(() => {
  const colors = ['#007AFF', '#34C759', '#FF9500', '#AF52DE', '#5AC8FA', '#FF3B30', '#FF2D55', '#5856D6']
  const dataMax = props.max ?? Math.max(...props.data, 1)

  if (props.horizontal) {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
        borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
        textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
      },
      grid: { left: 4, right: 50, top: 8, bottom: 4, containLabel: true },
      xAxis: {
        type: 'value',
        show: false,
        max: dataMax,
      },
      yAxis: {
        type: 'category',
        data: props.yData.slice().reverse(),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: uiStore.isDark ? '#e5e5ea' : '#3c3c43',
          fontSize: 12,
          width: 120,
          overflow: 'truncate',
        },
      },
      series: [{
        type: 'bar',
        data: props.data.slice().reverse().map((v, i) => ({
          value: v,
          itemStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: colors[i % colors.length] + '90' },
                { offset: 1, color: colors[i % colors.length] },
              ],
            },
            borderRadius: [0, 6, 6, 0],
          },
        })),
        barWidth: 14,
        label: {
          show: true,
          position: 'right',
          color: uiStore.isDark ? '#8e8e93' : '#8e8e93',
          fontSize: 11,
          formatter: '{c}',
        },
      }],
    }
  }

  // Vertical bars
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
      textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
    },
    grid: { left: 40, right: 12, top: 16, bottom: 4 },
    xAxis: {
      type: 'category',
      data: props.yData,
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
    series: [{
      type: 'bar',
      data: props.data.map(v => ({
        value: v,
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: props.color },
              { offset: 1, color: props.color + '60' },
            ],
          },
          borderRadius: [6, 6, 0, 0],
        },
      })),
      barWidth: 20,
    }],
  }
})
</script>
