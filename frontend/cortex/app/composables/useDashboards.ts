import { ref, type Ref, computed, readonly } from 'vue'
import type { Dashboard, DashboardView, DashboardWidget, StandardChartData } from '~/types/dashboards'

export interface DashboardFilters {
  search?: string
  type?: string
  sortBy?: 'name' | 'updated' | 'created' | 'type'
  sortOrder?: 'asc' | 'desc'
}

export interface CreateDashboardRequest {
  environment_id: string
  alias?: string
  name: string
  description?: string
  type: string
  views: CreateDashboardViewRequest[]
  default_view_index?: number
  tags?: string[]
}

export interface CreateDashboardViewRequest {
  name: string
  description?: string
  sections: CreateDashboardSectionRequest[]
  context_id?: string
}

export interface CreateDashboardSectionRequest {
  title?: string
  description?: string
  position: number
  widgets: CreateDashboardWidgetRequest[]
}

export interface CreateDashboardWidgetRequest {
  metric_id: string
  position: number
  grid_config: {
    columns: number
    rows: number
    min_columns?: number
    min_rows?: number
  }
  title?: string
  description?: string
  visualization: {
    type: string
    data_mapping: {
      x_axis: { field: string; type: string }
      y_axes: { field: string; type: string }[]
      series?: { split_by?: string; value_field?: string }
      category?: string
      value_field?: string
    }
    single_value_config?: {
      number_format: string
      prefix?: string
      suffix?: string
      show_comparison?: boolean
      show_trend?: boolean
      compact_mode?: boolean
    }
    gauge_config?: {
      min_value: number
      max_value: number
      target_value?: number
      show_value?: boolean
      show_target?: boolean
    }
    show_legend?: boolean
    show_grid?: boolean
    show_axes_labels?: boolean
    color_scheme?: string
    custom_colors?: string[]
  }
  metric_overrides?: {
    context_id?: string
    filters?: Record<string, any>
    parameters?: Record<string, any>
    limit?: number
  }
}

export interface DashboardExecutionResult {
  dashboard_id: string
  view_id: string
  view_execution: {
    view_id: string
    widgets: WidgetExecutionResult[]
    total_execution_time_ms?: number
    errors: string[]
  }
  total_execution_time_ms?: number
}

export interface WidgetExecutionResult {
  widget_id: string
  data: StandardChartData
  execution_time_ms?: number
  error?: string
}

