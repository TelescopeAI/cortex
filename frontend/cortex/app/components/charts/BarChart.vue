<script setup lang="ts">
interface BulletLegendItemInterface {
  name: string
  color: string
}

interface BarChartProps {
  data: Record<string, any>[]
  height: number
  categories: Record<string, BulletLegendItemInterface>
  yAxis: string[]
  xFormatter: (i: number, idx?: number) => string | number
  yFormatter?: (i: number, idx?: number) => string | number
  xNumTicks?: number
  radius?: number
  yGridLine?: boolean
  legendPosition?: string
  hideLegend?: boolean
}

const props = withDefaults(defineProps<BarChartProps>(), {
  yFormatter: (i: number) => i,
  xNumTicks: 5,
  radius: 0,
  yGridLine: true,
  legendPosition: 'top',
  hideLegend: false
})
</script>

<template>
  <BarChart
    :data="data"
    :height="height"
    :categories="categories"
    :y-axis="yAxis"
    :x-formatter="xFormatter"
    :y-formatter="yFormatter"
    :x-num-ticks="xNumTicks"
    :radius="radius"
    :y-grid-line="yGridLine"
    :legend-position="legendPosition"
    :hide-legend="hideLegend"
  />
</template> 