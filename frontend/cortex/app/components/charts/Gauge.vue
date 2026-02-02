<script setup lang="ts">
import { computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { useChartTheme } from '~/composables/useChartTheme'
import { getShadcnTooltipConfig } from '~/config/echartShadCNTooltip'

const props = defineProps<{
  value: number
  min?: number
  max?: number
  thickness?: number
  colorRanges?: Array<{ min: number; max: number; color: string }>
  showValue?: boolean
  showTarget?: boolean
  targetValue?: number
  gaugeType?: string
  height?: number
  title?: string
  showLegend?: boolean
  showGrid?: boolean
  showAxesLabels?: boolean
}>()

const { width } = useWindowSize()
const { chartTheme } = useChartTheme()

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
  const gaugeType = props.gaugeType ?? 'arc'

  // Build progress color configuration
  const progressItemStyle: any = {}
  if (props.colorRanges && props.colorRanges.length > 0) {
    // If colorRanges provided, create gradient from them
    const colorStops = [] as { offset: number; color: string }[]
    for (const r of props.colorRanges) {
      colorStops.push({ offset: (r.min - min) / (max - min), color: r.color })
    }
    colorStops.push({ offset: 1, color: props.colorRanges[props.colorRanges.length - 1]?.color || '#10b981' })

    progressItemStyle.color = {
      type: 'linear',
      x: 0, y: 0, x2: 1, y2: 0,
      colorStops
    }
  }
  // Otherwise let theme handle the color

  // Base gauge configuration
  const baseConfig: any = {
    tooltip: {
      ...getShadcnTooltipConfig({
        categorySize: 1
      }),
      trigger: 'item',
      formatter: (params: any) => {
        const value = params.value || 0
        const name = params.name || ''
        const marker = params.marker || ''
        return `
          <div style="min-width: 180px; font-family: 'Geist Mono', monospace;">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                ${marker}
                <span style="color: hsl(215, 16%, 47%);">${name}</span>
              </div>
              <span style="font-weight: 600; color: inherit;">${value.toLocaleString()}</span>
            </div>
          </div>
        `
      }
    },
    legend: { show: props.showLegend !== false },
    grid: { show: props.showGrid !== false },
    series: [{
      type: 'gauge',
      center: ['50%', '62%'],
      radius: '90%',
      min, max,
      progress: {
        show: true,
        width: thickness,
        itemStyle: progressItemStyle
      },
      axisLine: {
        lineStyle: {
          width: thickness
        }
      },
      axisTick: {
        show: props.showAxesLabels !== false,
        length: 8,
        lineStyle: { width: 2 }
      },
      splitLine: {
        show: props.showGrid !== false,
        length: 30,
        lineStyle: { width: 3 }
      },
      axisLabel: {
        show: props.showAxesLabels !== false,
        distance: 5,
        fontSize: 12
      },
      pointer: { show: true, width: 4, length: '70%' },
      title: {
        show: true,
        offsetCenter: [0, '18%'],
        fontSize: 14
      },
      detail: {
        show: props.showValue !== false,
        valueAnimation: true,
        offsetCenter: [0, '40%'],
        fontSize: 24,
        fontWeight: 'bold',
        formatter: (v:number)=> v.toLocaleString()
      },
      data: [{ value: props.value, name: props.title || '' }]
    }]
  }

  // Add target line if target value is provided and showTarget is true
  if (props.showTarget !== false && typeof props.targetValue === 'number') {
    baseConfig.series[0].markLine = {
      silent: true,
      symbol: 'none',
      lineStyle: { width: 2, type: 'dashed' },
      data: [{ yAxis: props.targetValue }]
    }
  }

  return baseConfig
})
</script>

<template>
  <VChart :option="option" :theme="chartTheme" :style="{ height: `${resolvedHeight}px` }" autoresize class="w-full min-h-[24rem]" />
  
</template>


