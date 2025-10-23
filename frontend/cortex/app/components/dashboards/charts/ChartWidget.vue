<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardWidget as DashboardWidgetType, StandardChartData } from '~/types/dashboards'
import { VisualizationType } from '~/types/dashboards'
import {
  BarChart,
  LineChart,
  AreaChart,
  DonutChart,
  SingleValue,
  Gauge,
  Table,
  Scatter,
  BoxPlot,
  StackedBarChart,
  StackedLineChart,
  NormalStackedArea,
  GradientStackedArea
} from '~/components/charts'

interface Props {
  widget: DashboardWidgetType
  data: StandardChartData
  executionResult?: any
}

const props = defineProps<Props>()

// Determine which chart component to use based on visualization type and config
const chartComponent = computed(() => {
  const vizType = props.widget.visualization.type
  const chartConfig = props.widget.visualization.chart_config
  const stackBars = chartConfig?.stack_bars || false
  
  // For chart types that support stacking, check if stacking is enabled
  if (stackBars) {
    switch (vizType) {
      case VisualizationType.BAR_CHART:
        return StackedBarChart
      case VisualizationType.LINE_CHART:
        return StackedLineChart
      case VisualizationType.AREA_CHART:
        // For area charts, check the stacking type preference
        const areaStackingType = chartConfig?.area_stacking_type || 'normal'
        return areaStackingType === 'gradient' ? GradientStackedArea : NormalStackedArea
      default:
        break
    }
  }
  
  // Default chart components (non-stacked)
  switch (vizType) {
    case VisualizationType.BAR_CHART:
      return BarChart
    case VisualizationType.LINE_CHART:
      return LineChart
    case VisualizationType.AREA_CHART:
      return AreaChart
    case VisualizationType.PIE_CHART:
    case VisualizationType.DONUT_CHART:
      return DonutChart
    case VisualizationType.SCATTER_PLOT:
      return Scatter
    case VisualizationType.BOX_PLOT:
      return BoxPlot
    case VisualizationType.SINGLE_VALUE:
      return SingleValue
    case VisualizationType.GAUGE:
      return Gauge
    case VisualizationType.TABLE:
      return Table
    default:
      return null
  }
})

// Prepare data for chart components
const chartData = computed(() => {
  const { processed, metadata } = props.data
  
  if (!processed.series || processed.series.length === 0) {
    return []
  }
  
  // Convert series data to the format expected by chart components
  const firstSeries = processed.series[0]
  if (!firstSeries || !firstSeries.data || firstSeries.data.length === 0) {
    return []
  }
  
  // Create data array with x-axis values and y-axis values for each series
  return firstSeries.data.map((point, index) => {
    const dataPoint: Record<string, any> = {
      index,
      x: point.x
    }
    
    // Add y values for each series
    processed.series?.forEach(series => {
      if (series.data[index] && 'y' in series.data[index]) {
        dataPoint[series.name] = (series.data[index] as any).y
      }
    })
    
    return dataPoint
  })
})

// Prepare categories for chart components
const chartCategories = computed(() => {
  const { processed } = props.data
  
  if (!processed.series || processed.series.length === 0) {
    return {}
  }
  
  const categories: Record<string, { name: string; color: string }> = {}
  
  processed.series.forEach((series, index) => {
    const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#8b5cf6', '#d946ef']
    if (series.name) {
      categories[series.name] = {
        name: series.name,
        color: series.color || colors[index % colors.length] as string
      }
    }
  })
  
  return categories
})

// X-axis formatter
const xFormatter = (i: number): string | number => {
  return chartData.value[i]?.x || ''
}

// Y-axis keys for bar charts
const yAxisKeys = computed(() => {
  if (!chartData.value.length) return []
  const firstRow = chartData.value[0]
  if (!firstRow) return []
  return Object.keys(firstRow).filter(key => key !== 'index' && key !== 'x')
})

