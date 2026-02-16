<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'
import { getShadcnTooltipConfig } from '~/config/echartShadCNTooltip'

interface BulletLegendItemInterface {
  name: string
  color?: string  // Make color optional
}

interface NormalStackedAreaProps {
  data: Record<string, any>[]
  height?: number
  xLabel?: string
  yLabel?: string
  categories: Record<string, BulletLegendItemInterface>
  xFormatter: (i: number, idx?: number) => string | number
  xNumTicks?: number
  xExplicitTicks?: number
  minMaxTicksOnly?: boolean
  yNumTicks?: number
  hideLegend?: boolean
  hideTooltip?: boolean
  hideToolbar?: boolean
  xGridLine?: boolean
  xDomainLine?: boolean
  yGridLine?: boolean
  yDomainLine?: boolean
  xTickLine?: boolean
  legendPosition?: 'top' | 'bottom' | 'left' | 'right'
  dataZoom?: boolean
}

const props = withDefaults(defineProps<NormalStackedAreaProps>(), {
  xLabel: '',
  yLabel: '',
  xNumTicks: 5,
  yNumTicks: 4,
  hideLegend: false,
  hideTooltip: false,
  hideToolbar: true,
  xGridLine: false,
  xDomainLine: true,
  yGridLine: false,
  yDomainLine: true,
  xTickLine: false,
  legendPosition: 'top',
  dataZoom: true
})

const { chartTheme } = useChartTheme()

// Convert data to ECharts format with stacking
const chartOption = computed(() => {
  const xAxisData = props.data.map((_, index) => props.xFormatter(index))
  const categorySize = props.data.length

  const series = Object.keys(props.categories).map(key => {
    const categoryInfo = props.categories[key]
    const seriesConfig: any = {
      name: categoryInfo?.name || key,
      type: 'line',
      stack: 'total', // This enables stacking
      data: props.data.map(item => item[key]),
      smooth: true,
      symbol: 'none',  // Hide data point markers
      areaStyle: {
        opacity: 0.7
      }
    }

    // Only override theme colors if explicitly provided
    if (categoryInfo?.color) {
      seriesConfig.itemStyle = {
        color: categoryInfo.color
      }
      seriesConfig.lineStyle = {
        color: categoryInfo.color
      }
    }

    return seriesConfig
  })

  return {
    tooltip: {
      ...getShadcnTooltipConfig({
        categorySize
      }),
      show: !props.hideTooltip,
      axisPointer: {
        type: 'none'
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
    toolbox: {
      show: !props.hideToolbar,
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
        show: false,
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
      name: props.xLabel,
      data: xAxisData,
      boundaryGap: false,
      splitLine: {
        show: props.xGridLine
      },
      axisLine: {
        show: props.xDomainLine
      }
    },
    yAxis: {
      type: 'value',
      name: props.yLabel,
      splitLine: {
        show: props.yGridLine
      },
      axisLine: {
        show: props.yDomainLine
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
