<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-vue-next'
import type { DashboardWidget, StandardChartData } from '~/types/dashboards'

interface Props {
  widget: DashboardWidget
  data: StandardChartData
  executionResult?: any
}

const props = defineProps<Props>()

// Computed values
const singleValueConfig = computed(() => {
  return props.widget.visualization.single_value_config
})

const value = computed(() => {
  return props.data.processed.value
})

const formattedValue = computed(() => {
  if (value.value === null || value.value === undefined) return 'N/A'
  
  const config = singleValueConfig.value
  if (!config) return value.value.toString()
  
  let formatted = ''
  
  // Add prefix
  if (config.prefix) {
    formatted += config.prefix
  }
  
  // Format number
  const numValue = typeof value.value === 'number' ? value.value : parseFloat(value.value)
  
  switch (config.number_format) {
    case 'integer':
      formatted += Math.round(numValue).toLocaleString()
      break
    case 'decimal':
      formatted += numValue.toLocaleString(undefined, { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      })
      break
    case 'percentage':
      formatted += (numValue * 100).toLocaleString(undefined, { 
        minimumFractionDigits: 1, 
        maximumFractionDigits: 1 
      }) + '%'
      break
    case 'currency':
      formatted += new Intl.NumberFormat(undefined, { 
        style: 'currency', 
        currency: 'USD' 
      }).format(numValue)
      break
    case 'abbreviated':
      formatted += abbreviateNumber(numValue)
      break
    case 'scientific':
      formatted += numValue.toExponential(2)
      break
    default:
      formatted += numValue.toLocaleString()
  }
  
  // Add suffix
  if (config.suffix) {
    formatted += config.suffix
  }
  
  return formatted
})

const comparisonValue = computed(() => {
  // Mock comparison data - in real implementation this would come from the backend
  const mockComparison = {
    previous_value: typeof value.value === 'number' ? value.value * 0.9 : 0,
    change_percentage: 12.5,
    change_absolute: typeof value.value === 'number' ? value.value * 0.1 : 0
  }
  
  return mockComparison
})

const trendDirection = computed(() => {
  if (!comparisonValue.value) return 'neutral'
  return comparisonValue.value.change_percentage > 0 ? 'up' : 
         comparisonValue.value.change_percentage < 0 ? 'down' : 'neutral'
})

const trendIcon = computed(() => {
  switch (trendDirection.value) {
    case 'up': return TrendingUp
    case 'down': return TrendingDown
    default: return Minus
  }
})

const trendColor = computed(() => {
  switch (trendDirection.value) {
    case 'up': return 'text-green-600'
    case 'down': return 'text-red-600'
    default: return 'text-gray-600'
  }
})

const shouldShowComparison = computed(() => {
  return singleValueConfig.value?.show_comparison !== false && comparisonValue.value
})

const shouldShowTrend = computed(() => {
  return singleValueConfig.value?.show_trend !== false
})

const isCompactMode = computed(() => {
  return singleValueConfig.value?.compact_mode === true
})

// Helper functions
function abbreviateNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B'
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
  return num.toString()
}
</script>

<template>
  <div class="h-full flex items-center justify-center p-4">
    <div 
      :class="[
        'text-center w-full',
        isCompactMode ? 'space-y-1' : 'space-y-3'
      ]"
    >
      <!-- Title -->
      <div 
        v-if="singleValueConfig?.show_title !== false"
        :class="[
          'font-medium text-muted-foreground',
          isCompactMode ? 'text-xs' : 'text-sm'
        ]"
      >
        {{ widget.title || 'Value' }}
      </div>

      <!-- Main Value -->
      <div 
        :class="[
          'font-bold text-foreground',
          isCompactMode ? 'text-2xl' : 'text-4xl lg:text-5xl'
        ]"
      >
        {{ formattedValue }}
      </div>

      <!-- Description -->
      <div 
        v-if="singleValueConfig?.show_description !== false && widget.description"
        :class="[
          'text-muted-foreground',
          isCompactMode ? 'text-xs' : 'text-sm'
        ]"
      >
        {{ widget.description }}
      </div>

      <!-- Comparison and Trend -->
      <div 
        v-if="shouldShowComparison || shouldShowTrend"
        :class="[
          'flex items-center justify-center gap-2',
          isCompactMode ? 'text-xs' : 'text-sm'
        ]"
      >
        <!-- Trend Indicator -->
        <div 
          v-if="shouldShowTrend"
          :class="['flex items-center gap-1', trendColor]"
        >
          <component :is="trendIcon" :class="isCompactMode ? 'w-3 h-3' : 'w-4 h-4'" />
          <span class="font-medium">
            {{ Math.abs(comparisonValue.change_percentage).toFixed(1) }}%
          </span>
        </div>

        <!-- Comparison Badge -->
        <Badge 
          v-if="shouldShowComparison && !isCompactMode"
          :variant="trendDirection === 'up' ? 'default' : trendDirection === 'down' ? 'destructive' : 'secondary'"
          class="text-xs"
        >
          vs previous
        </Badge>
      </div>

      <!-- Sparkline placeholder -->
      <div 
        v-if="singleValueConfig?.show_sparkline && !isCompactMode"
        class="h-8 bg-muted/50 rounded flex items-center justify-center"
      >
        <span class="text-xs text-muted-foreground">Sparkline</span>
      </div>
    </div>
  </div>
</template>