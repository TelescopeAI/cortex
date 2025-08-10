<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardWidget, StandardChartData } from '~/types/dashboards'

interface Props {
  widget: DashboardWidget
  data: StandardChartData
  executionResult?: any
}

const props = defineProps<Props>()

// Computed values
const gaugeConfig = computed(() => {
  return props.widget.visualization.gauge_config
})

const value = computed(() => {
  const rawValue = props.data.processed.value
  return typeof rawValue === 'number' ? rawValue : parseFloat(rawValue) || 0
})

const minValue = computed(() => {
  return gaugeConfig.value?.min_value ?? 0
})

const maxValue = computed(() => {
  return gaugeConfig.value?.max_value ?? 100
})

const targetValue = computed(() => {
  return gaugeConfig.value?.target_value
})

const showValue = computed(() => {
  return gaugeConfig.value?.show_value !== false
})

const showTarget = computed(() => {
  return gaugeConfig.value?.show_target !== false && targetValue.value !== undefined
})

// Chart option for gauge
const chartOption = computed(() => {
  const config = gaugeConfig.value
  const colorRanges = config?.color_ranges || [
    { min: 0, max: 30, color: '#ef4444' },
    { min: 30, max: 70, color: '#f97316' },
    { min: 70, max: 100, color: '#10b981' }
  ]

  // Create color stops for the gauge
  const colorStops = colorRanges.map((range, index) => ({
    offset: (range.min - minValue.value) / (maxValue.value - minValue.value),
    color: range.color
  }))

  // Add the last color stop
  if (colorRanges.length > 0) {
    const lastRange = colorRanges[colorRanges.length - 1]!
    colorStops.push({
      offset: (lastRange.max - minValue.value) / (maxValue.value - minValue.value),
      color: lastRange.color
    })
  }

  return {
    series: [
      {
        name: props.widget.title || 'Gauge',
        type: 'gauge',
        center: ['50%', '60%'],
        radius: '80%',
        min: minValue.value,
        max: maxValue.value,
        splitNumber: 5,
        progress: {
          show: true,
          width: config?.thickness || 10,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: colorStops
            }
          }
        },
        pointer: {
          show: true,
          width: 4,
          length: '70%',
          itemStyle: {
            color: '#464646'
          }
        },
        axisLine: {
          lineStyle: {
            width: config?.thickness || 10,
            color: [[1, '#E6EBF8']]
          }
        },
        axisTick: {
          distance: -15,
          splitNumber: 5,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        splitLine: {
          distance: -20,
          length: 5,
          lineStyle: {
            width: 2,
            color: '#999'
          }
        },
        axisLabel: {
          color: '#464646',
          fontSize: 12,
          distance: -35,
          formatter: (value: number) => {
            if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
            if (value >= 1000) return (value / 1000).toFixed(1) + 'K'
            return value.toString()
          }
        },
        title: {
          show: showValue.value,
          offsetCenter: [0, '20%'],
          fontSize: 16,
          fontWeight: 'bold',
          color: '#464646'
        },
        detail: {
          show: showValue.value,
          offsetCenter: [0, '40%'],
          fontSize: 20,
          fontWeight: 'bold',
          color: '#464646',
          formatter: (value: number) => {
            // Use the same formatting as single value widget
            const config = props.widget.visualization.single_value_config
            if (config?.number_format === 'percentage') {
              return value.toFixed(1) + '%'
            } else if (config?.number_format === 'currency') {
              return new Intl.NumberFormat(undefined, { 
                style: 'currency', 
                currency: 'USD' 
              }).format(value)
            }
            return value.toLocaleString()
          }
        },
        data: [
          {
            value: value.value,
            name: props.widget.title || 'Value'
          }
        ]
      }
    ]
  }
})

// Target indicator option (separate series if target is shown)
const targetOption = computed(() => {
  if (!showTarget.value || !targetValue.value) return null

  return {
    series: [
      {
        name: 'Target',
        type: 'gauge',
        center: ['50%', '60%'],
        radius: '85%',
        min: minValue.value,
        max: maxValue.value,
        splitNumber: 0,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: { show: false },
        detail: { show: false },
        pointer: { show: false },
        markLine: {
          data: [
            {
              name: 'Target',
              yAxis: targetValue.value,
              lineStyle: { color: '#ff6b6b', width: 3, type: 'dashed' },
              label: { show: true, position: 'end', formatter: 'Target: {c}', color: '#ff6b6b' }
            }
          ]
        },
        data: []
      }
    ]
  }
})

// Combined options
const finalOption = computed(() => {
  const base = chartOption.value
  if (targetOption.value) {
    return { ...base, series: [...base.series, ...targetOption.value.series] }
  }
  return base
})
</script>

<template>
  <div class="h-full min-h-[200px] flex flex-col">
    <!-- Gauge Chart -->
    <div class="flex-1">
      <VChart :option="finalOption" autoresize class="h-full w-full" />
    </div>

    <!-- Target Information -->
    <div v-if="showTarget && targetValue" class="text-center pt-2 border-t border-border">
      <div class="text-xs text-muted-foreground">
        Target: <span class="font-medium">{{ targetValue.toLocaleString() }}</span>
        <span :class="['ml-2', value >= targetValue ? 'text-green-600' : 'text-red-600']">
          {{ value >= targetValue ? '✓' : '✗' }}
          {{ ((value / targetValue) * 100).toFixed(1) }}%
        </span>
      </div>
    </div>
  </div>
</template>