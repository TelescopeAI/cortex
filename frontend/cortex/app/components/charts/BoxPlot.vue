<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'
import { getShadcnTooltipConfig } from '~/config/echartShadCNTooltip'
import type { BoxPlotDataPoint, ChartSeries } from '~/types/dashboards'

interface BoxPlotProps {
  series: ChartSeries[]
  height?: number
  yLabel?: string
  xLabel?: string
  hideLegend?: boolean
  hideToolbar?: boolean
  xGridLine?: boolean
  yGridLine?: boolean
  dataZoom?: boolean
  legendPosition?: string
}

const props = withDefaults(defineProps<BoxPlotProps>(), {
  hideLegend: false,
  hideToolbar: true,
  xGridLine: false,
  yGridLine: false,
  dataZoom: false,
  legendPosition: 'top'
})

const { chartTheme } = useChartTheme()

// Transform standardized data to ECharts format
const echartsData = computed(() => {
  if (!props.series || props.series.length === 0) {
    return { categories: [], boxData: [], outliers: [] }
  }
  
  // Get the first series data (Box Plot typically has one series)
  const firstSeries = props.series[0]
  if (!firstSeries || !firstSeries.data) {
    return { categories: [], boxData: [], outliers: [] }
  }
  
  const categories = firstSeries.data.map(d => d.x) || []
  
  // Convert standardized format to ECharts array format: [min, Q1, median, Q3, max]
  // For ECharts boxplot, we need to create a single series with all data points
  const boxData = (firstSeries.data as BoxPlotDataPoint[]).map(d => {
    // Backend should now provide correct data, so we can use it directly
    return [d.min, d.q1, d.median, d.q3, d.max]
  })
  
  // Extract outliers if present - format as [categoryIndex, outlierValue]
  const outliers = (firstSeries.data as BoxPlotDataPoint[]).flatMap((d, idx) => 
    (d.outliers || []).map((value: number) => [idx, value])
  ) || []
  
  return { categories, boxData, outliers }
})

const option = computed(() => {
  return {
    tooltip: {
      ...getShadcnTooltipConfig({
        categorySize: echartsData.value.categories.length
      }),
      trigger: 'item',
      axisPointer: {
        type: 'none'
      },
      formatter: (params: any) => {
        if (params.componentSubType === 'boxplot') {
          const data = params.data
          const categoryName = echartsData.value.categories[params.dataIndex] || 'Unknown'
          return `${categoryName}<br/>
            Max: ${data[4]}<br/>
            Q3: ${data[3]}<br/>
            Median: ${data[2]}<br/>
            Q1: ${data[1]}<br/>
            Min: ${data[0]}`
        } else {
          const categoryName = echartsData.value.categories[params.dataIndex] || 'Unknown'
          return `${categoryName}<br/>Outlier: ${params.data[1]}`
        }
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.dataZoom ? '20%' : '3%',
      top: props.hideLegend ? '3%' : '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: echartsData.value.categories,
      name: props.xLabel,
      nameLocation: 'middle',
      nameGap: 30,
      boundaryGap: true,
      splitLine: {
        show: props.xGridLine
      },
      axisLabel: {
        formatter: (value: string) => {
          return value.length > 15 ? value.substring(0, 12) + '...' : value
        }
      }
    },
    yAxis: {
      type: 'value',
      name: props.yLabel,
      nameLocation: 'middle',
      nameGap: 50,
      splitLine: {
        show: props.yGridLine
      }
    },
    legend: {
      show: !props.hideLegend,
      [props.legendPosition]: 10,
      data: props.series.map(s => s.name)
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
    series: [
      // Box plot series
      {
        name: props.series[0]?.name || 'Box Plot',
        type: 'boxplot',
        data: echartsData.value.boxData
      },
      // Outliers series (if any)
      ...(echartsData.value.outliers.length > 0 ? [{
        name: 'Outliers',
        type: 'scatter',
        data: echartsData.value.outliers,
        symbolSize: 4
      }] : [])
    ]
  }
})
</script>

<template>
  <div class="h-full w-full">
    <VChart :option="option" :theme="chartTheme" autoresize class="h-full w-full min-h-[24rem]" />
  </div>
</template>
