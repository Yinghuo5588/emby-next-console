<template>
  <div ref="chartEl" :style="{ height, width: '100%' }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = withDefaults(defineProps<{
  xData: string[]
  series: { name: string; data: number[]; color?: string }[]
  height?: string
}>(), { height: '220px' })

const COLORS = ['#007aff', '#34c759', '#ff9500', '#5856d6']
const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let ro: ResizeObserver | null = null

function buildOption() {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'var(--surface)', borderColor: 'var(--border)', textStyle: { color: 'var(--text)', fontSize: 12 } },
    legend: { right: 0, top: 0, textStyle: { color: 'var(--text-muted)', fontSize: 12 }, itemWidth: 12, itemHeight: 6 },
    grid: { left: 0, right: 8, top: 32, bottom: 0, containLabel: true },
    xAxis: { type: 'category', data: props.xData, boundaryGap: false, axisLine: { lineStyle: { color: 'var(--border)' } }, axisTick: { show: false }, axisLabel: { color: 'var(--text-muted)', fontSize: 11 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border)', type: 'dashed' } }, axisLabel: { color: 'var(--text-muted)', fontSize: 11 }, minInterval: 1 },
    series: props.series.map((s, i) => {
      const color = s.color ?? COLORS[i % COLORS.length]
      return { name: s.name, type: 'line', data: s.data, smooth: 0.3, symbol: 'circle', symbolSize: 4, lineStyle: { color, width: 2 }, itemStyle: { color }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: color + '30' }, { offset: 1, color: color + '00' }]) } }
    }),
  }
}

onMounted(() => {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value)
  chart.setOption(buildOption())
  ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartEl.value)
})

onBeforeUnmount(() => { ro?.disconnect(); chart?.dispose() })
watch(() => [props.xData, props.series], () => chart?.setOption(buildOption(), { notMerge: false }), { deep: true })
</script>
