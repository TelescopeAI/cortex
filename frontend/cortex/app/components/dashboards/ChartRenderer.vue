<script setup lang="ts">
import { computed } from 'vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import SingleValue from '@/components/charts/SingleValue.vue'
import Gauge from '@/components/charts/Gauge.vue'
import Scatter from '@/components/charts/Scatter.vue'
import BoxPlot from '@/components/charts/BoxPlot.vue'
import TableView from '@/components/charts/Table.vue'
import StackedBarChart from '@/components/charts/StackedBarChart.vue'
import StackedLineChart from '@/components/charts/StackedLineChart.vue'
import NormalStackedArea from '@/components/charts/NormalStackedArea.vue'
import GradientStackedArea from '@/components/charts/GradientStackedArea.vue'

interface Props {
  processed: any
  metadata?: any
  type: string
  gaugeConfig?: any
  singleValueConfig?: any
  chartConfig?: any
  error?: string | null
  dataZoom?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  dataZoom: false
})

const isPieOrDonut = computed(() => props.type === 'pie_chart' || props.type === 'donut_chart')

const lineAreaBarData = computed(() => {
  const series = Array.isArray(props.processed?.series) ? props.processed.series : []
  const categories: Record<string, { name: string }> = {}
  const rowsMap: Record<string, any> = {}
  series.forEach((s: any, sIdx: number) => {
    const seriesName = String((s && s.name) ? s.name : `Series ${sIdx + 1}`)
    // Don't pass color at all - let theme gradients apply
    categories[seriesName] = { name: seriesName }
    const dataPoints: any[] = Array.isArray(s?.data) ? (s.data as any[]) : []
    dataPoints.forEach((p: any) => {
      const x: string = String(p?.x ?? '')
      const y: number = typeof p?.y === 'number' ? (p.y as number) : Number(p?.y) || 0
      const key = String(x)
      if (!rowsMap[key]) rowsMap[key] = { x }
      rowsMap[key][seriesName] = y
    })
  })
  return { rows: Object.values(rowsMap), categories }
})

const donutData = computed(() => {
  const firstSeries: any = Array.isArray(props.processed?.series) ? (props.processed.series as any[])[0] : null
  const points: any[] = Array.isArray(firstSeries?.data) ? (firstSeries.data as any[]) : []
  const values = points.map((p: any) => (typeof p?.y === 'number' ? p.y : Number(p?.y) || 0))
  const labels: { name: string; color?: string }[] = points.map((p: any, idx: number) => ({ name: String(p?.x ?? String(idx)) }))
  return { values, labels }
})

const scatterSeries = computed(() => {
  const series = Array.isArray(props.processed?.series) ? (props.processed.series as any[]) : []
  return series.map((s, idx) => ({
    name: String(s?.name ?? `Series ${idx + 1}`),
    data: Array.isArray(s?.data) ? s.data.map((p:any) => ({ x: p?.x, y: typeof p?.y === 'number' ? p.y : Number(p?.y) || 0 })) : []
  }))
})

// Get chart config from props or metadata
const effectiveChartConfig = computed(() => {
  return props.chartConfig || props.metadata?.chart_config || {}
})

// Determine which stacked area component to use
const stackedAreaComponent = computed(() => {
  if (!effectiveChartConfig.value?.stack_bars) return null
  const stackingType = effectiveChartConfig.value?.area_stacking_type || 'normal'
  return stackingType === 'gradient' ? GradientStackedArea : NormalStackedArea
})
</script>

<template>
  <div class="w-full h-full">
    <div v-if="metadata?.title === 'Error' || error" class="w-full">
      <div class="text-xs text-destructive border border-destructive/30 bg-destructive/10 rounded p-2">
        {{ metadata?.description || error || 'Failed to render chart' }}
      </div>
    </div>
    <template v-else>
    <div v-if="type === 'single_value'" class="w-full h-full">
      <SingleValue :title="metadata?.title" :description="metadata?.description" :value="processed?.value" :config="singleValueConfig" />
    </div>
    <div v-else-if="type === 'gauge'" class="w-full h-full">
      <Gauge 
        :value="Number(processed?.value ?? 0)" 
        :min="Number(gaugeConfig?.min_value ?? metadata?.ranges?.min ?? 0)" 
        :max="Number(gaugeConfig?.max_value ?? metadata?.ranges?.max ?? 100)" 
        :thickness="Number(gaugeConfig?.thickness ?? 10)"
        :title="metadata?.title || ''"
        :show-value="gaugeConfig?.show_value ?? true"
        :show-target="gaugeConfig?.show_target ?? true"
        :gauge-type="gaugeConfig?.gauge_type ?? 'arc'"
        :target-value="gaugeConfig?.target_value"
        :color-ranges="gaugeConfig?.color_ranges"
        :show-legend="gaugeConfig?.show_legend ?? false"
        :show-grid="gaugeConfig?.show_grid ?? false"
        :show-axes-labels="gaugeConfig?.show_axes_labels ?? false"
      />
    </div>
    <div v-else-if="isPieOrDonut" class="w-full h-full">
      <DonutChart :data="donutData.values" :radius="80" :labels="donutData.labels" />
    </div>
    <div v-else-if="type === 'area_chart'" class="w-full h-full">
      <!-- Use stacked area chart when stacking is enabled -->
      <component
        v-if="effectiveChartConfig.stack_bars && stackedAreaComponent"
        :is="stackedAreaComponent"
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
      <AreaChart
        v-else
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
    </div>
    <div v-else-if="type === 'line_chart'" class="w-full h-full">
      <!-- Use stacked line chart when stacking is enabled -->
      <StackedLineChart
        v-if="effectiveChartConfig.stack_bars"
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
      <LineChart
        v-else
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
    </div>
    <div v-else-if="type === 'bar_chart'" class="w-full h-full">
      <!-- Use stacked bar chart when stacking is enabled -->
      <StackedBarChart
        v-if="effectiveChartConfig.stack_bars"
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :y-axis="Object.keys(lineAreaBarData.categories)"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-formatter="(v:number)=> v"
        :x-num-ticks="7"
        :radius="4"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
      <BarChart
        v-else
        :data="lineAreaBarData.rows as any"
        :categories="lineAreaBarData.categories"
        :y-axis="Object.keys(lineAreaBarData.categories)"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-formatter="(v:number)=> v"
        :x-num-ticks="7"
        :radius="4"
        :legend-position="'top'"
        :hide-legend="false"
        :data-zoom="dataZoom"
      />
    </div>
    <div v-else-if="type === 'scatter_plot'" class="w-full h-full">
      <Scatter :series="scatterSeries as any" :data-zoom="dataZoom" />
    </div>
    <div v-else-if="type === 'box_plot'" class="w-full h-full">
      <BoxPlot :series="processed?.series || []" :x-label="metadata?.x_label" :y-label="metadata?.y_label" />
    </div>
    <div v-else-if="type === 'table'" class="w-full h-full">
      <TableView :columns="processed?.table?.columns || []" :rows="processed?.table?.rows || []" />
    </div>
    <div v-else class="w-full h-full">
      <div class="text-sm text-muted-foreground">No chart renderer for this visualization type. Switch to JSON.</div>
    </div>
    </template>
  </div>
  
</template>


