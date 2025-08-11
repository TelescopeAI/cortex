<script setup lang="ts">
import { reactive, computed, watch, ref, onMounted } from 'vue'
import { refDebounced } from '@vueuse/core'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from '~/components/ui/sheet'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Select as UiSelect, SelectContent as UiSelectContent, SelectItem as UiSelectItem, SelectTrigger as UiSelectTrigger, SelectValue as UiSelectValue } from '~/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Separator } from '~/components/ui/separator'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { Eye, Settings, Save, X, AlertCircle, CheckCircle, ChevronDown, RefreshCw } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import MetricSelector from '~/components/MetricSelector.vue'
import DataMappingEditor from './DataMappingEditor.vue'
import type { DashboardWidget } from '~/types/dashboards'
import { useMetrics, type SemanticMetric } from '~/composables/useMetrics'
import { useDashboards } from '~/composables/useDashboards'
import PreviewChartRenderer from './PreviewChartRenderer.vue'

interface Props {
  open: boolean
  widget?: DashboardWidget
  dashboardId: string
}

interface Emits {
  (e: 'update:open', val: boolean): void
  (e: 'save', widget: Partial<DashboardWidget>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { getMetric } = useMetrics()
const { previewDashboardConfig } = useDashboards()

// Form state
const form = reactive({
  title: '',
  metric_id: '',
  type: 'single_value',
  columns: 3,
  rows: 1
})

const selectedMetric = ref<SemanticMetric | null>(null)
const availableTables = ref<Array<{ name: string; columns: Array<{ name: string; type: string }> }>>([])
const dataMapping = reactive<any>({})
const singleValue = reactive<any>({
  number_format: 'auto',
  prefix: '',
  suffix: '',
  show_comparison: true,
  show_trend: true,
  trend_period: 'previous_period',
  show_sparkline: false,
  show_title: true,
  show_description: false,
  compact_mode: false,
})

const gauge = reactive<any>({
  min_value: 0,
  max_value: 100,
  target_value: undefined,
  color_ranges: undefined,
  show_value: true,
  show_target: true,
  gauge_type: 'arc',
  thickness: 10,
})

// Current mode: 'edit' or 'view'
const currentMode = ref<'edit' | 'view'>('edit')

// Preview state
const previewData = ref<any>(null)
const previewLoading = ref(false)
const previewError = ref<string | null>(null)
const previewTab = ref<'charts' | 'json'>('charts')

// Screen size detection
const windowWidth = ref(0)
const isSmallScreen = computed(() => windowWidth.value < 768)

// Create debounced version of form data for preview
const debouncedFormData = refDebounced(
  computed(() => ({
    ...form,
    dataMapping: { ...dataMapping },
    singleValue: { ...singleValue },
    gauge: { ...gauge }
  })),
  500 // 500ms delay as suggested by VueUse docs
)

// Watch for changes and initialize
watch(() => props.widget, (widget) => {
  if (widget) {
    form.title = widget.title || ''
    form.metric_id = widget.metric_id || ''
    form.type = widget.visualization?.type || 'single_value'
    form.columns = widget.grid_config?.columns || 3
    form.rows = widget.grid_config?.rows || 1
    
    if (widget.visualization?.data_mapping) {
      Object.assign(dataMapping, widget.visualization.data_mapping)
    }
    if (widget.visualization?.single_value_config) {
      Object.assign(singleValue, widget.visualization.single_value_config)
    }
    if (widget.visualization?.gauge_config) {
      Object.assign(gauge, widget.visualization.gauge_config)
    }
    
    // Load metric details
    if (widget.metric_id) {
      getMetric(widget.metric_id).then(m => {
        if (m) {
          selectedMetric.value = m
          buildAvailableTablesFromMetric(m)
        }
      })
    }
  }
}, { immediate: true })

// Watch debounced form data for preview updates
watch(debouncedFormData, async (newData) => {
  if (props.open && selectedMetric.value) {
    await updatePreview()
  }
})

// Reset mapping/config when visualization type changes to keep payload clean
watch(() => form.type, (newType, oldType) => {
  if (newType === oldType) return
  // Clear all mapping/config states
  Object.keys(dataMapping).forEach(k => delete (dataMapping as any)[k])
  Object.assign(singleValue, { number_format: 'decimal', prefix: '', suffix: '', show_comparison: true, show_trend: true, trend_period: 'previous_period', show_sparkline: false, show_title: true, show_description: false, compact_mode: false })
  Object.assign(gauge, { min_value: 0, max_value: 100, target_value: undefined, color_ranges: undefined, show_value: true, show_target: true, gauge_type: 'arc', thickness: 10 })
})

const selectedMetricLabel = computed(() => {
  if (!selectedMetric.value && !form.metric_id) return ''
  const name = selectedMetric.value?.name
  const model = selectedMetric.value?.data_model?.name
  return name ? `${name}${model ? ' • ' + model : ''}` : ''
})

function buildAvailableTablesFromMetric(metric: SemanticMetric | null) {
  if (!metric) { 
    availableTables.value = []
    return 
  }
  const columns: { name: string; type: string }[] = []
  try {
    ;(metric.dimensions || []).forEach((d: any) => columns.push({ name: d.name || d, type: d.type || 'dimension' }))
    ;(metric.measures || []).forEach((m: any) => columns.push({ name: m.name || m, type: m.type || 'measure' }))
  } catch {}
  const tableName = metric.data_model?.name || metric.table_name || 'Metric'
  availableTables.value = [{ name: tableName, columns }]
}

function onMetricSelect(metric: any) {
  form.metric_id = metric.id
  selectedMetric.value = metric
  buildAvailableTablesFromMetric(metric)
}

function updateDataMapping(mapping: any) {
  Object.assign(dataMapping, mapping)
}

function close() {
  emit('update:open', false)
}

function save() {
  const widgetData = {
    title: form.title,
    metric_id: form.metric_id,
    grid_config: { columns: form.columns, rows: form.rows },
    visualization: { 
      type: form.type as any,
      data_mapping: dataMapping,
      single_value_config: form.type === 'single_value' ? singleValue : undefined,
      gauge_config: form.type === 'gauge' ? gauge : undefined
    }
  }
  
  emit('save', widgetData)
  close()
}

function copyPreview() {
  try {
    if (previewData.value && typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(JSON.stringify(previewData.value, null, 2))
    }
  } catch {}
}

async function updatePreview() {
  if (!props.widget || !form.metric_id) return
  
  previewLoading.value = true
  previewError.value = null
  
  try {
    // Create a mock dashboard configuration for preview
    const previewConfig = {
      views: [{
        sections: [{
          alias: 'preview_section',
          widgets: [{
            alias: 'preview_widget',
            section_alias: 'preview_section',
            metric_id: form.metric_id,
            title: form.title || 'Preview Widget',
            visualization: {
              type: form.type,
              data_mapping: dataMapping,
              single_value_config: form.type === 'single_value' ? singleValue : undefined,
              gauge_config: form.type === 'gauge' ? gauge : undefined
            },
            grid_config: { columns: form.columns, rows: form.rows }
          }]
        }]
      }]
    }
    
    // Call preview API using the composable
    const result = await previewDashboardConfig(props.dashboardId, previewConfig)
    previewData.value = result.view_execution?.widgets?.[0]?.data
    
  } catch (error) {
    console.error('Preview error:', error)
    previewError.value = error instanceof Error ? error.message : 'Failed to generate preview'
  } finally {
    previewLoading.value = false
  }
}

onMounted(() => {
  if (props.open && props.widget) {
    updatePreview()
  }
  
  // Update window width on mount and resize
  if (process.client) {
    windowWidth.value = window.innerWidth
    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })
  }
})
</script>

