<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import LineChart from './LineChart.vue'
import BarChart from './BarChart.vue'
import AreaChart from './AreaChart.vue'
import DonutChart from './DonutChart.vue'
import StackedBarChart from './StackedBarChart.vue'
import StackedLineChart from './StackedLineChart.vue'
import NormalStackedArea from './NormalStackedArea.vue'
import GradientStackedArea from './GradientStackedArea.vue'

// Define props
const props = defineProps<{
  data: Record<string, any>[]
}>()

// State
const chartType = ref('bar')
const xAxisKey = ref<string>('')
const yAxisKey = ref<string>('')
const useStacked = ref(false)
const useDataZoom = ref(false)

const chartTypes = [
  { value: 'bar', label: 'Bar Chart' },
  { value: 'line', label: 'Line Chart' },
  { value: 'area', label: 'Area Chart' },
  { value: 'donut', label: 'Donut Chart' },
]

// Computed properties for keys
const availableKeys = computed(() => {
  if (props.data.length === 0) return []
  const firstRow = props.data[0]
  return firstRow ? Object.keys(firstRow) : []
})

const numericKeys = computed(() => {
  if (props.data.length === 0) return []
  const firstRow = props.data[0]
  if (!firstRow) return []
  return Object.keys(firstRow).filter(key => typeof firstRow[key] === 'number' || !isNaN(Number(firstRow[key])))
})

// Initialize default keys
const setDefaultKeys = () => {
  if (availableKeys.value.length > 0 && !xAxisKey.value) {
    xAxisKey.value = availableKeys.value.find(k => typeof props.data[0]?.[k] === 'string' || k.toLowerCase().includes('date') || k.toLowerCase().includes('name')) || availableKeys.value[0] || ''
  }
  if (numericKeys.value.length > 0 && !yAxisKey.value) {
    yAxisKey.value = numericKeys.value[0] || ''
  }
}

watch(() => props.data, setDefaultKeys, { immediate: true })

// Check if chart can be rendered
const canRenderChart = computed(() => {
  return props.data.length > 0 && xAxisKey.value && yAxisKey.value
})

// Prepare data for nuxt-charts format
const chartData = computed(() => {
  if (!canRenderChart.value) return []
  return props.data.map((item, index) => ({
    [xAxisKey.value]: item[xAxisKey.value],
    [yAxisKey.value]: Number(item[yAxisKey.value]) || 0,
    index
  }))
})

// Prepare categories for nuxt-charts
const categories = computed(() => {
  if (!yAxisKey.value) return {}
  const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#8b5cf6', '#d946ef']
  return {
    [yAxisKey.value]: {
      name: yAxisKey.value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      color: colors[0] || '#3b82f6'
    }
  }
})

// X-axis formatter
const xFormatter = (i: number): string | number => {
  return chartData.value[i]?.[xAxisKey.value] || ''
}

// Y-axis formatter
const yFormatter = (i: number): string | number => {
  return i
}

// Specific computed props for Donut Chart
const donutChartData = computed(() => {
  if (!canRenderChart.value) return []
  return props.data.map(item => Number(item[yAxisKey.value]) || 0)
})

