import { ref, type Ref } from 'vue'
import type { SemanticOrderSequence } from '~/types/order'

export interface SemanticMetric {
  id: string
  environment_id: string
  name: string
  alias?: string
  title?: string
  description?: string
  data_model_id: string
  data_source_id?: string
  data_model_name?: string
  query?: string
  table_name?: string
  limit?: number
  grouped?: boolean
  ordered?: boolean
  parameters?: MetricParameter[]
  public: boolean
  model_version?: number
  measures?: any[]
  dimensions?: any[]
  joins?: any[]
  aggregations?: any[]
  filters?: any[]
  order?: SemanticOrderSequence[]
  output_formats?: any[]
  extends?: string
  add?: Record<string, any>
  override?: Record<string, any>
  refresh_key?: any
  meta?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MetricParameter {
  name: string
  type: string
  description?: string
  default_value?: any
  required: boolean
}

export interface MetricFilters {
  search?: string
  model?: string
  status?: 'valid' | 'invalid' | 'pending'
  public?: boolean
  sortBy?: 'name' | 'updated' | 'model' | 'validation_status'
  sortOrder?: 'asc' | 'desc'
}

export interface ExecutionRequest {
  parameters?: Record<string, any>
  output_format?: string
  context_id?: string
  limit?: number
  offset?: number
  grouped?: boolean
  ordered?: boolean
  modifiers?: any
  cache?: any
  preview?: boolean
}

export const useMetrics = () => {
  const { apiUrl } = useApi()
  const metrics: Ref<SemanticMetric[]> = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchMetrics = async (environmentId: string, filters?: MetricFilters) => {
    loading.value = true
    error.value = null
    
    try {
      // Use the correct backend endpoint with proper URL construction
      const response = await $fetch<{ metrics: SemanticMetric[], total_count: number, page: number, page_size: number }>(apiUrl('/api/v1/metrics'), {
        query: { environment_id: environmentId, ...filters }
      })
      metrics.value = response.metrics || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch metrics'
      console.error('Failed to fetch metrics:', err)
    } finally {
      loading.value = false
    }
  }

  const getMetric = async (id: string, environmentId: string): Promise<SemanticMetric | null> => {
    try {
      const response = await $fetch<SemanticMetric>(apiUrl(`/api/v1/metrics/${id}`), {
        query: { environment_id: environmentId }
      })
      return response
    } catch (err) {
      console.error('Failed to fetch metric:', err)
      return null
    }
  }

  const createMetric = async (metricData: Partial<SemanticMetric>): Promise<SemanticMetric | null> => {
    try {
      const response = await $fetch<SemanticMetric>(apiUrl('/api/v1/metrics'), {
        method: 'POST',
        body: metricData
      })
      // Add to local state
      metrics.value.push(response)
      return response
    } catch (err) {
      console.error('Failed to create metric:', err)
      return null
    }
  }

  const updateMetric = async (id: string, environmentId: string, metricData: Partial<SemanticMetric>): Promise<SemanticMetric | null> => {
    try {
      const response = await $fetch<SemanticMetric>(apiUrl(`/api/v1/metrics/${id}`), {
        method: 'PUT',
        body: { environment_id: environmentId, ...metricData }
      })
      // Update local state
      const index = metrics.value.findIndex(m => m.id === id)
      if (index !== -1) {
        metrics.value[index] = response
      }
      return response
    } catch (err) {
      console.error('Failed to update metric:', err)
      return null
    }
  }

  const deleteMetric = async (id: string, environmentId: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/metrics/${id}`), {
        method: 'DELETE',
        query: { environment_id: environmentId }
      })
      // Remove from local state
      metrics.value = metrics.value.filter(m => m.id !== id)
      return true
    } catch (err) {
      console.error('Failed to delete metric:', err)
      return false
    }
  }

  const executeMetric = async (id: string, executionRequest: ExecutionRequest, preview: boolean = false) => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/metrics/${id}/execute`), {
        method: 'POST',
        body: {
          ...executionRequest,
          preview
        }
      })
      return response
    } catch (err) {
      console.error('Failed to execute metric:', err)
      throw err
    }
  }

  const cloneMetric = async (id: string, cloneRequest: { name: string; alias?: string }) => {
    try {
      const response = await $fetch<SemanticMetric>(apiUrl(`/api/v1/metrics/${id}/clone`), {
        method: 'POST',
        body: cloneRequest
      })
      // Add to local state
      metrics.value.push(response)
      return response
    } catch (err) {
      console.error('Failed to clone metric:', err)
      throw err
    }
  }

  const getMetricVersions = async (id: string) => {
    try {
      const response = await $fetch<{ versions: any[], total_count: number }>(apiUrl(`/api/v1/metrics/${id}/versions`))
      return response.versions || []
    } catch (err) {
      console.error('Failed to fetch metric versions:', err)
      return []
    }
  }

  const getMetricsForModel = async (modelId: string, environmentId: string) => {
    try {
      const response = await $fetch<{ metrics: SemanticMetric[], total_count: number, page: number, page_size: number }>(apiUrl('/api/v1/metrics'), {
        query: { environment_id: environmentId, data_model_id: modelId }
      })
      return response.metrics || []
    } catch (err) {
      console.error('Failed to fetch metrics for model:', err)
      return []
    }
  }

  type RecommendOptions = {
    select?: {
      include?: Record<string, string[]>
      exclude?: Record<string, string[]>
    }
    metricTypes?: string[]
    timeWindows?: number[]
    grains?: string[]
  }

  type RecommendResult = {
    metrics: SemanticMetric[]
    total_count?: number
    metadata?: any
  }

  const recommendMetrics = async (
    environmentId: string,
    dataSourceId: string,
    dataModelId: string,
    options: RecommendOptions = {}
  ): Promise<RecommendResult> => {
    try {
      const response = await $fetch<{ metrics: SemanticMetric[], total_count: number, metadata?: any }>(
        apiUrl('/api/v1/metrics/recommendations'),
        {
          method: 'POST',
          body: {
            environment_id: environmentId,
            data_source_id: dataSourceId,
            data_model_id: dataModelId,
            select: options.select,
            metric_types: options.metricTypes,
            time_windows: options.timeWindows,
            grains: options.grains,
          }
        }
      )
      return {
        metrics: response.metrics || [],
        total_count: response.total_count,
        metadata: response.metadata
      }
    } catch (err) {
      console.error('Failed to generate metric recommendations:', err)
      throw err
    }
  }

  return {
    metrics: readonly(metrics),
    loading: readonly(loading),
    error: readonly(error),
    fetchMetrics,
    getMetric,
    createMetric,
    updateMetric,
    deleteMetric,
    executeMetric,
    cloneMetric,
    getMetricVersions,
    getMetricsForModel,
    recommendMetrics
  }
} 