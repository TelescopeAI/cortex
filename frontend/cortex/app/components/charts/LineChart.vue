<script setup lang="ts">
interface BulletLegendItemInterface {
  name: string
  color: string
}

interface LineChartProps {
  data: Record<string, any>[]
  height: number
  categories: Record<string, BulletLegendItemInterface>
  xFormatter: (i: number, idx?: number) => string | number
  yLabel?: string
  xNumTicks?: number
  yNumTicks?: number
  curveType?: string
  legendPosition?: string
  hideLegend?: boolean
  yGridLine?: boolean
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
</script>

<template>
  <LineChart
    :data="data"
    :height="height"
    :categories="categories"
    :x-formatter="xFormatter"
    :y-label="yLabel"
    :x-num-ticks="xNumTicks"
    :y-num-ticks="yNumTicks"
    :curve-type="curveType"
    :legend-position="legendPosition"
    :hide-legend="hideLegend"
    :y-grid-line="yGridLine"
  />
</template> 