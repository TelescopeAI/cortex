<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'

interface BulletLegendItemInterface {
  name: string
  color: string
}

interface LineChartProps {
  data: Record<string, any>[]
  height?: number // Make height optional
  categories: Record<string, BulletLegendItemInterface>
  xFormatter: (i: number, idx?: number) => string | number
  yLabel?: string
  xNumTicks?: number
  yNumTicks?: number
  curveType?: string
  legendPosition?: string
  hideLegend?: boolean
  yGridLine?: boolean
  dataZoom?: boolean
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

const { chartTheme } = useChartTheme()

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
  <div class="h-full w-full">
    <VChart 
      :option="chartOption" 
      :theme="chartTheme"
      autoresize
      class="h-full w-full min-h-[24rem]"
    />
  </div>
</template> 