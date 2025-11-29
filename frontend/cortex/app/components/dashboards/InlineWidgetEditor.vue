<script setup lang="ts">
import { ref, reactive, computed, watch, provide, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Badge } from '~/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Separator } from '~/components/ui/separator'
import { Select as UiSelect, SelectContent as UiSelectContent, SelectItem as UiSelectItem, SelectTrigger as UiSelectTrigger, SelectValue as UiSelectValue } from '~/components/ui/select'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { 
  X, Save, RefreshCw, AlertCircle, CheckCircle, 
  Sparkles, List, ChevronDown, ChevronUp,
  Eye, Settings, Plus
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import MetricSelector from '~/components/MetricSelector.vue'
import MetricSchemaBuilder from '~/components/metric-builder/MetricSchemaBuilder.vue'
import DataMappingEditor from './DataMappingEditor.vue'
import VisualizationTypeSelector from './VisualizationTypeSelector.vue'
import GridSizeSelector from './GridSizeSelector.vue'
import MetricRecommendations from './MetricRecommendations.vue'
import PreviewWidgetViz from './PreviewWidgetViz.vue'

import type { DashboardWidget } from '~/types/dashboards'
import type { SemanticMetric } from '~/composables/useMetrics'
import { useWidgetEditor } from '~/composables/useWidgetEditor'
import { useSchemaBuilder } from '~/composables/useSchemaBuilder'

interface Props {
  dashboardId: string
  sectionAlias: string
  viewAlias: string
  mode?: 'create' | 'edit'
  widget?: DashboardWidget | null
  metricsCount?: number
}

interface Emits {
  (e: 'cancel'): void
  (e: 'save', widget: Partial<DashboardWidget>): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  widget: null,
  metricsCount: 0
})

const emit = defineEmits<Emits>()

// Composables
const { selectedEnvironmentId } = useEnvironments()
const { dataSources, getDataSourceSchema } = useDataSources()

// Initialize widget editor
const editor = useWidgetEditor({
  dashboardId: props.dashboardId,
  mode: props.mode,
  initialWidget: props.widget
})

// Schema builder for metric creation
const schemaBuilder = useSchemaBuilder({})
provide('schemaBuilder', schemaBuilder)

// Local state
const isExpanded = ref(true)
const tableSchema = ref<any>(null)
const selectedDataSourceId = ref<string>('')

// Check if in edit mode
const isEditMode = computed(() => props.mode === 'edit')

// Collapsible sections config
// - Create mode: Recommendations open, Metric Definition closed (user picks recommendation first)
// - Edit mode: Both closed (user expands when needed)
const collapsibleSections = reactive({
  recommendations: {
    label: 'Recommendations',
    icon: Sparkles,
    isOpen: !isEditMode.value // Open in create mode, closed in edit mode
  },
  metricDefinition: {
    label: 'Metric',
    icon: Settings,
    isOpen: false // Always closed by default, user expands when needed
  },
  widgetSettings: {
    label: 'Widget Settings',
    icon: Settings,
    isOpen: true
  }
})

// Default tab - always start with "select" for simplicity
const activeMetricTab = ref<'select' | 'custom'>('select')

// Simplified 2-tab structure
const metricTabsOrder = computed(() => [
  { value: 'select', label: 'Select Metric', icon: List },
  { value: 'custom', label: 'New', icon: Plus }
])

// Watch for data source changes and fetch schema
watch(selectedDataSourceId, async (newId) => {
  if (newId) {
    try {
      const schema = await getDataSourceSchema(newId)
      tableSchema.value = schema
    } catch (err) {
      console.error('Failed to fetch schema:', err)
      tableSchema.value = null
    }
  } else {
    tableSchema.value = null
  }
})

// Watch schema builder changes to update available tables for data mapping
// This ensures embedded metric measures/dimensions are available in the widget config
watch(
  () => ({
    measures: schemaBuilder.schema.value.measures,
    dimensions: schemaBuilder.schema.value.dimensions,
    tableName: schemaBuilder.schema.value.table_name || schemaBuilder.schema.value.name
  }),
  ({ measures, dimensions, tableName }) => {
    // Only update if we're in custom metric mode
    if (activeMetricTab.value === 'custom') {
      const columns: { name: string; type: string }[] = []
      
      // Add dimensions
      ;(dimensions || []).forEach((d: any) => {
        columns.push({ name: d.name || d, type: d.type || 'dimension' })
      })
      
      // Add measures
      ;(measures || []).forEach((m: any) => {
        columns.push({ name: m.name || m, type: m.type || 'measure' })
      })
      
      if (columns.length > 0) {
        editor.availableTables.value = [{ 
          name: tableName || 'Custom Metric', 
          columns 
        }]
      }
    }
  },
  { deep: true }
)

