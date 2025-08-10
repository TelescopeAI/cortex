<script setup lang="ts">
import { computed } from 'vue'

interface DonutChartProps {
  data: number[]
  height: number
  radius: number
  labels: Array<{ name: string; color: string }>
  type?: string
  hideLegend?: boolean
}

const props = withDefaults(defineProps<DonutChartProps>(), {
  type: 'donut',
  hideLegend: false
})

// Convert data to ECharts format
const chartOption = computed(() => {
  const pieData = props.data.map((value, index) => ({
    name: props.labels[index]?.name || `Item ${index + 1}`,
    value: value,
    itemStyle: {
      color: props.labels[index]?.color || '#3b82f6'
    }
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      show: !props.hideLegend,
      orient: 'vertical',
      right: 10,
      top: 'center',
      data: props.labels.map(label => label.name)
    },
    series: [
      {
        name: 'Data',
        type: 'pie',
        radius: ['40%', `${props.radius}%`],
        center: ['40%', '50%'],
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
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