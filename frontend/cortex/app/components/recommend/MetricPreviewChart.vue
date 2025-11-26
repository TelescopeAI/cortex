<script setup lang="ts">
import { ref, watch } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import { AlertCircle } from 'lucide-vue-next'
import PreviewWidgetViz from '~/components/dashboards/PreviewWidgetViz.vue'
import { useDashboards, generateWidgetConfigFromMetric } from '~/composables/useDashboards'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  metric: SemanticMetric
  expanded?: boolean
}

const props = defineProps<Props>()

const { previewDashboardConfig, fetchDashboards, dashboards } = useDashboards()
const { selectedEnvironmentId } = useEnvironments()

const previewData = ref<any>(null)
const previewLoading = ref(false)
const previewError = ref<string | null>(null)
const dashboardId = ref<string | null>(null)
const visualizationType = ref<string>('single_value')
const containerRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const hasLoaded = ref(false)  // Track if we've already loaded to avoid re-fetching

// Use Intersection Observer to detect when component is visible
const { stop } = useIntersectionObserver(
  containerRef,
  ([entry]) => {
    isVisible.value = entry?.isIntersecting || false
    
    // Load preview when visible for the first time
    if (isVisible.value && !hasLoaded.value && props.expanded) {
      hasLoaded.value = true
      loadPreview(props.metric)
    }
  },
  { threshold: 0.1 }  // Trigger when 10% of the element is visible
)

// Fetch first available dashboard for preview
async function ensureDashboardId(): Promise<string | null> {
  if (dashboardId.value) return dashboardId.value
  
  if (!selectedEnvironmentId.value) {
    previewError.value = 'No environment selected'
    return null
  }
  
  try {
    // Fetch dashboards if not already loaded
    if (dashboards.value.length === 0) {
      await fetchDashboards(selectedEnvironmentId.value)
    }
    
    // Use the first available dashboard
    const firstDashboard = dashboards.value[0]
    if (firstDashboard) {
      dashboardId.value = firstDashboard.id
      return dashboardId.value
    } else {
      previewError.value = 'No dashboards available for preview. Please create a dashboard first.'
      return null
    }
  } catch (error) {
    console.error('Failed to fetch dashboards:', error)
    previewError.value = 'Failed to load dashboards for preview'
    return null
  }
}

// Generate widget config and load preview
async function loadPreview(metric: SemanticMetric) {
  previewLoading.value = true
  previewError.value = null
  
  try {
    // Ensure we have a valid dashboard ID
    const validDashboardId = await ensureDashboardId()
    if (!validDashboardId) {
      previewLoading.value = false
      return
    }
    
    // Generate widget config from metric
    const widgetConfig = generateWidgetConfigFromMetric(metric)
    
    // Store the visualization type for rendering
    visualizationType.value = widgetConfig.visualization?.type || 'single_value'
    
    // Create a mock dashboard configuration for preview
    const previewConfig = {
      views: [{
        alias: 'preview_view',
        sections: [{
          alias: 'preview_section',
          position: 0,
          widgets: [{
            alias: 'preview_widget',
            section_alias: 'preview_section',
            metric: metric,  // Pass the full embedded metric object
            title: metric.title || metric.name || 'Preview',
            description: metric.description,
            position: 0,
            grid_config: {
              columns: widgetConfig.grid_config?.columns || 4,
              rows: widgetConfig.grid_config?.rows || 2,
              min_columns: widgetConfig.grid_config?.min_columns || 1,
              min_rows: widgetConfig.grid_config?.min_rows || 1
            },
            visualization: {
              type: widgetConfig.visualization?.type || 'single_value',
              data_mapping: widgetConfig.visualization?.data_mapping || {},
              show_legend: widgetConfig.visualization?.show_legend ?? true,
              show_grid: widgetConfig.visualization?.show_grid ?? true,
              show_axes_labels: widgetConfig.visualization?.show_axes_labels ?? true
            }
          }]
        }]
      }]
    }
    
    // Call preview API with valid dashboard ID
    const result = await previewDashboardConfig(validDashboardId, previewConfig)
    previewData.value = result.view_execution?.widgets?.[0]?.data
    
  } catch (error) {
    console.error('Preview error:', error)
    previewError.value = error instanceof Error ? error.message : 'Failed to generate preview'
  } finally {
    previewLoading.value = false
  }
}

// Reset and reload when metric changes
watch(() => props.metric, (newMetric, oldMetric) => {
  if (newMetric && oldMetric && newMetric.name !== oldMetric.name) {
    // Reset state for new metric
    hasLoaded.value = false
    previewData.value = null
    previewError.value = null
    
    // If already visible, load immediately
    if (isVisible.value && props.expanded) {
      hasLoaded.value = true
      loadPreview(newMetric)
    }
  }
}, { deep: true })
</script>

<template>
  <div v-if="expanded" ref="containerRef" class="h-full">
    <!-- Loading State -->
    <div v-if="previewLoading" class="flex items-center justify-center h-full min-h-[200px]">
      <div class="text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
        <p class="text-sm text-muted-foreground">Generating preview...</p>
      </div>
    </div>
    
    <!-- Error State (from previewError or from API response metadata) -->
    <div v-else-if="previewError || previewData?.metadata?.title === 'Error'" class="flex items-center justify-center h-full min-h-[200px] bg-muted/20 rounded-lg">
      <div class="text-center px-4">
        <AlertCircle class="w-6 h-6 text-muted-foreground mx-auto mb-2" />
        <p class="text-sm text-muted-foreground">Preview unavailable</p>
        <p class="text-xs text-muted-foreground/70 mt-1">Add the metric to see details</p>
      </div>
    </div>
    
    <!-- Chart Preview -->
    <div v-else-if="previewData" class="h-full min-h-[200px]">
      <PreviewWidgetViz 
        :type="visualizationType"
        :data="previewData"
        :loading="previewLoading"
        :error="previewError"
      />
    </div>
    
    <!-- Waiting to load (not yet visible) -->
    <div v-else-if="!hasLoaded" class="flex items-center justify-center h-full min-h-[200px] bg-muted/30 rounded-lg border border-dashed">
      <p class="text-sm text-muted-foreground">Scroll to load preview</p>
    </div>
    
    <!-- No Data State -->
    <div v-else class="flex items-center justify-center h-full min-h-[200px]">
      <p class="text-sm text-muted-foreground">No preview available</p>
    </div>
  </div>
</template>

