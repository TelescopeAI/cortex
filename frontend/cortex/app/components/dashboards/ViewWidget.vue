<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { useDashboards } from '~/composables/useDashboards'
import ChartRenderer from './ChartRenderer.vue'
import { Toggle } from '@/components/ui/toggle'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { toast } from 'vue-sonner'

interface Props {
  dashboardId: string
  viewAlias: string
  widget: any
  refreshKey?: number
}

interface Emits {
  (e: 'edit', widget: any): void
  (e: 'deleted'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { executeWidget, deleteWidget } = useDashboards()

const loading = ref(true)
const error = ref<string | null>(null)
const data = ref<any | null>(null)
const dataZoom = ref(false)
const deleteDialogOpen = ref(false)
const deleting = ref(false)

async function load() {
  try {
    loading.value = true
    error.value = null
    data.value = null
    const res = await executeWidget(props.dashboardId, props.viewAlias, props.widget.alias)
    data.value = (res as any)?.data || null
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to load widget'
  } finally {
    loading.value = false
  }
}

function refreshData() {
  load()
}

function editWidget() {
  emit('edit', props.widget)
}

async function handleDeleteWidget() {
  try {
    deleting.value = true
    await deleteWidget(props.dashboardId, props.viewAlias, props.widget.alias)
    deleteDialogOpen.value = false
    
    // Show success toast
    toast.success('Widget deleted successfully')
    
    // Emit deleted event to refresh dashboard config
    emit('deleted')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Failed to delete widget'
    toast.error('Failed to delete widget')
  } finally {
    deleting.value = false
  }
}

// Determine if current chart type supports data zoom
const is2DChart = computed(() => {
  const chartType = props.widget?.visualization?.type
  return ['line_chart', 'bar_chart', 'area_chart', 'scatter_plot'].includes(chartType)
})

onMounted(load)
watch(() => [props.dashboardId, props.viewAlias, props.widget?.alias], load)
// Refresh when the parent increments the refreshKey
watch(() => props.refreshKey, () => load())
</script>

<template>
  <div class="w-full h-full flex flex-col border border-slate-200 rounded-md shadow">
    <!-- Widget Header -->
    <div class="flex items-center justify-between p-3 border-b bg-muted/30">
      <div class="flex items-center space-x-2">
        <h3 class="font-medium text-sm">{{ widget.title || 'Untitled Widget' }}</h3>
      </div>
      
      <!-- Action Buttons -->
      <div class="flex items-center space-x-2">
        <!-- Data Zoom Toggle - Only show for 2D charts -->
        <Toggle
          v-if="is2DChart"
          v-model="dataZoom"
          class="p-1.5"
          title="Toggle data zoom"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </Toggle>

        <button
          @click="refreshData"
          :disabled="loading"
          class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-background rounded transition-colors"
          title="Refresh data"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <button
          @click="editWidget"
          class="p-1.5 text-muted-foreground hover:text-foreground hover:bg-background rounded transition-colors"
          title="Edit widget"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>

        <AlertDialog v-model:open="deleteDialogOpen">
          <AlertDialogTrigger as-child>
            <button
              class="p-1.5 text-muted-foreground hover:text-destructive hover:bg-background rounded transition-colors"
              title="Delete widget"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Widget</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{{ widget.title || 'Untitled Widget' }}"? 
                This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                @click="handleDeleteWidget"
                :disabled="deleting"
                class="bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
              >
                {{ deleting ? 'Deleting...' : 'Delete' }}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>

    <!-- Widget Content -->
    <div class="flex-1 p-4 card-content-bg rounded-b-md">
      <!-- Loading State -->
      <div v-if="loading" class="space-y-3">
        <div class="h-6 w-32 bg-muted rounded animate-pulse" />
        <div class="h-64 w-full bg-muted rounded animate-pulse" />
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="flex flex-col items-center justify-center h-full space-y-4 text-center">
        <div class="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center">
          <svg class="w-8 h-8 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        
        <div class="space-y-2">
          <h4 class="font-medium text-destructive">Failed to load widget</h4>
          <p class="text-sm text-muted-foreground max-w-xs">{{ error }}</p>
        </div>
        
        <div class="flex space-x-2">
          <button
            @click="refreshData"
            class="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
          <button
            @click="editWidget"
            class="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded hover:bg-secondary/90 transition-colors"
          >
            Edit Widget
          </button>
        </div>
      </div>
      
      <!-- Success State -->
      <ChartRenderer
        v-else
        :processed="data?.processed"
        :metadata="data?.metadata"
        :type="widget.visualization.type"
        :gauge-config="widget.visualization.gauge_config"
        :single-value-config="widget.visualization.single_value_config"
        :chart-config="widget.visualization.chart_config"
        :error="data?.metadata?.title === 'Error' ? (data?.metadata?.description || 'Failed to render') : null"
        :data-zoom="dataZoom"
      />
    </div>
  </div>
</template>


