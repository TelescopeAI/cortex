<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ series: { name: string; data: { x: number | string; y: number }[] }[]; height?: number }>()

const option = computed(() => ({
  tooltip: { trigger: 'item', formatter: (p:any) => `${p.seriesName}<br/>(${p.data[0]}, ${p.data[1]})` },
  xAxis: { type: 'category' },
  yAxis: { type: 'value' },
  series: props.series.map(s => ({ name: s.name, type: 'scatter', data: s.data.map(p => [p.x, p.y]) }))
}))
</script>

<template>
  <VChart :option="option" :style="{ height: `${height ?? 320}px` }" autoresize />
</template>