// Handle metric selection from MetricSelector
function handleMetricSelect(metric: SemanticMetric) {
  editor.onMetricSelect(metric)
  // Auto-trigger preview after metric selection
  setTimeout(() => editor.updatePreview(), 100)
}

// Helper to prefill schema builder with metric data
function prefillSchemaBuilderWithMetric(metric: SemanticMetric, dataSourceId?: string, dataModelId?: string) {
  schemaBuilder.schema.value = {
    name: metric.name || '',
    alias: metric.alias || '',
    title: metric.title || '',
    description: metric.description || '',
    table_name: metric.table_name || '',
    query: metric.query || '',
    data_source_id: dataSourceId || metric.data_source_id || undefined,
    data_model_id: dataModelId || (metric as any).data_model_id || undefined,
    limit: metric.limit || undefined,
    grouped: metric.grouped ?? true,
    ordered: metric.ordered ?? true,
    measures: metric.measures ? [...metric.measures] : [],
    dimensions: metric.dimensions ? [...metric.dimensions] : [],
    joins: metric.joins ? [...metric.joins] : [],
    filters: metric.filters ? [...metric.filters] : [],
    order: metric.order ? [...metric.order] : [],
    parameters: metric.parameters || {},
    refresh: (metric as any).refresh || undefined,
    cache: (metric as any).cache || undefined
  }
}

// Helper to prefill widget form with a metric
function prefillFormWithRecommendation(metric: SemanticMetric, dataSourceId: string, dataModelId: string) {
  // Prefill form with recommendation data
  editor.form.title = metric.title || metric.name
  editor.form.type = determineVisualizationType(metric)
  
  // Build available tables from the metric
  const columns: { name: string; type: string }[] = []
  try {
    ;(metric.dimensions || []).forEach((d: any) => 
      columns.push({ name: d.name || d, type: d.type || 'dimension' })
    )
    ;(metric.measures || []).forEach((m: any) => 
      columns.push({ name: m.name || m, type: m.type || 'measure' })
    )
  } catch {}
  const tableName = metric.data_model_name || metric.table_name || 'Metric'
  editor.availableTables.value = [{ name: tableName, columns }]
  
  // Use embedded metric (saved directly in widget, not as a separate metric)
  editor.form.metric_id = '' // Clear metric_id
  editor.selectedMetric.value = metric
  editor.isEmbeddedMetric.value = true
  
  // Auto-generate data mapping based on metric structure
  const hasMeasures = metric.measures && metric.measures.length > 0
  const hasDimensions = metric.dimensions && metric.dimensions.length > 0
  
  if (editor.form.type === 'single_value' && hasMeasures && metric.measures) {
    const firstMeasure = metric.measures[0]
    editor.dataMapping.value = {
      x_axis: {
        field: firstMeasure.name || firstMeasure.query || 'value',
        data_type: 'numerical',
        label: firstMeasure.name,
        required: true
      }
    }
  } else if (hasMeasures && hasDimensions && metric.dimensions && metric.measures) {
    const firstDim = metric.dimensions[0]
    editor.dataMapping.value = {
      x_axis: {
        field: firstDim.name || firstDim.query || 'dimension',
        data_type: 'categorical',
        label: firstDim.name,
        required: true
      },
      y_axes: metric.measures.map((measure: any) => ({
        field: measure.name || measure.query || 'measure',
        data_type: 'numerical',
        label: measure.name,
        required: true
      }))
    }
  }
}

// Handle click on recommendation - pre-fill schema builder and preview
function handleRecommendationSelect(metric: SemanticMetric, dataSourceId: string, dataModelId: string) {
  // Pre-fill the schema builder with recommendation data (including data_model_id)
  prefillSchemaBuilderWithMetric(metric, dataSourceId, dataModelId)
  
  // Also prefill the widget form for preview
  prefillFormWithRecommendation(metric, dataSourceId, dataModelId)
  
  // Set data source for schema builder
  if (dataSourceId) {
    selectedDataSourceId.value = dataSourceId
  }
  
  // Trigger preview with embedded metric
  setTimeout(() => editor.updatePreview(), 100)
  
  toast.info(`Pre-filled from: ${metric.title || metric.name}. Customize below and save.`)
}

