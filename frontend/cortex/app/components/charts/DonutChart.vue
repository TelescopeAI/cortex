<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'

interface DonutChartProps {
  data: number[]
  height?: number // Make height optional
  radius: number
  labels: Array<{ name: string; color: string }>
  type?: string
  hideLegend?: boolean
}

const props = withDefaults(defineProps<DonutChartProps>(), {
  type: 'donut',
  hideLegend: false
})

const { chartTheme } = useChartTheme()

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
  <div class="h-full w-full">
    <VChart 
      :option="chartOption" 
      :theme="chartTheme"
      autoresize
      class="h-full w-full min-h-[24rem]"
    />
  </div>
</template> 