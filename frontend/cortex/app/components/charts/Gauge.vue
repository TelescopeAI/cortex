<script setup lang="ts">
import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'

const props = defineProps<{
  value: number
  min?: number
  max?: number
  thickness?: number
  colorRanges?: Array<{ min: number; max: number; color: string }>
  showValue?: boolean
  height?: number
  title?: string
}>()

const { width } = useWindowSize()

const resolvedHeight = computed(() => {
  if (typeof props.height === 'number') return props.height
  const w = width.value || 1024
  if (w < 640) return 260
  if (w < 1024) return 320
  return 380
})

const option = computed(() => {
  const min = props.min ?? 0
  const max = props.max ?? 100
  const thickness = props.thickness ?? 10
  const ranges = props.colorRanges ?? [
    { min, max: min + (max - min) * 0.3, color: '#ef4444' },
    { min: min + (max - min) * 0.3, max: min + (max - min) * 0.7, color: '#f97316' },
    { min: min + (max - min) * 0.7, max, color: '#10b981' }
  ]
  const colorStops = [] as { offset: number; color: string }[]
  for (const r of ranges) {
    colorStops.push({ offset: (r.min - min) / (max - min), color: r.color })
  }
  colorStops.push({ offset: 1, color: ranges[ranges.length - 1]?.color || '#10b981' })
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'gauge',
      center: ['50%', '62%'],
      radius: '90%',
      min, max,
      progress: { show: true, width: thickness, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops } } },
      axisLine: { lineStyle: { width: thickness, color: [[1, '#E6EBF8']] } },
      pointer: { show: true, width: 4, length: '70%' },
      title: { show: true, offsetCenter: [0, '18%'], color: '#6b7280' },
      detail: { show: props.showValue !== false, valueAnimation: true, offsetCenter: [0, '40%'], fontSize: 24, fontWeight: 'bold', formatter: (v:number)=> v.toLocaleString() },
      data: [{ value: props.value, name: props.title || '' }]
    }]
  }
})
</script>

<template>
  <VChart :option="option" :style="{ height: `${resolvedHeight}px` }" autoresize class="w-full" />
  
</template>


