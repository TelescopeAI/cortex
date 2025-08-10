<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import type { DashboardWidget as DashboardWidgetType, StandardChartData, VisualizationType } from '~/types/dashboards'

interface Props {
  widget: DashboardWidgetType
  data: StandardChartData
  executionResult?: any
}

const props = defineProps<Props>()

// Chart options for different chart types
const chartOption = computed(() => {
  const { processed, metadata } = props.data
  const vizType = props.widget.visualization.type
  
  // Base configuration
  const baseOption = {
    title: {
      text: metadata.title || props.widget.title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'transparent',
      textStyle: {
        color: '#fff'
      }
    },
    legend: {
      show: props.widget.visualization.show_legend !== false,
      bottom: 0,
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.widget.visualization.show_legend !== false ? '15%' : '3%',
      top: metadata.title ? '15%' : '3%',
      containLabel: true
    }
  }

  // Handle different chart types
  switch (vizType) {
    case 'bar_chart':
      return {
        ...baseOption,
        xAxis: {
          type: metadata.data_types.x === 'temporal' ? 'time' : 'category',
          name: metadata.x_axis_title,
          nameLocation: 'middle',
          nameGap: 30,
          show: props.widget.visualization.show_axes_labels !== false,
          data: processed.series?.[0]?.data.map(d => d.x) || []
        },
        yAxis: {
          type: 'value',
          name: metadata.y_axis_title,
          nameLocation: 'middle',
          nameGap: 50,
          show: props.widget.visualization.show_axes_labels !== false
        },
        series: processed.series?.map(series => ({
          name: series.name,
          type: 'bar',
          data: series.data.map(d => d.y),
          itemStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          }
        })) || []
      }

    case 'line_chart':
      return {
        ...baseOption,
        xAxis: {
          type: metadata.data_types.x === 'temporal' ? 'time' : 'category',
          name: metadata.x_axis_title,
          nameLocation: 'middle',
          nameGap: 30,
          show: props.widget.visualization.show_axes_labels !== false,
          data: processed.series?.[0]?.data.map(d => d.x) || []
        },
        yAxis: {
          type: 'value',
          name: metadata.y_axis_title,
          nameLocation: 'middle',
          nameGap: 50,
          show: props.widget.visualization.show_axes_labels !== false
        },
        series: processed.series?.map(series => ({
          name: series.name,
          type: 'line',
          data: series.data.map(d => d.y),
          smooth: true,
          itemStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          },
          lineStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          }
        })) || []
      }

    case 'area_chart':
      return {
        ...baseOption,
        xAxis: {
          type: metadata.data_types.x === 'temporal' ? 'time' : 'category',
          name: metadata.x_axis_title,
          nameLocation: 'middle',
          nameGap: 30,
          show: props.widget.visualization.show_axes_labels !== false,
          data: processed.series?.[0]?.data.map(d => d.x) || []
        },
        yAxis: {
          type: 'value',
          name: metadata.y_axis_title,
          nameLocation: 'middle',
          nameGap: 50,
          show: props.widget.visualization.show_axes_labels !== false
        },
        series: processed.series?.map(series => ({
          name: series.name,
          type: 'line',
          data: series.data.map(d => d.y),
          smooth: true,
          areaStyle: {
            opacity: 0.7
          },
          itemStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          },
          lineStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          }
        })) || []
      }

    case 'pie_chart':
    case 'donut_chart':
      return {
        ...baseOption,
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        series: [{
          name: metadata.title || 'Data',
          type: 'pie',
          radius: vizType === 'donut_chart' ? ['40%', '70%'] : '70%',
          center: ['50%', '50%'],
          data: processed.categories?.map(cat => ({
            name: cat.name,
            value: cat.value,
            itemStyle: {
              color: cat.color || getColorFromScheme(props.widget.visualization.color_scheme)
            }
          })) || [],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }

    case 'scatter_plot':
      return {
        ...baseOption,
        xAxis: {
          type: 'value',
          name: metadata.x_axis_title,
          nameLocation: 'middle',
          nameGap: 30,
          show: props.widget.visualization.show_axes_labels !== false
        },
        yAxis: {
          type: 'value',
          name: metadata.y_axis_title,
          nameLocation: 'middle',
          nameGap: 50,
          show: props.widget.visualization.show_axes_labels !== false
        },
        series: processed.series?.map(series => ({
          name: series.name,
          type: 'scatter',
          data: series.data.map(d => [d.x, d.y]),
          symbolSize: 8,
          itemStyle: {
            color: series.color || getColorFromScheme(props.widget.visualization.color_scheme)
          }
        })) || []
      }

    default:
      return baseOption
  }
})

// Color scheme helper
function getColorFromScheme(scheme?: string) {
  const colorSchemes = {
    blue: '#3b82f6',
    green: '#10b981',
    red: '#ef4444',
    purple: '#8b5cf6',
    orange: '#f97316',
    default: '#6b7280'
  }
  return colorSchemes[scheme as keyof typeof colorSchemes] || colorSchemes.default
}
</script>

<template>
  <div class="h-full min-h-[200px]">
    <VChart 
      :option="chartOption" 
      autoresize
      class="h-full w-full"
    />
  </div>
</template>