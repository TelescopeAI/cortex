<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'
import { getShadcnTooltipConfig } from '~/config/echartShadCNTooltip'

interface DonutChartProps {
  data: number[]
  height?: number
  radius: number
  labels: Array<{ name: string; color?: string }>
  type?: string
  hideLegend?: boolean
  hideToolbar?: boolean
  legendPosition?: string
}

const props = withDefaults(defineProps<DonutChartProps>(), {
  type: 'donut',
  hideLegend: false,
  hideToolbar: true,
  legendPosition: 'right'
})

const { chartTheme } = useChartTheme()

// Convert data to ECharts format
const chartOption = computed(() => {
  const pieData = props.data.map((value, index) => {
    const item: any = {
      name: props.labels[index]?.name || `Item ${index + 1}`,
      value: value
    }
    // Only set color if explicitly provided, otherwise let theme handle it
    if (props.labels[index]?.color) {
      item.itemStyle = {
        color: props.labels[index].color
      }
    }
    return item
  })

  return {
    tooltip: {
      ...getShadcnTooltipConfig({
        categorySize: props.data.length
      }),
      trigger: 'item',
      axisPointer: {
        type: 'none'
      },
      formatter: (params: any) => {
        const name = params.name || ''
        const value = params.value || 0
        const percent = params.percent || 0
        const marker = params.marker || ''

        return `
          <div style="min-width: 180px; font-family: 'Geist Mono', monospace;">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                ${marker}
                <span style="color: inherit;">${name}</span>
              </div>
              <span style="font-weight: 600; color: inherit;">
                ${value.toLocaleString()}
                <span style="opacity: 0.6;">(${percent.toFixed(1)}%)</span>
              </span>
            </div>
          </div>
        `
      }
    },
    legend: {
      show: !props.hideLegend,
      orient: props.legendPosition === 'right' || props.legendPosition === 'left' ? 'vertical' : 'horizontal',
      [props.legendPosition]: 10,
      top: props.legendPosition === 'right' || props.legendPosition === 'left' ? 'center' : 10,
      data: props.labels.map(label => label.name)
    },
    toolbox: {
      show: !props.hideToolbar,
      feature: {
        restore: {
          show: true,
          title: 'Restore'
        },
        saveAsImage: {
          show: true,
          title: 'Save as Image'
        }
      },
      right: '5%',
      top: '5%'
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