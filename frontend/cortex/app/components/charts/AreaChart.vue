<script setup lang="ts">
interface BulletLegendItemInterface {
  name: string
  color: string
}

interface AreaChartProps {
  data: Record<string, any>[]
  height: number
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
  xGridLine?: boolean
  xDomainLine?: boolean
  yGridLine?: boolean
  yDomainLine?: boolean
  xTickLine?: boolean
  legendPosition?: 'top' | 'bottom' | 'left' | 'right'
}

const props = withDefaults(defineProps<AreaChartProps>(), {
  xLabel: '',
  yLabel: '',
  xNumTicks: 5,
  yNumTicks: 4,
  hideLegend: false,
  hideTooltip: false,
  xGridLine: true,
  xDomainLine: true,
  yGridLine: true,
  yDomainLine: true,
  xTickLine: false,
  legendPosition: 'top'
})
</script>

<template>
  <AreaChart
    :data="data"
    :height="height"
    :x-label="xLabel"
    :y-label="yLabel"
    :categories="categories"
    :x-formatter="xFormatter"
    :x-num-ticks="xNumTicks"
    :x-explicit-ticks="xExplicitTicks"
    :min-max-ticks-only="minMaxTicksOnly"
    :y-num-ticks="yNumTicks"
    :hide-legend="hideLegend"
    :hide-tooltip="hideTooltip"
    :x-grid-line="xGridLine"
    :x-domain-line="xDomainLine"
    :y-grid-line="yGridLine"
    :y-domain-line="yDomainLine"
    :x-tick-line="xTickLine"
    :legend-position="legendPosition"
  />
</template> 