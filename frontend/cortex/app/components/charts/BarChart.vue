<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'

interface BulletLegendItemInterface {
  name: string
  color: string
}

interface BarChartProps {
  data: Record<string, any>[]
  height?: number // Make height optional
  categories: Record<string, BulletLegendItemInterface>
  yAxis: string[]
  xFormatter: (i: number, idx?: number) => string | number
  yFormatter?: (i: number, idx?: number) => string | number
  xNumTicks?: number
  radius?: number
  yGridLine?: boolean
  legendPosition?: string
  hideLegend?: boolean
  dataZoom?: boolean
}

const props = withDefaults(defineProps<BarChartProps>(), {
  yFormatter: (i: number) => i,
  xNumTicks: 5,
  radius: 0,
  yGridLine: true,
  legendPosition: 'top',
  hideLegend: false
})

const { chartTheme } = useChartTheme()

// Convert data to ECharts format
const chartOption = computed(() => {
  const xAxisData = props.data.map((_, index) => props.xFormatter(index))
  
  const series = props.yAxis.map(key => {
    const categoryInfo = props.categories[key]
    return {
      name: categoryInfo?.name || key,
      type: 'bar',
      data: props.data.map(item => item[key]),
      itemStyle: {
        color: categoryInfo?.color || '#3b82f6',
        borderRadius: props.radius
      }
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValueLabel}<br/>`
        params.forEach((param: any) => {
          const formattedValue = props.yFormatter ? props.yFormatter(param.value) : param.value
          result += `${param.marker} ${param.seriesName}: ${formattedValue}<br/>`
        })
        return result
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
      bottom: props.dataZoom ? '20%' : '3%',
      top: props.hideLegend ? '3%' : '15%',
      containLabel: true
    },
    toolbox: {
      show: true,
      feature: {
        dataZoom: {
          show: true,
          title: {
            zoom: 'Zoom',
            back: 'Reset Zoom'
          }
        },
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
    dataZoom: props.dataZoom ? [
      {
        type: 'inside',
        xAxisIndex: [0],
        filterMode: 'none'
      },
      {
        type: 'slider',
        xAxisIndex: [0],
        bottom: '5%',
        height: '12%',
        filterMode: 'none',
        showDetail: false,
        showDataShadow: true,
        handleSize: '110%',
        handleStyle: {
          color: '#fff',
          shadowBlur: 3,
          shadowColor: 'rgba(0,0,0,0.6)',
          shadowOffsetX: 2,
          shadowOffsetY: 2
        }
      }
    ] : undefined,
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: {
      type: 'value',
      splitLine: {
        show: props.yGridLine
      }
    },
    series: series
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