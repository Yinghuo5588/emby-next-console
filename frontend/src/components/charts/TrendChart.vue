<template>
 <div class="trend-chart" ref="chartEl" :style="{ height }" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

interface Series {
 name: string
 data: number[]
 color?: string
}

const props = withDefaults(defineProps<{
 xData: string[]
 series: Series[]
 height?: string
}>(), { height: '220px' })

const chartEl = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function initChart() {
 if (!chartEl.value) return
 chart = echarts.init(chartEl.value)
 updateOptions()
}

function updateOptions() {
 if (!chart) return
 const option: echarts.EChartsOption = {
 backgroundColor: 'transparent',
 tooltip: { trigger: 'axis' },
 legend: {
 data: props.series.map(s => s.name),
 textStyle: { color: '#8892a4' },
 bottom: 0,
 },
 grid: {
 left: 36,
 right: 16,
 top: 16,
 bottom: 36,
 containLabel: true,
 },
 xAxis: {
 type: 'category',
 data: props.xData,
 axisLine: { lineStyle: { color: '#2e3246' } },
 axisLabel: { color: '#8892a4', fontSize: 11 },
 },
 yAxis: {
 type: 'value',
 splitLine: { lineStyle: { color: '#2e3246' } },
 axisLabel: { color: '#8892a4', fontSize: 11 },
 },
 series: props.series.map(s => ({
 name: s.name,
 type: 'line',
 data: s.data,
 smooth: true,
 symbol: 'circle',
 symbolSize: 4,
 itemStyle: { color: s.color || '#6366f1' },
 })),
 }
 chart.setOption(option)
}

watch(() => [props.xData, props.series], updateOptions, { deep: true })

onMounted(() => {
 initChart()
 window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
 chart?.dispose()
})
</script>

<style scoped>
.trend-chart {
 width: 100%;
}
</style>