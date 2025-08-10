<script setup lang="ts">
import { computed } from 'vue'

interface BulletLegendItemInterface {
  name: string
  color: string
}

interface LineChartProps {
  data: Record<string, any>[]
  height: number
  categories: Record<string, BulletLegendItemInterface>
  xFormatter: (i: number, idx?: number) => string | number
  yLabel?: string
  xNumTicks?: number
  yNumTicks?: number
  curveType?: string
  legendPosition?: string
  hideLegend?: boolean
  yGridLine?: boolean
}

const props = withDefaults(defineProps<LineChartProps>(), {
  yLabel: '',
  xNumTicks: 5,
  yNumTicks: 4,
  curveType: 'linear',
  legendPosition: 'top',
  hideLegend: false,
  yGridLine: true
})

// Convert data to ECharts format
const chartOption = computed(() => {
  const xAxisData = props.data.map((_, index) => props.xFormatter(index))
  
  const series = Object.keys(props.categories).map(key => {
    const categoryInfo = props.categories[key]
    return {
      name: categoryInfo?.name || key,
      type: 'line',
      data: props.data.map(item => item[key]),
      smooth: props.curveType === 'smooth',
      itemStyle: {
        color: categoryInfo?.color || '#3b82f6'
      },
      lineStyle: {
        color: categoryInfo?.color || '#3b82f6'
      }
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      show: !props.hideLegend,
      [props.legendPosition]: 10,
      data: series.map(s => s.name)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.hideLegend ? '3%' : '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: props.yLabel,
      splitLine: {
        show: props.yGridLine
      }
    },
    series: series
  }
})
</script>

<template>
  <VChart 
    :option="chartOption" 
    :style="{ height: `${height}px` }"
    autoresize
  />
</template> 