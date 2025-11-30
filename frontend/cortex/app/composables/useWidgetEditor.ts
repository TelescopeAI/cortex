import { ref, reactive, computed, watch, type Ref } from 'vue'
import type { DashboardWidget } from '~/types/dashboards'
import type { SemanticMetric } from '~/composables/useMetrics'

export interface WidgetEditorForm {
  title: string
  metric_id: string
  type: string
  columns: number
  rows: number
}

export interface SingleValueConfig {
  number_format: string
  prefix: string
  suffix: string
  show_comparison: boolean
  show_trend: boolean
  trend_period: string
  show_sparkline: boolean
  show_title: boolean
  show_description: boolean
  compact_mode: boolean
  selection_mode?: string
  selection_config?: {
    n?: number
    aggregate_by?: string
    delimiter?: string
  }
}

export interface ChartConfig {
  show_points: boolean
  line_width: number
  bar_width?: number
  stack_bars: boolean
  smooth_lines: boolean
  area_stacking_type?: 'normal' | 'gradient'
}

export interface GaugeConfig {
  min_value: number
  max_value: number
  target_value?: number
  color_ranges?: any
  show_value: boolean
  show_target: boolean
  gauge_type: string
  thickness: number
  selection_mode?: string
  selection_config?: {
    n?: number
    aggregate_by?: string
    delimiter?: string
  }
}

export interface AvailableTable {
  name: string
  columns: Array<{ name: string; type: string }>
}

export interface UseWidgetEditorOptions {
  dashboardId: string
  mode?: 'create' | 'edit'
  initialWidget?: DashboardWidget | null
}