<template>
  <Sheet :open="open" @update:open="val => emit('update:open', val)">
    <SheetContent 
      :side="isSmallScreen ? 'bottom' : 'right'" 
      :class="[
        'flex flex-col',
        'p-4',
        isSmallScreen 
          ? '!w-full !h-[90vh]' 
          :'!w-[95vw] sm:!w-[85vw] md:!w-[75vw] lg:!w-[65vw] xl:!w-[50vw] !max-w-[50vw] sm:!max-w-none'
      ]"
    >
      <SheetHeader>
        <div class="flex items-center justify-between">
          <div>
            <SheetTitle>Edit Widget</SheetTitle>
            <SheetDescription>Configure your widget settings and see live preview</SheetDescription>
          </div>
          <div class="flex items-center gap-2">
            <Tabs :value="currentMode" @update:value="currentMode = $event" class="w-auto">
              <TabsList class="grid w-full grid-cols-2">
                <TabsTrigger value="edit" class="flex items-center gap-1">
                  <Settings class="w-4 h-4" />
                  Edit
                </TabsTrigger>
                <TabsTrigger value="view" class="flex items-center gap-1">
                  <Eye class="w-4 h-4" />
                  Preview
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </SheetHeader>

      <!-- Main content area -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <!-- Configuration Panel -->
        <div :class="{ 'hidden': currentMode === 'view' }" class="space-y-6 py-4">
          <div class="space-y-4">
            <!-- Basic Configuration -->
            <div class="space-y-3">
              <Label class="text-base font-medium">Basic Settings</Label>
              
              <div class="space-y-2">
                <Label>Title</Label>
                <Input v-model="form.title" placeholder="Widget title" />
              </div>
              
              <div class="space-y-2">
                <Label>Metric</Label>
                <MetricSelector :button-text="selectedMetricLabel || 'Select Metric'" @select="onMetricSelect" />
              </div>
              
              <div class="grid grid-cols-3 gap-3">
                <div class="space-y-2">
                  <Label>Visualization</Label>
                  <UiSelect v-model="form.type">
                    <UiSelectTrigger>
                      <UiSelectValue placeholder="Type" />
                    </UiSelectTrigger>
                    <UiSelectContent>
                      <UiSelectItem value="single_value">Single Value</UiSelectItem>
                      <UiSelectItem value="gauge">Gauge</UiSelectItem>
                      <UiSelectItem value="bar_chart">Bar</UiSelectItem>
                      <UiSelectItem value="line_chart">Line</UiSelectItem>
                      <UiSelectItem value="area_chart">Area</UiSelectItem>
                      <UiSelectItem value="pie_chart">Pie</UiSelectItem>
                      <UiSelectItem value="donut_chart">Donut</UiSelectItem>
                      <UiSelectItem value="scatter_plot">Scatter</UiSelectItem>
                      <UiSelectItem value="table">Table</UiSelectItem>
                    </UiSelectContent>
                  </UiSelect>
                </div>
                <div class="space-y-2">
                  <Label>Columns</Label>
                  <NumberField v-model="form.columns" :min="1" :max="12" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
                <div class="space-y-2">
                  <Label>Rows</Label>
                  <NumberField v-model="form.rows" :min="1" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
              </div>
            </div>

            <Separator />

            <!-- Data Mapping -->
            <DataMappingEditor
              :visualization-type="form.type"
              :mapping="dataMapping"
              :available-tables="availableTables"
              @update="updateDataMapping"
            />

            <Separator />

            <!-- Visualization-specific config -->
            <div v-if="form.type === 'single_value'" class="space-y-3">
              <Label class="text-base font-medium">Single Value Options</Label>
              <div class="grid grid-cols-3 gap-3">
                <div class="space-y-2">
                  <Label class="text-xs">Prefix</Label>
                  <Input v-model="singleValue.prefix" placeholder="$" />
                </div>
                <div class="space-y-2">
                  <Label class="text-xs">Suffix</Label>
                  <Input v-model="singleValue.suffix" placeholder="units" />
                </div>
            <div class="space-y-2">
              <Label class="text-xs">Number format</Label>
              <UiSelect v-model="singleValue.number_format">
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

            <div v-if="form.type === 'gauge'" class="space-y-3">
              <Label class="text-base font-medium">Gauge Options</Label>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <Label class="text-xs">Min</Label>
                  <NumberField v-model="gauge.min_value" :min="0" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
                <div>
                  <Label class="text-xs">Max</Label>
                  <NumberField v-model="gauge.max_value" :min="1" :step="1">
                    <NumberFieldContent>
                      <NumberFieldDecrement />
                      <NumberFieldInput />
                      <NumberFieldIncrement />
                    </NumberFieldContent>
                  </NumberField>
                </div>
                <div>
                  <Label class="text-xs">Thickness</Label>
                  <NumberField v-model="gauge.thickness" :min="1" :step="1">
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
          
          <!-- Preview Panel (shown below config) -->
          <div class="space-y-4">
          <Card>
            <CardHeader>
              <div class="flex items-center justify-between">
                <CardTitle class="text-lg">Live Preview</CardTitle>
                <div class="flex items-center gap-2">
                  <Badge v-if="previewLoading" variant="secondary" class="animate-pulse">
                    Updating...
                  </Badge>
                  <Badge v-else-if="previewError" variant="destructive">
                    <AlertCircle class="w-3 h-3 mr-1" />
                    Error
                  </Badge>
                  <Badge v-else variant="secondary">
                    <CheckCircle class="w-3 h-3 mr-1" />
                    Live
                  </Badge>
                  <Button variant="outline" size="sm" :disabled="previewLoading" @click="updatePreview">
                    <RefreshCw class="w-3 h-3 mr-1" />
                    Run
                  </Button>
                  <Button variant="outline" size="sm" @click="copyPreview">Copy</Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div v-if="previewLoading" class="flex items-center justify-center h-32">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                  <p class="text-sm text-muted-foreground">Generating preview...</p>
                </div>
              </div>
              
              <div v-else-if="previewError" class="flex items-center justify-center h-32">
                <div class="text-center">
                  <AlertCircle class="w-8 h-8 text-destructive mx-auto mb-2" />
                  <p class="text-sm text-destructive">{{ previewError }}</p>
                </div>
              </div>
              
              <div v-else-if="previewData" class="min-h-32">
                <Tabs v-model="previewTab" class="w-full">
                  <TabsList class="grid w-full grid-cols-2">
                    <TabsTrigger value="charts">Charts</TabsTrigger>
                    <TabsTrigger value="json">JSON</TabsTrigger>
                  </TabsList>

                  <TabsContent value="charts" class="mt-4">
                    <div class="w-full max-h-[36rem]">
                      <PreviewChartRenderer 
                        :processed="previewData.processed" 
                        :metadata="previewData.metadata"
                        :type="form.type"
                        :gauge-config="gauge"
                      />
                    </div>
                  </TabsContent>
                  <TabsContent value="json" class="mt-4">
                    <pre class="text-xs bg-muted p-3 rounded overflow-auto max-h-64">{{ JSON.stringify(previewData, null, 2) }}</pre>
                  </TabsContent>
                </Tabs>
              </div>
              
              <div v-else class="flex items-center justify-center h-32">
                <p class="text-sm text-muted-foreground">Configure your widget to see preview</p>
              </div>
            </CardContent>
          </Card>
          </div>
        </div>
        
        <!-- Full Preview Mode -->
        <div v-if="currentMode === 'view'" class="py-4">
          <Card>
            <CardHeader>
              <div class="flex items-center justify-between">
                <CardTitle class="text-lg">Live Preview</CardTitle>
                <div class="flex items-center gap-2">
                  <Badge v-if="previewLoading" variant="secondary" class="animate-pulse">
                    Updating...
                  </Badge>
                  <Badge v-else-if="previewError" variant="destructive">
                    <AlertCircle class="w-3 h-3 mr-1" />
                    Error
                  </Badge>
                  <Badge v-else variant="secondary">
                    <CheckCircle class="w-3 h-3 mr-1" />
                    Live
                  </Badge>
                  <Button variant="outline" size="sm" :disabled="previewLoading" @click="updatePreview">
                    <RefreshCw class="w-3 h-3 mr-1" />
                    Run
                  </Button>
                  <Button variant="outline" size="sm" @click="copyPreview">Copy</Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div v-if="previewLoading" class="flex items-center justify-center h-64">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                  <p class="text-sm text-muted-foreground">Generating preview...</p>
                </div>
              </div>
              
              <div v-else-if="previewError" class="flex items-center justify-center h-64">
                <div class="text-center">
                  <AlertCircle class="w-8 h-8 text-destructive mx-auto mb-2" />
                  <p class="text-sm text-destructive">{{ previewError }}</p>
                </div>
              </div>
              
              <div v-else-if="previewData" class="min-h-64">
                <Tabs v-model="previewTab" class="w-full">
                  <TabsList class="grid w-full grid-cols-2">
                    <TabsTrigger value="charts">Charts</TabsTrigger>
                    <TabsTrigger value="json">JSON</TabsTrigger>
                  </TabsList>

                  <TabsContent value="charts" class="mt-4">
                    <div class="w-full max-h-[40rem]">
                      <PreviewChartRenderer 
                        :processed="previewData.processed" 
                        :metadata="previewData.metadata"
                        :type="form.type"
                        :gauge-config="gauge"
                      />
                    </div>
                  </TabsContent>
                  <TabsContent value="json" class="mt-4">
                    <pre class="text-xs bg-muted p-3 rounded overflow-auto max-h-96">{{ JSON.stringify(previewData, null, 2) }}</pre>
                  </TabsContent>
                </Tabs>
              </div>
              
              <div v-else class="flex items-center justify-center h-64">
                <p class="text-sm text-muted-foreground">Configure your widget to see preview</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <SheetFooter class="mt-6">
        <Button variant="outline" @click="close">
          <X class="w-4 h-4 mr-2" />
          Cancel
        </Button>
        <Button @click="save" :disabled="!form.metric_id">
          <Save class="w-4 h-4 mr-2" />
          Save Changes
        </Button>
      </SheetFooter>
    </SheetContent>
  </Sheet>
</template>