export function useDashboards() {
  const { apiUrl } = useApi()
  
  // State
  const dashboards = ref<Dashboard[]>([])
  const currentDashboard = ref<Dashboard | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const dashboardsCount = computed(() => dashboards.value.length)
  
  // API Methods
  async function fetchDashboards(environmentId: string, filters?: DashboardFilters) {
    loading.value = true
    error.value = null
    
    try {
      let url = apiUrl(`/api/v1/environments/${environmentId}/dashboards`)
      
      if (filters) {
        const params = new URLSearchParams()
        if (filters.search) params.append('search', filters.search)
        if (filters.type) params.append('type', filters.type)
        if (filters.sortBy) params.append('sortBy', filters.sortBy)
        if (filters.sortOrder) params.append('sortOrder', filters.sortOrder)
        
        if (params.toString()) {
          url += `?${params.toString()}`
        }
      }
      
      const response = await $fetch<{ dashboards: Dashboard[]; total: number }>(url)
      dashboards.value = response.dashboards
      return response
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch dashboards'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchDashboard(dashboardId: string) {
    loading.value = true
    error.value = null
    
    try {
      const dashboard = await $fetch<Dashboard>(apiUrl(`/api/v1/dashboards/${dashboardId}`))
      currentDashboard.value = dashboard
      return dashboard
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDashboard(dashboardData: CreateDashboardRequest) {
    loading.value = true
    error.value = null
    
    try {
      const dashboard = await $fetch<Dashboard>(apiUrl(`/api/v1/dashboards`), {
        method: 'POST',
        body: dashboardData
      })
      
      dashboards.value.push(dashboard)
      return dashboard
    } catch (err: any) {
      error.value = err.message || 'Failed to create dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateDashboard(dashboardId: string, updates: Partial<CreateDashboardRequest>) {
    loading.value = true
    error.value = null
    
    console.log('updateDashboard called with:', updates)
    
    try {
      const dashboard = await $fetch<Dashboard>(apiUrl(`/api/v1/dashboards/${dashboardId}`), {
        method: 'PUT',
        body: updates
      })
      
      const index = dashboards.value.findIndex(d => d.id === dashboardId)
      if (index !== -1) {
        dashboards.value[index] = dashboard
      }
      
      if (currentDashboard.value?.id === dashboardId) {
        currentDashboard.value = dashboard
      }
      
      return dashboard
    } catch (err: any) {
      error.value = err.message || 'Failed to update dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteDashboard(dashboardId: string) {
    loading.value = true
    error.value = null
    
    try {
      await $fetch(apiUrl(`/api/v1/dashboards/${dashboardId}`), {
        method: 'DELETE'
      })
      
      dashboards.value = dashboards.value.filter(d => d.id !== dashboardId)
      
      if (currentDashboard.value?.id === dashboardId) {
        currentDashboard.value = null
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function setDefaultView(dashboardId: string, viewId: string) {
    loading.value = true
    error.value = null
    
    try {
      const dashboard = await $fetch<Dashboard>(apiUrl(`/api/v1/dashboards/${dashboardId}/default-view`), {
        method: 'POST',
        body: { view_id: viewId }
      })
      
      const index = dashboards.value.findIndex(d => d.id === dashboardId)
      if (index !== -1) {
        dashboards.value[index] = dashboard
      }
      
      if (currentDashboard.value?.id === dashboardId) {
        currentDashboard.value = dashboard
      }
      
      return dashboard
    } catch (err: any) {
      error.value = err.message || 'Failed to set default view'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function executeDashboard(dashboardId: string, viewId?: string) {
    loading.value = true
    error.value = null
    
    try {
      let url = apiUrl(`/api/v1/dashboards/${dashboardId}/execute`)
      if (viewId) {
        url += `?view_id=${viewId}`
      }
      
      const result = await $fetch<DashboardExecutionResult>(url, {
        method: 'POST'
      })
      
      return result
    } catch (err: any) {
      error.value = err.message || 'Failed to execute dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function executeWidget(dashboardId: string, viewId: string, widgetId: string) {
    loading.value = true
    error.value = null
    
    try {
      const result = await $fetch<WidgetExecutionResult>(
        apiUrl(`/api/v1/dashboards/${dashboardId}/views/${viewId}/widgets/${widgetId}/execute`),
        { method: 'POST' }
      )
      
      return result
    } catch (err: any) {
      error.value = err.message || 'Failed to execute widget'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function previewDashboardConfig(dashboardId: string, config: any) {
    loading.value = true
    error.value = null
    
    try {
      // Ensure the config has all required fields
      const previewConfig = {
        id: dashboardId,
        views: config.views?.map((view: any) => ({
          alias: view.alias || 'preview_view',
          title: view.title || view.name || 'Preview View',
          description: view.description || '',
          context_id: view.context_id,
          sections: view.sections?.map((section: any, sectionIndex: number) => ({
            alias: section.alias || `preview_section_${sectionIndex}`,
            title: section.title || 'Preview Section',
            description: section.description || '',
            position: section.position || 0,
            widgets: section.widgets?.map((widget: any, index: number) => ({
              alias: widget.alias || `preview_widget_${index}`,
              section_alias: section.alias || `preview_section_${index}`,
              metric_id: widget.metric_id,
              title: widget.title || 'Preview Widget',
              description: widget.description || '',
              position: widget.position || index,
              grid_config: widget.grid_config || { columns: 3, rows: 2 },
              visualization: {
                type: widget.visualization?.type || 'single_value',
                data_mapping: {
                  x_axis: widget.visualization?.data_mapping?.x_axis ? {
                    field: widget.visualization.data_mapping.x_axis.field || 'x',
                    // omit data_type to allow backend inference
                    label: widget.visualization.data_mapping.x_axis.label || null,
                    required: widget.visualization.data_mapping.x_axis.required || false
                  } : null,
                  // Support multi-Y via y_axes
                  y_axes: Array.isArray(widget.visualization?.data_mapping?.y_axes)
                    ? widget.visualization.data_mapping.y_axes.map((m:any) => ({
                        field: m.field,
                        // omit data_type to allow backend inference
                        label: m.label || null,
                        required: m.required ?? true
                      }))
                    : [],
                  value_field: widget.visualization?.data_mapping?.value_field ? {
                    field: widget.visualization.data_mapping.value_field.field,
                    label: widget.visualization.data_mapping.value_field.label || null,
                    required: widget.visualization.data_mapping.value_field.required ?? true
                  } : undefined,
                  category_field: widget.visualization?.data_mapping?.category_field ? {
                    field: widget.visualization.data_mapping.category_field.field,
                    label: widget.visualization.data_mapping.category_field.label || null,
                    required: widget.visualization.data_mapping.category_field.required ?? true
                  } : undefined,
                  series_field: widget.visualization?.data_mapping?.series_field ? {
                    field: widget.visualization.data_mapping.series_field.field,
                    label: widget.visualization.data_mapping.series_field.label || null,
                    required: widget.visualization.data_mapping.series_field.required ?? false
                  } : undefined,
                  columns: widget.visualization?.data_mapping?.columns
                },
                single_value_config: widget.visualization?.single_value_config,
                gauge_config: widget.visualization?.gauge_config
              }
            })) || []
          })) || []
        })) || []
      }
      
      const result = await $fetch<DashboardExecutionResult>(
        apiUrl(`/api/v1/dashboards/${dashboardId}/preview`),
        {
          method: 'POST',
          body: previewConfig
        }
      )
      
      return result
    } catch (err: any) {
      error.value = err.message || 'Failed to preview dashboard'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Utility functions
  function getDefaultView(dashboard: Dashboard): DashboardView | null {
    return dashboard.views.find(view => view.alias === dashboard.default_view) || null
  }

  function getViewById(dashboard: Dashboard, viewAlias: string): DashboardView | null {
    return dashboard.views.find(view => view.alias === viewAlias) || null
  }

  function getWidgetById(view: DashboardView, widgetAlias: string): DashboardWidget | null {
    for (const section of view.sections) {
      const widget = section.widgets.find(w => w.alias === widgetAlias)
      if (widget) return widget
    }
    return null
  }

  return {
    // State
    dashboards: readonly(dashboards),
    currentDashboard: readonly(currentDashboard),
    loading: readonly(loading),
    error: readonly(error),
    
    // Computed
    dashboardsCount,
    
    // Methods
    fetchDashboards,
    fetchDashboard,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    setDefaultView,
    executeDashboard,
    executeWidget,
    previewDashboardConfig,
    
    // Utilities
    getDefaultView,
    getViewById,
    getWidgetById
  }
}