export function useWidgetEditor(options: UseWidgetEditorOptions) {
  const { dashboardId, mode = 'create', initialWidget = null } = options
  
  const { getMetric } = useMetrics()
  const { previewDashboardConfig } = useDashboards()
  const { selectedEnvironmentId } = useEnvironments()

  // Form state
  const form = reactive<WidgetEditorForm>({
    title: '',
    metric_id: '',
    type: 'single_value',
    columns: 12,
    rows: 3
  })

  // Selected metric (can be embedded or referenced by ID)
  const selectedMetric = ref<SemanticMetric | null>(null)
  const availableTables = ref<AvailableTable[]>([])
  const isEmbeddedMetric = ref(false) // True if using embedded metric instead of metric_id

  // Data mapping
  const dataMapping = ref<any>({})

  // Single value configuration
  const singleValueConfig = reactive<SingleValueConfig>({
    number_format: 'decimal',
    prefix: '',
    suffix: '',
    show_comparison: true,
    show_trend: true,
    trend_period: 'previous_period',
    show_sparkline: false,
    show_title: true,
    show_description: false,
    compact_mode: false
  })

  // Chart configuration
  const chartConfig = reactive<ChartConfig>({
    show_points: true,
    line_width: 2,
    bar_width: undefined,
    stack_bars: false,
    smooth_lines: false
  })

  // Gauge configuration
  const gaugeConfig = reactive<GaugeConfig>({
    min_value: 0,
    max_value: 100,
    target_value: undefined,
    color_ranges: undefined,
    show_value: true,
    show_target: true,
    gauge_type: 'arc',
    thickness: 10
  })

  // Area stacking type (for area charts)
  const areaStackingType = ref<'normal' | 'gradient'>('normal')

  // Preview state
  const previewData = ref<any>(null)
  const previewLoading = ref(false)
  const previewError = ref<string | null>(null)
  const isUpdatingPreview = ref(false)

  // Validation state
  const isInitialLoad = ref(true)
  const isDirty = ref(false)

  // Computed
  const selectedMetricLabel = computed(() => {
    if (!selectedMetric.value && !form.metric_id) return ''
    const name = selectedMetric.value?.name
    const model = selectedMetric.value?.data_model_name
    return name ? `${name}${model ? ' • ' + model : ''}` : ''
  })

  const isValid = computed(() => {
    // Valid if we have either a metric_id or an embedded metric
    return (!!form.metric_id || !!selectedMetric.value) && !!form.type
  })

  const isChartType = computed(() => {
    return ['bar_chart', 'line_chart', 'area_chart'].includes(form.type)
  })

  // Build available tables from metric
  function buildAvailableTablesFromMetric(metric: SemanticMetric | null) {
    if (!metric) {
      availableTables.value = []
      return
    }
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
    availableTables.value = [{ name: tableName, columns }]
  }

  // Load widget data
  function loadWidget(widget: DashboardWidget | null) {
    if (!widget) {
      resetForm()
      return
    }

    // Load basic form data
    form.title = widget.title || ''
    form.metric_id = widget.metric_id || ''
    form.type = widget.visualization?.type || 'single_value'
    form.columns = widget.grid_config?.columns || 12
    form.rows = widget.grid_config?.rows || 3

    // Load data mapping
    if (widget.visualization?.data_mapping) {
      const dm = widget.visualization.data_mapping
      const nextMapping: any = {}

      if (dm.x_axis) {
        nextMapping.x_axis = {
          field: dm.x_axis.field || '',
          data_type: dm.x_axis.data_type || 'categorical',
          label: dm.x_axis.label || '',
          required: dm.x_axis.required !== false
        }
      }

      if (dm.y_axes && Array.isArray(dm.y_axes)) {
        nextMapping.y_axes = dm.y_axes.map((y: any) => ({
          field: y.field || '',
          data_type: y.data_type || 'numerical',
          label: y.label || '',
          required: y.required !== false
        }))
      }

      if (dm.value_field) {
        nextMapping.value_field = {
          field: dm.value_field.field || '',
          data_type: dm.value_field.data_type || 'numerical',
          label: dm.value_field.label || '',
          required: dm.value_field.required !== false
        }
      }

      if (dm.category_field) {
        nextMapping.category_field = {
          field: dm.category_field.field || '',
          data_type: dm.category_field.data_type || 'categorical',
          label: dm.category_field.label || '',
          required: dm.category_field.required !== false
        }
      }

      if (dm.series_field) {
        nextMapping.series_field = {
          field: dm.series_field.field || '',
          data_type: dm.series_field.data_type || 'categorical',
          label: dm.series_field.label || '',
          required: dm.series_field.required !== false
        }
      }

      if (dm.columns && Array.isArray(dm.columns)) {
        nextMapping.columns = dm.columns.map((col: any) => ({
          field: col.field || '',
          label: col.label || '',
          width: col.width,
          sortable: col.sortable !== false,
          filterable: col.filterable !== false,
          alignment: col.alignment || 'left'
        }))
      }

      dataMapping.value = nextMapping
    }

    // Load single value config
    if (widget.visualization?.single_value_config) {
      Object.assign(singleValueConfig, widget.visualization.single_value_config)
    }

    // Load chart config
    if (widget.visualization?.chart_config) {
      Object.assign(chartConfig, widget.visualization.chart_config)
      if (widget.visualization.chart_config.area_stacking_type) {
        areaStackingType.value = widget.visualization.chart_config.area_stacking_type
      } else if (widget.visualization.chart_config.stack_bars && widget.visualization.type === 'area_chart') {
        areaStackingType.value = 'normal'
      }
    }

    // Load gauge config
    if (widget.visualization?.gauge_config) {
      Object.assign(gaugeConfig, widget.visualization.gauge_config)
    }

    // Load metric details - handle both metric_id and embedded metric
    if (widget.metric_id && selectedEnvironmentId.value) {
      // Referenced metric - fetch from API
      getMetric(widget.metric_id, selectedEnvironmentId.value).then(m => {
        if (m) {
          selectedMetric.value = m
          buildAvailableTablesFromMetric(m)
        }
      })
    } else if ((widget as any).metric) {
      // Embedded metric - use directly
      const embeddedMetric = (widget as any).metric
      selectedMetric.value = embeddedMetric
      isEmbeddedMetric.value = true
      buildAvailableTablesFromMetric(embeddedMetric)
    }

    isInitialLoad.value = false
  }

  // Reset form to defaults
  function resetForm() {
    form.title = ''
    form.metric_id = ''
    form.type = 'single_value'
    form.columns = 12
    form.rows = 3

    selectedMetric.value = null
    availableTables.value = []
    dataMapping.value = {}

    Object.assign(singleValueConfig, {
      number_format: 'decimal',
      prefix: '',
      suffix: '',
      show_comparison: true,
      show_trend: true,
      trend_period: 'previous_period',
      show_sparkline: false,
      show_title: true,
      show_description: false,
      compact_mode: false
    })

    Object.assign(chartConfig, {
      show_points: true,
      line_width: 2,
      bar_width: undefined,
      stack_bars: false,
      smooth_lines: false
    })

    Object.assign(gaugeConfig, {
      min_value: 0,
      max_value: 100,
      target_value: undefined,
      color_ranges: undefined,
      show_value: true,
      show_target: true,
      gauge_type: 'arc',
      thickness: 10
    })

    areaStackingType.value = 'normal'
    previewData.value = null
    previewError.value = null
    isInitialLoad.value = true
    isDirty.value = false
  }

  // Handle metric selection
  function onMetricSelect(metric: SemanticMetric) {
    form.metric_id = metric.id
    selectedMetric.value = metric
    buildAvailableTablesFromMetric(metric)
    isDirty.value = true
  }

  // Update data mapping and trigger preview
  function updateDataMapping(mapping: any) {
    dataMapping.value = { ...(dataMapping.value || {}), ...(mapping || {}) }
    isDirty.value = true
    
    // Auto-update preview when data mapping changes (debounced)
    if (form.metric_id || selectedMetric.value) {
      setTimeout(() => updatePreview(), 300)
    }
  }

  // Build widget data for saving
  function buildWidgetData(): Partial<DashboardWidget> {
    const widgetData: any = {
      title: form.title,
      grid_config: { columns: form.columns, rows: form.rows },
      visualization: {
        type: form.type as any,
        data_mapping: dataMapping.value,
        chart_config: isChartType.value ? { ...chartConfig, area_stacking_type: areaStackingType.value } : undefined,
        single_value_config: form.type === 'single_value' ? { ...singleValueConfig } : undefined,
        gauge_config: form.type === 'gauge' ? { ...gaugeConfig } : undefined
      }
    }
    
    // Use either metric_id (reference) or metric (embedded)
    if (isEmbeddedMetric.value && selectedMetric.value) {
      widgetData.metric = selectedMetric.value
    } else if (form.metric_id) {
      widgetData.metric_id = form.metric_id
    }
    
    return widgetData
  }

  // Update preview
  async function updatePreview() {
    // Need either a metric_id or an embedded metric
    if ((!form.metric_id && !selectedMetric.value) || isUpdatingPreview.value) return

    isUpdatingPreview.value = true
    previewLoading.value = true
    previewError.value = null

    try {
      const widgetConfig: any = {
        alias: 'preview_widget',
        section_alias: 'preview_section',
        title: form.title || 'Preview Widget',
        visualization: {
          type: form.type,
          data_mapping: dataMapping.value,
          chart_config: isChartType.value ? { ...chartConfig, area_stacking_type: areaStackingType.value } : undefined,
          single_value_config: form.type === 'single_value' ? { ...singleValueConfig } : undefined,
          gauge_config: form.type === 'gauge' ? { ...gaugeConfig } : undefined
        },
        grid_config: { columns: form.columns, rows: form.rows }
      }
      
      // Use either metric_id (reference) or metric (embedded)
      if (isEmbeddedMetric.value && selectedMetric.value) {
        widgetConfig.metric = selectedMetric.value
      } else if (form.metric_id) {
        widgetConfig.metric_id = form.metric_id
      }
      
      const previewConfig = {
        views: [{
          sections: [{
            alias: 'preview_section',
            widgets: [widgetConfig]
          }]
        }]
      }

      const result = await previewDashboardConfig(dashboardId, previewConfig)
      previewData.value = result.view_execution?.widgets?.[0]?.data
    } catch (error) {
      console.error('Preview error:', error)
      previewError.value = error instanceof Error ? error.message : 'Failed to generate preview'
    } finally {
      previewLoading.value = false
      isUpdatingPreview.value = false
    }
  }

  // Watch for area stacking type changes
  watch(areaStackingType, (newType) => {
    if (chartConfig.stack_bars && form.type === 'area_chart') {
      chartConfig.area_stacking_type = newType
    }
  })

  // Watch for stack_bars changes
  watch(() => chartConfig.stack_bars, (newStackBars) => {
    if (newStackBars && form.type === 'area_chart' && !areaStackingType.value) {
      areaStackingType.value = 'normal'
    }
  })

  // Watch for chart type changes and reset configs
  watch(() => form.type, (newType, oldType) => {
    if (newType === oldType) return

    if (newType !== 'area_chart') {
      areaStackingType.value = 'normal'
    } else if (chartConfig.stack_bars && !areaStackingType.value) {
      areaStackingType.value = 'normal'
    }

    // Reset configs when type changes (not during initial load)
    if (oldType && newType && oldType !== '' && !isInitialLoad.value) {
      Object.assign(singleValueConfig, {
        number_format: 'decimal',
        prefix: '',
        suffix: '',
        show_comparison: true,
        show_trend: true,
        trend_period: 'previous_period',
        show_sparkline: false,
        show_title: true,
        show_description: false,
        compact_mode: false
      })
      Object.assign(gaugeConfig, {
        min_value: 0,
        max_value: 100,
        target_value: undefined,
        color_ranges: undefined,
        show_value: true,
        show_target: true,
        gauge_type: 'arc',
        thickness: 10
      })
    }

    isDirty.value = true
  })

  // Initialize with widget if provided
  if (initialWidget) {
    loadWidget(initialWidget)
  }

  return {
    // Form state
    form,
    selectedMetric,
    selectedMetricLabel,
    availableTables,
    dataMapping,
    isEmbeddedMetric,
    
    // Configs
    singleValueConfig,
    chartConfig,
    gaugeConfig,
    areaStackingType,
    
    // Preview state
    previewData,
    previewLoading,
    previewError,
    
    // Validation
    isValid,
    isDirty,
    isChartType,
    isInitialLoad,
    
    // Methods
    loadWidget,
    resetForm,
    onMetricSelect,
    updateDataMapping,
    buildWidgetData,
    updatePreview,
    buildAvailableTablesFromMetric
  }
}

