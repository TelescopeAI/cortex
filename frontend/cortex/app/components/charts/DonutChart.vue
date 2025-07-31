<script setup lang="ts">
interface DonutChartProps {
  data: number[]
  height: number
  radius: number
  labels: Array<{ name: string; color: string }>
  type?: string
  hideLegend?: boolean
}

const props = withDefaults(defineProps<DonutChartProps>(), {
  type: 'donut',
  hideLegend: false
})
</script>

<template>
  <DonutChart
    :data="data"
    :height="height"
    :radius="radius"
    :labels="labels"
    :type="type"
    :hide-legend="hideLegend"
  >
    <slot />
  </DonutChart>
</template> 