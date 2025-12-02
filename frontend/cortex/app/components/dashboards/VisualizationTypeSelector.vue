<script setup lang="ts">
import { computed } from 'vue'
import { Button } from '~/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator } from '~/components/ui/dropdown-menu'
import { Badge } from '~/components/ui/badge'
import { 
  BarChart3, LineChart, AreaChart, PieChart, 
  Gauge, TrendingUp, Activity, Box, Table,
  Info, CheckCircle, AlertTriangle
} from 'lucide-vue-next'

interface Props {
  modelValue: string
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Visualization type definitions with helpful descriptions
const visualizationTypes = [
  {
    value: 'single_value',
    label: 'Single Value',
    icon: TrendingUp,
    description: 'Display a single number with optional formatting',
    useCase: 'KPIs, totals, averages',
    dataType: 'Numerical',
    color: 'bg-blue-100 text-blue-800'
  },
  {
    value: 'gauge',
    label: 'Gauge',
    icon: Gauge,
    description: 'Circular progress indicator with target',
    useCase: 'Performance metrics, completion rates',
    dataType: 'Numerical',
    color: 'bg-purple-100 text-purple-800'
  },
  {
    value: 'bar_chart',
    label: 'Bar Chart',
    icon: BarChart3,
    description: 'Compare values across categories',
    useCase: 'Sales by region, product performance',
    dataType: 'Categorical X-axis',
    color: 'bg-green-100 text-green-800',
    warning: 'Use for categorical data (names, categories)'
  },
  {
    value: 'line_chart',
    label: 'Line Chart',
    icon: LineChart,
    description: 'Show trends over time or continuous data',
    useCase: 'Time series, trends, continuous metrics',
    dataType: 'Continuous X-axis',
    color: 'bg-orange-100 text-orange-800',
    warning: 'Use for time series or continuous data'
  },
  {
    value: 'area_chart',
    label: 'Area Chart',
    icon: AreaChart,
    description: 'Show cumulative values over time',
    useCase: 'Revenue over time, cumulative metrics',
    dataType: 'Continuous X-axis',
    color: 'bg-cyan-100 text-cyan-800',
    warning: 'Use for time series or continuous data'
  },
  {
    value: 'pie_chart',
    label: 'Pie Chart',
    icon: PieChart,
    description: 'Show parts of a whole',
    useCase: 'Market share, budget allocation',
    dataType: 'Categorical',
    color: 'bg-pink-100 text-pink-800'
  },
  {
    value: 'donut_chart',
    label: 'Donut Chart',
    icon: PieChart,
    description: 'Show parts of a whole with center space',
    useCase: 'Market share, budget allocation',
    dataType: 'Categorical',
    color: 'bg-rose-100 text-rose-800'
  },
  {
    value: 'scatter_plot',
    label: 'Scatter Plot',
    icon: Activity,
    description: 'Show relationship between two variables',
    useCase: 'Correlation analysis, data distribution',
    dataType: 'Numerical X & Y',
    color: 'bg-indigo-100 text-indigo-800'
  },
  {
    value: 'box_plot',
    label: 'Box Plot',
    icon: Box,
    description: 'Show data distribution and outliers',
    useCase: 'Statistical analysis, data distribution',
    dataType: 'Numerical',
    color: 'bg-teal-100 text-teal-800'
  },
  {
    value: 'table',
    label: 'Table',
    icon: Table,
    description: 'Display detailed data in rows and columns',
    useCase: 'Detailed data, reports, comparisons',
    dataType: 'Any',
    color: 'bg-gray-100 text-gray-800'
  }
]

const selectedType = computed(() => {
  return visualizationTypes.find(type => type.value === props.modelValue)
})

function selectType(value: string) {
  emit('update:modelValue', value)
}

// Group types by category
const chartCategories = computed(() => {
  return {
    'Single Values': visualizationTypes.filter(t => ['single_value', 'gauge'].includes(t.value)),
    'Categorical Charts': visualizationTypes.filter(t => ['bar_chart', 'pie_chart', 'donut_chart'].includes(t.value)),
    'Time Series': visualizationTypes.filter(t => ['line_chart', 'area_chart'].includes(t.value)),
    'Analysis': visualizationTypes.filter(t => ['scatter_plot', 'box_plot'].includes(t.value)),
    'Data Display': visualizationTypes.filter(t => ['table'].includes(t.value))
  }
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button 
        variant="outline" 
        class="w-full justify-start"
        :disabled="disabled"
      >
        <component 
          :is="selectedType?.icon || BarChart3" 
          class="w-4 h-4 mr-2" 
        />
        <span class="flex-1 text-left">
          {{ selectedType?.label || 'Select visualization type' }}
        </span>
        <Badge 
          v-if="selectedType" 
          :class="selectedType.color"
          class="ml-2 text-xs"
        >
          {{ selectedType.dataType }}
        </Badge>
      </Button>
    </DropdownMenuTrigger>
    
    <DropdownMenuContent class="z-[100002]" align="start" :side-offset="4" :avoid-collisions="true">
      <div v-for="(types, category) in chartCategories" :key="category" class="p-1">
        <DropdownMenuLabel class="text-xs font-semibold text-muted-foreground mb-1 px-2">
          {{ category }}
        </DropdownMenuLabel>
        
        <DropdownMenuItem
          v-for="type in types"
          :key="type.value"
          @select="selectType(type.value)"
          class="flex items-center p-2 cursor-pointer"
        >
          <component :is="type.icon" class="w-4 h-4 mr-3 text-muted-foreground" />
          <div class="flex-1">
            <div class="font-medium text-sm">{{ type.label }}</div>
            <div class="text-xs text-muted-foreground">
              {{ type.useCase }}
            </div>
          </div>
          <Badge :class="type.color" class="text-xs ml-2">
            {{ type.dataType }}
          </Badge>
        </DropdownMenuItem>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
