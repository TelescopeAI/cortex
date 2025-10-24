<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'
import type { BoxPlotDataPoint, ChartSeries } from '~/types/dashboards'

interface BoxPlotProps {
  series: ChartSeries[]
  height?: number
  yLabel?: string
  xLabel?: string
}

const props = defineProps<BoxPlotProps>()

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
      trigger: 'item',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        if (params.componentSubType === 'boxplot') {
          const data = params.data
          // Get the category name from the x-axis data
          const categoryName = echartsData.value.categories[params.dataIndex] || 'Unknown'
          return `${categoryName}<br/>
            Max: ${data[4]}<br/>
            Q3: ${data[3]}<br/>
            Median: ${data[2]}<br/>
            Q1: ${data[1]}<br/>
            Min: ${data[0]}`
        } else {
          // For outliers, also use the category name
          const categoryName = echartsData.value.categories[params.dataIndex] || 'Unknown'
          return `${categoryName}<br/>Outlier: ${params.data[1]}`
        }
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
      backgroundColor: 'rgba(0, 0, 0, 0.02)',
      borderColor: 'rgba(0, 0, 0, 0.1)',
      borderWidth: 1
    },
    xAxis: {
      type: 'category',
      data: echartsData.value.categories,
      name: props.xLabel,
      nameLocation: 'middle',
      nameGap: 30,
      boundaryGap: true,
      splitArea: {
        show: false
      },
      splitLine: {
        show: false
      },
      axisLabel: {
        formatter: (value: string) => {
          // Truncate long labels if necessary
          return value.length > 15 ? value.substring(0, 12) + '...' : value
        },
        color: '#666',
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisTick: {
        lineStyle: {
          color: '#ccc'
        }
      }
    },
    yAxis: {
      type: 'value',
      name: props.yLabel,
      nameLocation: 'middle',
      nameGap: 50,
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
        }
      },
      splitLine: {
        lineStyle: {
          color: '#e0e0e0',
          type: 'dashed'
        }
      },
      axisLabel: {
        color: '#666',
        fontSize: 12
      },
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      }
    },
    legend: {
      data: props.series.map(s => s.name),
      top: 10,
      left: 'center',
      textStyle: {
        color: '#666',
        fontSize: 12
      }
    },
    dataZoom: [
      {
        type: 'inside', // Zoom by scrolling
        start: 0,
        end: 100
      },
      {
        type: 'slider', // Zoom with a slider
        start: 0,
        end: 100,
        height: 20,
        bottom: 10
      }
    ],
    toolbox: {
      show: true,
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {},
        dataView: { readOnly: true }
      },
      right: 20,
      top: 0
    },
    series: [
      // Box plot series
      {
        name: props.series[0]?.name || 'Box Plot',
        type: 'boxplot',
        data: echartsData.value.boxData,
        itemStyle: {
          color: '#5470c6',
          borderColor: '#5470c6',
          borderWidth: 1
        },
        boxWidth: ['7%', '50%'],
        emphasis: {
          itemStyle: {
            borderColor: '#5470c6',
            borderWidth: 2
          }
        }
      },
      // Outliers series (if any)
      ...(echartsData.value.outliers.length > 0 ? [{
        name: 'Outliers',
        type: 'scatter',
        data: echartsData.value.outliers,
        itemStyle: {
          color: 'rgba(255, 99, 71, 0.8)',
          borderColor: 'rgba(255, 99, 71, 1)',
          borderWidth: 1
        },
        symbolSize: 4,
        emphasis: {
          itemStyle: {
            color: 'rgba(255, 99, 71, 1)',
            borderColor: 'rgba(255, 99, 71, 1)',
            borderWidth: 2
          }
        }
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