// Determine visualization type based on metric structure
function determineVisualizationType(metric: SemanticMetric): string {
  const hasMeasures = metric.measures && metric.measures.length > 0
  const hasDimensions = metric.dimensions && metric.dimensions.length > 0
  
  if (hasMeasures && hasDimensions) {
    // For metrics with both measures and dimensions, prefer bar chart
    return 'bar_chart'
  }
  
  return 'single_value'
}

// Handle cancel
function handleCancel() {
  emit('cancel')
}

// Handle save
async function handleSave() {
  // For custom metrics (embedded), build the metric from schema builder
  if (activeMetricTab.value === 'custom') {
    const schema = schemaBuilder.schema.value
    
    // Validate that we have at least a name
    if (!schema.name) {
      toast.error('Please provide a metric name')
      return
    }
    
    // Build the embedded metric from schema builder
    const embeddedMetric: SemanticMetric = {
      id: '', // Will be generated by backend or kept empty for embedded
      name: schema.name,
      alias: schema.alias || undefined,
      title: schema.title || schema.name,
      description: schema.description || undefined,
      table_name: schema.table_name || undefined,
      query: schema.query || undefined,
      data_source_id: schema.data_source_id || selectedDataSourceId.value || undefined,
      data_model_id: schema.data_model_id || undefined,
      limit: schema.limit || undefined,
      grouped: schema.grouped ?? true,
      ordered: schema.ordered ?? true,
      measures: schema.measures?.length ? schema.measures : undefined,
      dimensions: schema.dimensions?.length ? schema.dimensions : undefined,
      joins: schema.joins?.length ? schema.joins : undefined,
      filters: schema.filters?.length ? schema.filters : undefined,
      order: schema.order?.length ? schema.order : undefined,
    } as SemanticMetric
    
    // Update editor state with the embedded metric
    editor.selectedMetric.value = embeddedMetric
    editor.isEmbeddedMetric.value = true
    editor.form.metric_id = '' // Clear metric_id for embedded
    
    // Update form title if not set
    if (!editor.form.title) {
      editor.form.title = embeddedMetric.title || embeddedMetric.name
    }
    
    // Auto-generate data mapping if not already set
    if (!editor.dataMapping.value?.x_axis && !editor.dataMapping.value?.y_axes?.length) {
      const hasMeasures = embeddedMetric.measures && embeddedMetric.measures.length > 0
      const hasDimensions = embeddedMetric.dimensions && embeddedMetric.dimensions.length > 0
      
      if (editor.form.type === 'single_value' && hasMeasures) {
        const firstMeasure = embeddedMetric.measures![0]
        editor.dataMapping.value = {
          x_axis: {
            field: firstMeasure.name || 'value',
            data_type: 'numerical',
            label: firstMeasure.name,
            required: true
          }
        }
      } else if (hasMeasures && hasDimensions) {
        const firstDim = embeddedMetric.dimensions![0]
        editor.dataMapping.value = {
          x_axis: {
            field: firstDim.name || 'dimension',
            data_type: 'categorical',
            label: firstDim.name,
            required: true
          },
          y_axes: embeddedMetric.measures!.map((measure: any) => ({
            field: measure.name || 'measure',
            data_type: 'numerical',
            label: measure.name,
            required: true
          }))
        }
      }
    }
  }
  
  // Validate that we have a metric selected
  if (!editor.isValid.value) {
    toast.error('Please select or define a metric')
    return
  }
  
  const widgetData = editor.buildWidgetData()
  emit('save', widgetData)
}

// Toggle expanded state
function toggleExpanded() {
  isExpanded.value = !isExpanded.value
}

// Load widget data when editing
watch(() => props.widget, (widget) => {
  if (widget) {
    loadWidgetForEditing(widget)
  }
}, { immediate: true })