const donutChartLabels = computed(() => {
  if (!canRenderChart.value) return []
  const colors = ['#3b82f6', '#ef4444', '#22c55e', '#f97316', '#8b5cf6', '#d946ef']
  return props.data.map((item, index) => ({
    name: String(item[xAxisKey.value]),
    color: colors[index % colors.length] || '#8884d8',
  }))
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Execution Result Chart</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
        <!-- Chart Type -->
        <div class="space-y-2">
          <Label for="chart-type">Chart Type</Label>
          <Select v-model="chartType">
            <SelectTrigger>
              <SelectValue placeholder="Select chart type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="type in chartTypes" :key="type.value" :value="type.value">
                {{ type.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Stacked Toggle -->
        <div class="space-y-2">
          <Label for="stacked-toggle">Stacked</Label>
          <div class="flex items-center space-x-2">
            <input
              id="stacked-toggle"
              type="checkbox"
              v-model="useStacked"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-600">Enable stacking</span>
          </div>
        </div>

        <!-- Data Zoom Toggle -->
        <div class="space-y-2">
          <Label for="data-zoom-toggle">Data Zoom & Toolbox</Label>
          <div class="flex items-center space-x-2">
            <input
              id="data-zoom-toggle"
              type="checkbox"
              v-model="useDataZoom"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-600">Enable zoom controls & toolbox</span>
          </div>
          <p class="text-xs text-muted-foreground">
            Adds zoom sliders and toolbox with zoom/restore/save features
          </p>
        </div>

        <!-- X-Axis (Labels) -->
        <div class="space-y-2">
          <Label for="x-axis">X-Axis (Labels)</Label>
          <Select v-model="xAxisKey">
            <SelectTrigger>
              <SelectValue placeholder="Select label field" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="key in availableKeys" :key="key" :value="key">
                {{ key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Y-Axis (Data) -->
        <div class="space-y-2">
          <Label for="y-axis">Y-Axis (Data)</Label>
          <Select v-model="yAxisKey">
            <SelectTrigger>
              <SelectValue placeholder="Select data field" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="key in numericKeys" :key="key" :value="key">
                {{ key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <!-- Debug Information -->
      <div v-if="props.data.length > 0" class="mb-4 p-3 bg-muted rounded-lg text-xs">
        <p><strong>Debug Info:</strong></p>
        <p>Data rows: {{ props.data.length }}</p>
        <p>Available keys: {{ availableKeys.join(', ') }}</p>
        <p>Numeric keys: {{ numericKeys.join(', ') }}</p>
        <p>X-Axis: {{ xAxisKey || 'Not selected' }}</p>
        <p>Y-Axis: {{ yAxisKey || 'Not selected' }}</p>
        <p>Stacked: {{ useStacked ? 'Yes' : 'No' }}</p>
        <p>Data Zoom & Toolbox: {{ useDataZoom ? 'Enabled' : 'Disabled' }}</p>
        <p>Can render: {{ canRenderChart }}</p>
      </div>

      <div class="mt-6">
        <div v-if="canRenderChart" class="h-96">
          <!-- Line Chart -->
          <LineChart
            v-if="chartType === 'line' && !useStacked"
            :data="chartData"
            :height="384"
            :y-label="yAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :categories="categories"
            :x-formatter="xFormatter"
            :y-num-ticks="4"
            :x-num-ticks="7"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Stacked Line Chart -->
          <StackedLineChart
            v-else-if="chartType === 'line' && useStacked"
            :data="chartData"
            :height="384"
            :y-label="yAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :categories="categories"
            :x-formatter="xFormatter"
            :y-num-ticks="4"
            :x-num-ticks="7"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Bar Chart -->
          <BarChart
            v-else-if="chartType === 'bar' && !useStacked"
            :data="chartData"
            :height="384"
            :categories="categories"
            :y-axis="[yAxisKey]"
            :x-formatter="xFormatter"
            :y-formatter="yFormatter"
            :x-num-ticks="7"
            :radius="4"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Stacked Bar Chart -->
          <StackedBarChart
            v-else-if="chartType === 'bar' && useStacked"
            :data="chartData"
            :height="384"
            :categories="categories"
            :y-axis="[yAxisKey]"
            :x-formatter="xFormatter"
            :y-formatter="yFormatter"
            :x-num-ticks="7"
            :radius="4"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Area Chart -->
          <AreaChart
            v-else-if="chartType === 'area' && !useStacked"
            :data="chartData"
            :height="384"
            :x-label="xAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :y-label="yAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :categories="categories"
            :x-formatter="xFormatter"
            :y-num-ticks="4"
            :x-num-ticks="7"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Stacked Area Chart -->
          <NormalStackedArea
            v-else-if="chartType === 'area' && useStacked"
            :data="chartData"
            :height="384"
            :x-label="xAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :y-label="yAxisKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())"
            :categories="categories"
            :x-formatter="xFormatter"
            :y-num-ticks="4"
            :x-num-ticks="7"
            :y-grid-line="true"
            :legend-position="'top'"
            :hide-legend="false"
            :data-zoom="useDataZoom"
          />
          <!-- Donut Chart -->
          <DonutChart
            v-else-if="chartType === 'donut'"
            :data="donutChartData"
            :height="384"
            :radius="0"
            :labels="donutChartLabels"
            :hide-legend="false"
          />
        </div>
        <div v-else class="flex h-96 items-center justify-center text-muted-foreground">
          <p>
            {{ props.data.length === 0 ? 'No data available for charting.' : 'Please select valid X and Y axis fields.' }}
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
</template> 