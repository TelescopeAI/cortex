<script setup lang="ts">
import { computed, ref } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { 
  MoreHorizontal, RefreshCw, Edit, Trash2, Settings, 
  TrendingUp, AlertTriangle, Clock, Loader2 
} from 'lucide-vue-next'
import type { DashboardWidget as WidgetType, VisualizationType } from '~/types/dashboards'
import ChartWidget from '~/components/dashboards/charts/ChartWidget.vue'
import SingleValueWidget from '~/components/dashboards/charts/SingleValueWidget.vue'
import GaugeWidget from '~/components/dashboards/charts/GaugeWidget.vue'
import TableWidget from '~/components/dashboards/charts/TableWidget.vue'
import { toast } from 'vue-sonner'

interface Props {
  widget: WidgetType
  executionResult?: any
  dashboardId?: string
  viewAlias?: string
}

interface Emits {
  (e: 'execute'): void
  (e: 'updated'): void
  (e: 'edit', widget: WidgetType): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const isExecuting = ref(false)

// Computed
const widgetTitle = computed(() => {
  return props.widget.title || 'Untitled Widget'
})

const hasData = computed(() => {
  return props.executionResult && !props.executionResult.error
})

const hasError = computed(() => {
  return props.executionResult?.error
})

const isLoading = computed(() => {
  return isExecuting.value || (!props.executionResult && !hasError.value)
})

const visualizationType = computed(() => {
  return props.widget.visualization.type
})

const executionTime = computed(() => {
  return props.executionResult?.execution_time_ms
})

// Methods
async function executeWidget() {
  isExecuting.value = true
  try {
    emit('execute')
  } finally {
    // Don't set to false immediately, let the parent handle the result
    setTimeout(() => {
      isExecuting.value = false
    }, 500)
  }
}

function editWidget() {
  emit('edit', props.widget)
}

function deleteWidget() {
  // TODO: Implement delete widget functionality
  toast.info('Delete widget functionality coming soon')
}

function configureWidget() {
  // TODO: Implement widget configuration
  toast.info('Widget configuration coming soon')
}

function getVisualizationComponent() {
  switch (visualizationType.value) {
    case 'single_value':
      return SingleValueWidget
    case 'gauge':
      return GaugeWidget
    case 'table':
      return TableWidget
    case 'bar_chart':
    case 'line_chart':
    case 'area_chart':
    case 'pie_chart':
    case 'donut_chart':
    case 'scatter_plot':
    case 'heatmap':
      return ChartWidget
    default:
      return ChartWidget
  }
}

function getVisualizationIcon() {
  switch (visualizationType.value) {
    case 'single_value':
      return TrendingUp
    case 'gauge':
      return 'Gauge' // Custom icon
    default:
      return 'BarChart'
  }
}
</script>

<template>
  <Card class="h-full flex flex-col">
    <!-- Widget Header -->
    <CardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex-1">
          <CardTitle class="text-base font-medium">{{ widgetTitle }}</CardTitle>
          <p v-if="widget.description" class="text-xs text-muted-foreground mt-1">
            {{ widget.description }}
          </p>
        </div>
        
        <div class="flex items-center gap-1">
          <!-- Drag-anywhere mode enabled; keep icon as visual affordance only -->
          <span class="h-6 w-6 rounded hover:bg-muted flex items-center justify-center text-muted-foreground" title="Drag">
            <span class="block w-3 h-3 m-auto bg-[linear-gradient(#999_2px,transparent_2px),linear-gradient(90deg,#999_2px,transparent_2px)] bg-[length:4px_4px]" />
          </span>
          <!-- Execution Status -->
          <Badge 
            v-if="executionTime" 
            variant="secondary" 
            class="text-xs"
          >
            {{ executionTime.toFixed(0) }}ms
          </Badge>
          
          <!-- Execute Button -->
          <Button 
            variant="ghost" 
            size="icon" 
            class="h-6 w-6"
            draggable="false"
            @mousedown.stop
            @pointerdown.stop
            @touchstart.stop
            @click="executeWidget"
            :disabled="isExecuting"
          >
            <RefreshCw :class="{ 'animate-spin': isExecuting, 'w-3 h-3': true }" />
          </Button>
          
          <!-- Widget Actions -->
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button 
                variant="ghost" 
                size="icon" 
                class="h-6 w-6"
                draggable="false"
                @mousedown.stop
                @pointerdown.stop
                @touchstart.stop
                @click.stop
              >
                <MoreHorizontal class="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="z-[9999]">
              <DropdownMenuItem @click="editWidget">
                <Edit class="w-4 h-4 mr-2" />
                Edit Widget
              </DropdownMenuItem>
              <DropdownMenuItem @click="configureWidget">
                <Settings class="w-4 h-4 mr-2" />
                Configure
              </DropdownMenuItem>
              <DropdownMenuItem @click="deleteWidget" class="text-destructive">
                <Trash2 class="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </CardHeader>

    <!-- Widget Content -->
    <CardContent class="flex-1 pb-4 card-content-bg">
      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center h-32">
        <div class="text-center">
          <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2 text-muted-foreground" />
          <p class="text-sm text-muted-foreground">Loading data...</p>
        </div>
      </div>

      <!-- Error State -->
      <Alert v-else-if="hasError" variant="destructive" class="h-32 flex items-center">
        <AlertTriangle class="h-4 w-4" />
        <AlertDescription class="ml-2">
          <div class="font-medium">Execution Failed</div>
          <div class="text-xs mt-1">{{ executionResult.error }}</div>
        </AlertDescription>
      </Alert>

      <!-- No Data State -->
      <div v-else-if="!hasData" class="flex items-center justify-center h-32">
        <div class="text-center">
          <div class="w-8 h-8 mx-auto mb-2 bg-muted rounded flex items-center justify-center">
            <component :is="getVisualizationIcon()" class="w-4 h-4 text-muted-foreground" />
          </div>
          <p class="text-sm text-muted-foreground">No data available</p>
          <Button variant="ghost" size="sm" @click="executeWidget" class="mt-2">
            <RefreshCw class="w-3 h-3 mr-1" />
            Execute
          </Button>
        </div>
      </div>

      <!-- Widget Visualization -->
      <component
        v-else
        :is="getVisualizationComponent()"
        :widget="widget"
        :data="executionResult.data"
        :execution-result="executionResult"
        class="h-full"
      />
    </CardContent>
  </Card>
</template>