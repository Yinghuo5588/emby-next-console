<template>
  <v-chart :option="chartOption" :autoresize="true" :style="{ width: '100%', height: height }" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { useUiStore } from '@/stores/ui'

use([PieChart, CanvasRenderer, TooltipComponent, LegendComponent])

const props = withDefaults(defineProps<{
  data: { name: string; value: number }[]
  title?: string
  height?: string
  colors?: string[]
}>(), { height: '260px' })

const uiStore = useUiStore()

const defaultColors = [
  '#007AFF', '#34C759', '#FF9500', '#FF3B30', '#AF52DE',
  '#5AC8FA', '#FF2D55', '#5856D6',
]

const chartOption = computed(() => ({
  color: props.colors || defaultColors,
  tooltip: {
    trigger: 'item',
    backgroundColor: uiStore.isDark ? 'rgba(44,44,46,0.95)' : 'rgba(255,255,255,0.95)',
    borderColor: uiStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)',
    textStyle: { color: uiStore.isDark ? '#fff' : '#000', fontSize: 13 },
    formatter: '{b}: {c} ({d}%)',
  },
  series: [{
    type: 'pie',
    radius: ['45%', '72%'],
    center: ['50%', '50%'],
    avoidLabelOverlap: true,
    itemStyle: { borderRadius: 6, borderColor: uiStore.isDark ? '#1c1c1e' : '#fff', borderWidth: 2 },
    label: { show: true, fontSize: 12, color: uiStore.isDark ? '#e5e5ea' : '#3c3c43', formatter: '{b}\n{d}%' },
    labelLine: { length: 8, length2: 12 },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold' },
      itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.15)' },
    },
    data: props.data,
  }],
}))
</script>