// Helper to load widget for editing (handles both metric_id and embedded metric)
function loadWidgetForEditing(widget: DashboardWidget) {
  // Load basic widget data
  editor.loadWidget(widget)
  
  // Check if widget has embedded metric
  const embeddedMetric = (widget as any).metric
  if (embeddedMetric) {
    // Embedded metric - pre-fill schema builder and switch to custom tab
    prefillSchemaBuilderWithMetric(embeddedMetric, embeddedMetric.data_source_id)
    activeMetricTab.value = 'custom'
    editor.isEmbeddedMetric.value = true
    editor.selectedMetric.value = embeddedMetric
    
    // Set data source if available
    if (embeddedMetric.data_source_id) {
      selectedDataSourceId.value = embeddedMetric.data_source_id
    }
  } else if (widget.metric_id) {
    // Referenced metric - use select tab
    activeMetricTab.value = 'select'
  }
}

// Initialize on mount
onMounted(() => {
  if (props.widget) {
    loadWidgetForEditing(props.widget)
    // Auto-trigger preview for existing widgets
    if (editor.form.metric_id || editor.selectedMetric.value) {
      setTimeout(() => editor.updatePreview(), 200)
    }
  }
})
</script>

<template>
  <Card class="inline-widget-editor border-2 border-primary/30 shadow-lg">
    <!-- Header -->
    <CardHeader class="pb-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <CardTitle class="text-lg">
            {{ mode === 'create' ? 'Add Widget' : 'Edit Widget' }}
          </CardTitle>
          <Badge v-if="editor.selectedMetric.value" variant="secondary">
            {{ editor.selectedMetricLabel.value }}
          </Badge>
        </div>
        
        <div class="flex items-center gap-2">
          <Button variant="ghost" size="icon" @click="toggleExpanded">
            <ChevronUp v-if="isExpanded" class="h-4 w-4" />
            <ChevronDown v-else class="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="handleCancel">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </CardHeader>

    <CardContent v-show="isExpanded" class="space-y-6">
      <!-- Live Preview Panel -->
      <Card class="bg-muted/30">
        <CardHeader class="pb-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Eye class="h-4 w-4 text-muted-foreground" />
              <span class="text-sm font-medium">Preview</span>
            </div>
            <div class="flex items-center gap-2">
              <Badge v-if="editor.previewLoading.value" variant="secondary" class="animate-pulse">
                Loading...
              </Badge>
              <Badge v-else-if="editor.previewError.value" variant="destructive">
                <AlertCircle class="w-3 h-3 mr-1" />
                Error
              </Badge>

              <Button variant="ghost" size="sm" :disabled="editor.previewLoading.value || (!editor.form.metric_id && !editor.selectedMetric.value)" @click="editor.updatePreview">
                <RefreshCw class="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="editor.previewLoading.value" class="flex items-center justify-center h-40">
            <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
          
          <div v-else-if="editor.previewError.value" class="flex items-center justify-center h-40">
            <div class="text-center">
              <AlertCircle class="w-6 h-6 text-destructive mx-auto mb-2" />
              <p class="text-xs text-destructive">{{ editor.previewError.value }}</p>
            </div>
          </div>
          
          <div v-else-if="editor.previewData.value" class="min-h-40">
            <PreviewWidgetViz 
              :type="editor.form.type"
              :data="editor.previewData.value"
              :loading="editor.previewLoading.value"
              :error="editor.previewError.value"
              :gauge-config="editor.gaugeConfig"
              :single-value-config="editor.singleValueConfig"
              :chart-config="editor.chartConfig"
            />
          </div>
          
          <div v-else class="flex items-center justify-center h-40 text-muted-foreground">
            <p class="text-sm">Select a metric to see preview</p>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <!-- Metric Selection Tabs -->
      <div class="space-y-4">
        <div class="flex items-center gap-2">
          <Settings class="h-4 w-4 text-muted-foreground" />
          <span class="text-sm font-medium">Metric Configuration</span>
        </div>
        
        <Tabs v-model="activeMetricTab" class="w-full">
          <TabsList class="grid w-full" :class="`grid-cols-${metricTabsOrder.length}`">
            <TabsTrigger 
              v-for="tab in metricTabsOrder" 
              :key="tab.value" 
              :value="tab.value"
              class="text-xs"
            >
              <component :is="tab.icon" class="h-3 w-3 mr-1" />
              {{ tab.label }}
            </TabsTrigger>
          </TabsList>

          <!-- Select Metric Tab -->
          <TabsContent value="select" class="mt-4 space-y-4">
            <div class="space-y-2">
              <Label>Choose an existing metric</Label>
              <MetricSelector 
                :button-text="editor.selectedMetricLabel.value || 'Select Metric'" 
                @select="handleMetricSelect" 
              />
            </div>
          </TabsContent>

          <!-- Custom Metric Tab (Recommendations + Schema Builder) -->
          <TabsContent value="custom" class="mt-4 space-y-6">
            <!-- Recommendations Section (Collapsible) -->
            <div class="space-y-3 border rounded-lg p-3">
              <button 
                type="button"
                class="w-full flex items-center justify-between text-left"
                @click="collapsibleSections.recommendations.isOpen = !collapsibleSections.recommendations.isOpen"
              >
                <Label class="text-sm font-medium flex items-center gap-2 cursor-pointer">
                  <component :is="collapsibleSections.recommendations.icon" class="h-4 w-4" />
                  {{ collapsibleSections.recommendations.label }}
                </Label>
                <div class="flex items-center gap-2">
                  <ChevronDown 
                    class="h-4 w-4 text-muted-foreground transition-transform" 
                    :class="{ 'rotate-180': collapsibleSections.recommendations.isOpen }"
                  />
                </div>
              </button>
              
              <div v-show="collapsibleSections.recommendations.isOpen" class="pt-2">
                <div class="max-h-[2/3vh] overflow-y-auto">
                  <MetricRecommendations 
                    :dashboard-id="dashboardId"
                    :initial-data-source-id="selectedDataSourceId"
                    :initial-data-model-id="schemaBuilder.schema.value.data_model_id"
                    @select="handleRecommendationSelect"
                    compact
                  />
                </div>
              </div>
            </div>

            <Separator />

            <!-- Metric Schema Builder Section (Collapsible) -->
            <div class="space-y-3 border rounded-lg p-3">
              <button 
                type="button"
                class="w-full flex items-center justify-between text-left"
                @click="collapsibleSections.metricDefinition.isOpen = !collapsibleSections.metricDefinition.isOpen"
              >
                <Label class="text-sm font-medium flex items-center gap-2 cursor-pointer">
                  <component :is="collapsibleSections.metricDefinition.icon" class="h-4 w-4" />
                  {{ collapsibleSections.metricDefinition.label }}
                </Label>
                <ChevronDown 
                  class="h-4 w-4 text-muted-foreground transition-transform" 
                  :class="{ 'rotate-180': collapsibleSections.metricDefinition.isOpen }"
                />
              </button>
              
              <div v-show="collapsibleSections.metricDefinition.isOpen" class="space-y-3 pt-2">
                <!-- Data Source Selector for Schema -->
                <div class="space-y-2">
                  <Label class="text-xs text-muted-foreground">Data Source</Label>
                  <UiSelect v-model="selectedDataSourceId">
                    <UiSelectTrigger>
                      <UiSelectValue placeholder="Select data source" />
                    </UiSelectTrigger>
                    <UiSelectContent>
                      <UiSelectItem 
                        v-for="source in dataSources" 
                        :key="source.id" 
                        :value="source.id"
                      >
                        {{ source.name }}
                      </UiSelectItem>
                    </UiSelectContent>
                  </UiSelect>
                </div>

                <!-- Metric Schema Builder -->
                <div class="max-h-[400px] overflow-y-auto pr-2">
                  <MetricSchemaBuilder 
                    :selected-data-source-id="selectedDataSourceId"
                    :table-schema="tableSchema"
                  />
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <!-- Widget Configuration (shown when metric is selected) -->
      <div v-if="editor.form.metric_id || editor.selectedMetric.value" class="space-y-4">
        <Separator />
        
        <!-- Collapsible Widget Settings Section -->
        <div class="border rounded-lg p-3">
          <button 
            type="button"
            class="w-full flex items-center justify-between text-left"
            @click="collapsibleSections.widgetSettings.isOpen = !collapsibleSections.widgetSettings.isOpen"
          >
            <div class="flex items-center gap-2">
              <component :is="collapsibleSections.widgetSettings.icon" class="h-4 w-4 text-muted-foreground" />
              <span class="text-sm font-medium">{{ collapsibleSections.widgetSettings.label }}</span>
            </div>
            <ChevronDown 
              class="h-4 w-4 text-muted-foreground transition-transform" 
              :class="{ 'rotate-180': collapsibleSections.widgetSettings.isOpen }"
            />
          </button>

          <div v-show="collapsibleSections.widgetSettings.isOpen" class="space-y-4 pt-4">
            <!-- Title -->
            <div class="space-y-2">
              <Label>Title</Label>
              <Input v-model="editor.form.title" placeholder="Widget title" />
            </div>

            <!-- Visualization Type -->
            <div class="space-y-2">
              <Label>Visualization</Label>
              <VisualizationTypeSelector v-model="editor.form.type" />
            </div>

            <!-- Grid Size -->
            <GridSizeSelector 
              :columns="editor.form.columns" 
              :rows="editor.form.rows"
              @update:columns="(value) => editor.form.columns = value"
              @update:rows="(value) => editor.form.rows = value"
            />

            <!-- Data Mapping -->
            <DataMappingEditor
              :visualization-type="editor.form.type"
              :mapping="editor.dataMapping.value"
              :available-tables="editor.availableTables.value"
              @update="editor.updateDataMapping"
            />

            <!-- Chart Options -->
            <div v-if="editor.isChartType.value" class="space-y-3">
              <Label class="text-sm font-medium">Chart Options</Label>
              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-2">
                  <Label class="text-xs">Stack Columns</Label>
                  <div class="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      v-model="editor.chartConfig.stack_bars"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span class="text-sm text-muted-foreground">Enable stacking</span>
                  </div>
                </div>
                
                <div v-if="editor.form.type === 'area_chart' && editor.chartConfig.stack_bars" class="space-y-2">
                  <Label class="text-xs">Stacking Style</Label>
                  <UiSelect v-model="editor.areaStackingType.value">
                    <UiSelectTrigger>
                      <UiSelectValue placeholder="Select style" />
                    </UiSelectTrigger>
                    <UiSelectContent>
                      <UiSelectItem value="normal">Normal</UiSelectItem>
                      <UiSelectItem value="gradient">Gradient</UiSelectItem>
                    </UiSelectContent>
                  </UiSelect>
                </div>
              </div>
            </div>

            <!-- Single Value Options -->
            <div v-if="editor.form.type === 'single_value'" class="space-y-3">
              <Label class="text-sm font-medium">Single Value Options</Label>
              <div class="grid grid-cols-3 gap-3">
                <div class="space-y-2">
                  <Label class="text-xs">Prefix</Label>
                  <Input v-model="editor.singleValueConfig.prefix" placeholder="$" />
                </div>
                <div class="space-y-2">
                  <Label class="text-xs">Suffix</Label>
                  <Input v-model="editor.singleValueConfig.suffix" placeholder="units" />
                </div>
                <div class="space-y-2">
                  <Label class="text-xs">Number format</Label>
                  <UiSelect v-model="editor.singleValueConfig.number_format">
                    <UiSelectTrigger>
                      <UiSelectValue placeholder="Select format" />
                    </UiSelectTrigger>
                    <UiSelectContent>
                      <UiSelectItem value="integer">Integer</UiSelectItem>
                      <UiSelectItem value="decimal">Decimal</UiSelectItem>
                      <UiSelectItem value="percentage">Percentage</UiSelectItem>
                      <UiSelectItem value="currency">Currency</UiSelectItem>
                      <UiSelectItem value="abbreviated">Abbreviated</UiSelectItem>
                      <UiSelectItem value="scientific">Scientific</UiSelectItem>
                    </UiSelectContent>
                  </UiSelect>
                </div>
              </div>
            </div>

            <!-- Gauge Options -->
            <div v-if="editor.form.type === 'gauge'" class="space-y-3">
              <Label class="text-sm font-medium">Gauge Options</Label>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <Label class="text-xs">Min</Label>
                  <NumberField v-model="editor.gaugeConfig.min_value" :min="0" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
                <div>
                  <Label class="text-xs">Max</Label>
                  <NumberField v-model="editor.gaugeConfig.max_value" :min="1" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
                <div>
                  <Label class="text-xs">Thickness</Label>
                  <NumberField v-model="editor.gaugeConfig.thickness" :min="1" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      <!-- Action Buttons -->
      <div class="flex items-center justify-end gap-3">
        <Button variant="outline" @click="handleCancel">
          <X class="w-4 h-4 mr-2" />
          Cancel
        </Button>
        <Button @click="handleSave" :disabled="!editor.isValid.value">
          <Save class="w-4 h-4 mr-2" />
          {{ mode === 'create' ? 'Add Widget' : 'Save Changes' }}
        </Button>
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
.inline-widget-editor {
  transition: all 0.3s ease-out;
}
</style>

