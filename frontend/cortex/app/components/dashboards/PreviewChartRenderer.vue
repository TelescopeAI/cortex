<script setup lang="ts">
import { computed } from 'vue'
import { Card } from '@/components/ui/card'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'
import DonutChart from '@/components/charts/DonutChart.vue'
import SingleValue from '@/components/charts/SingleValue.vue'
import Gauge from '@/components/charts/Gauge.vue'
import Scatter from '@/components/charts/Scatter.vue'
import TableView from '@/components/charts/Table.vue'

const props = defineProps<{ processed: any; metadata?: any; type: string; gaugeConfig?: any }>()

// Normalize processed data into inputs our chart wrappers expect
const isPieOrDonut = computed(() => props.type === 'pie_chart' || props.type === 'donut_chart')

const lineAreaBarData = computed(() => {
  // Expect processed.series: [{ name, data: [{x,y}] }]
  const series = Array.isArray(props.processed?.series) ? props.processed.series : []
  const xValues: any[] = []
  const categories: Record<string, { name: string; color: string }> = {}
  const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#8b5cf6', '#d946ef']

  // Compose rows of objects in the shape our wrappers need: [{ xLabel, series1, series2 }]
  const rowsMap: Record<string, any> = {}
  series.forEach((s: any, sIdx: number) => {
    const seriesName = String((s && s.name) ? s.name : `Series ${sIdx + 1}`)
    categories[seriesName] = {
      name: seriesName,
      color: colors[sIdx % colors.length] || '#3b82f6'
    }
    const dataPoints: any[] = Array.isArray(s?.data) ? (s.data as any[]) : []
    dataPoints.forEach((p: any) => {
      const x: string = String(p?.x ?? '')
      const y: number = typeof p?.y === 'number' ? (p.y as number) : Number(p?.y) || 0
      const key = String(x)
      if (!rowsMap[key]) rowsMap[key] = { x }
      const catName = (categories[seriesName] && categories[seriesName].name) ? categories[seriesName].name : seriesName
      rowsMap[key][catName] = y
    })
  })

  const rows = Object.values(rowsMap)
  return {
    rows,
    categories
  }
})

const donutData = computed(() => {
  // Expect processed.series[0].data as [{x,y}] or processed.value list
  const firstSeries: any = Array.isArray(props.processed?.series) ? (props.processed.series as any[])[0] : null
  const points: any[] = Array.isArray(firstSeries?.data) ? (firstSeries.data as any[]) : []
  const values = points.map((p: any) => (typeof p?.y === 'number' ? p.y : Number(p?.y) || 0))
  const labels: { name: string; color: string }[] = points.map((p: any, idx: number) => ({ name: String(p?.x ?? String(idx)), color: ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#8b5cf6', '#d946ef'][idx % 6] || '#3b82f6' }))
  return { values, labels }
})

const scatterSeries = computed(() => {
  const series = Array.isArray(props.processed?.series) ? (props.processed.series as any[]) : []
  return series.map((s, idx) => ({
    name: String(s?.name ?? `Series ${idx + 1}`),
    data: Array.isArray(s?.data) ? s.data.map((p:any) => ({ x: p?.x, y: typeof p?.y === 'number' ? p.y : Number(p?.y) || 0 })) : []
  }))
})
</script>

<template>
  <div class="w-full h-full">
    <!-- Single chain for all viz types to avoid stray fallback rendering -->
    <div v-if="type === 'single_value'">
      <SingleValue :title="metadata?.title" :description="metadata?.description" :value="processed?.value" />
    </div>
    <div v-else-if="type === 'gauge'" class="w-full">
      <Gauge 
        :value="Number(processed?.value ?? 0)" 
        :min="Number(gaugeConfig?.min_value ?? metadata?.ranges?.min ?? 0)" 
        :max="Number(gaugeConfig?.max_value ?? metadata?.ranges?.max ?? 100)" 
        :thickness="Number(gaugeConfig?.thickness ?? 10)"
        :height="undefined"
        :title="metadata?.title || ''"
      />
    </div>
    <div v-else-if="isPieOrDonut">
      <DonutChart :data="donutData.values" :height="320" :radius="80" :labels="donutData.labels" />
    </div>
    <div v-else-if="type === 'area_chart'">
      <AreaChart
        :data="lineAreaBarData.rows as any"
        :height="320"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
      />
    </div>
    <div v-else-if="type === 'line_chart'">
      <LineChart
        :data="lineAreaBarData.rows as any"
        :height="320"
        :categories="lineAreaBarData.categories"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-num-ticks="4"
        :x-num-ticks="7"
        :legend-position="'top'"
        :hide-legend="false"
      />
    </div>
    <div v-else-if="type === 'bar_chart'">
      <BarChart
        :data="lineAreaBarData.rows as any"
        :height="320"
        :categories="lineAreaBarData.categories"
        :y-axis="Object.keys(lineAreaBarData.categories)"
        :x-formatter="(i:number)=> (lineAreaBarData.rows[i]?.x ?? '')"
        :y-formatter="(v:number)=> v"
        :x-num-ticks="7"
        :radius="4"
        :y-grid-line="true"
        :legend-position="'top'"
        :hide-legend="false"
      />
    </div>
    <div v-else-if="type === 'scatter_plot'">
      <Scatter :series="scatterSeries as any" :height="320" />
    </div>
    <div v-else-if="type === 'table'">
      <TableView :columns="processed?.table?.columns || []" :rows="processed?.table?.rows || []" />
    </div>
    <div v-else>
      <div class="text-sm text-muted-foreground">No chart renderer for this visualization type. Switch to JSON.</div>
    </div>
  </div>
</template>