// Get chart props based on component type
const chartProps = computed(() => {
  const vizType = props.widget.visualization.type
  const { metadata } = props.data
  
  const baseProps = {
    data: chartData.value,
    categories: chartCategories.value,
    xFormatter,
    hideLegend: props.widget.visualization.show_legend === false,
    yGridLine: props.widget.visualization.show_grid !== false
  }
  
  switch (vizType) {
    case VisualizationType.BAR_CHART:
      return {
        ...baseProps,
        yAxis: yAxisKeys.value,
        xNumTicks: 7,
        radius: 4,
        legendPosition: 'top'
      }
    
    case VisualizationType.LINE_CHART:
      return {
        ...baseProps,
        yLabel: metadata.y_axes_title,
        xNumTicks: 7,
        yNumTicks: 4,
        curveType: 'smooth',
        legendPosition: 'top'
      }
    
    case VisualizationType.AREA_CHART:
      return {
        ...baseProps,
        xLabel: metadata.x_axis_title,
        yLabel: metadata.y_axes_title,
        xNumTicks: 7,
        yNumTicks: 4,
        legendPosition: 'top'
      }
    
    case VisualizationType.PIE_CHART:
    case VisualizationType.DONUT_CHART:
      return {
        data: props.data.processed.categories?.map(cat => cat.value) || [],
        labels: props.data.processed.categories?.map(cat => ({
          name: cat.name,
          color: cat.color || '#3b82f6'
        })) || [],
        radius: vizType === VisualizationType.DONUT_CHART ? 70 : 0,
        hideLegend: props.widget.visualization.show_legend === false
      }
    
    case VisualizationType.SCATTER_PLOT:
      return {
        series: props.data.processed.series?.map(series => ({
          name: series.name,
          data: series.data.map(point => ({ x: point.x, y: 'y' in point ? point.y : 0 }))
        })) || []
      }
    
    case VisualizationType.BOX_PLOT:
      return {
        series: props.data.processed.series || [],
        xLabel: metadata.x_axis_title,
        yLabel: metadata.y_axes_title
      }
    
    case VisualizationType.SINGLE_VALUE:
      return {
        title: metadata.title || props.widget.title,
        description: metadata.description,
        value: props.data.processed.value,
        config: props.widget.visualization.single_value_config
      }
    
    case VisualizationType.GAUGE:
      return {
        value: props.data.processed.value || 0,
        min: props.widget.visualization.gauge_config?.min_value || 0,
        max: props.widget.visualization.gauge_config?.max_value || 100,
        thickness: props.widget.visualization.gauge_config?.thickness || 10,
        targetValue: props.widget.visualization.gauge_config?.target_value,
        colorRanges: props.widget.visualization.gauge_config?.color_ranges,
        showValue: props.widget.visualization.gauge_config?.show_value !== false,
        showTarget: props.widget.visualization.gauge_config?.show_target !== false,
        gaugeType: props.widget.visualization.gauge_config?.gauge_type || 'arc',
        title: (metadata.title || props.widget.title) || '',
        showLegend: props.widget.visualization.show_legend !== false,
        showGrid: props.widget.visualization.show_grid !== false,
        showAxesLabels: props.widget.visualization.show_axes_labels !== false
      }
    
    case VisualizationType.TABLE:
      return {
        columns: props.data.processed.table?.columns || [],
        rows: props.data.processed.table?.rows || []
      }
    
    default:
      return baseProps
  }
})
</script>

<template>
  <div class="h-full min-h-[200px]">
    <!-- Render the appropriate chart component dynamically -->
    <component
      v-if="chartComponent"
      :is="chartComponent"
      v-bind="chartProps"
    />
    
    <!-- Fallback for unsupported chart types -->
    <div v-else class="flex items-center justify-center h-full text-muted-foreground">
      <p>Unsupported chart type: {{ widget.visualization.type }}</p>
    </div>
  </div>
</template>
