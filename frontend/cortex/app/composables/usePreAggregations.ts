import { ref, type Ref } from 'vue'

export interface DataSourceRef {
  data_source_id: string
  engine: string
  schema?: string
  table: string
}

export interface SemanticMeasure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
}

export interface SemanticDimension {
  name: string
  description?: string
  query: string
  table?: string
  formatting?: any[]
}

export interface PreAggregationSpec {
  id: string
  name?: string
  metric_id: string
  source: DataSourceRef
  dimensions: SemanticDimension[]
  measures: SemanticMeasure[]
  filters?: PreAggregationFilter[]
  partitions?: PreAggregationPartitionConfig
  refresh?: RefreshPolicy
  storage?: PreAggregationStorageConfig
  build?: PreAggregationBuildConfig
  type: PreAggregationType
  created_at: string
  updated_at: string
}

export interface PreAggregationFilter {
  dimension: string
  operator: FilterOperator
  values: any[]
}

export interface PreAggregationPartitionConfig {
  dimension: string
  grain: TimeGrain
}

export interface RefreshPolicy {
  type: RefreshType
  every?: string
  sql?: string
  max?: string
}

export interface PreAggregationStorageConfig {
  mode: PreAggregationStorageMode
  schema?: string
  table_prefix?: string
  remote_config?: Record<string, any>
}

export interface PreAggregationBuildConfig {
  strategy: PreAggregationBuildStrategy
  select_sql?: string
}

export interface PreAggregationStatus {
  spec_id: string
  status: 'pending' | 'building' | 'completed' | 'failed'
  last_built_at?: string
  next_refresh_at?: string
  error_message?: string
  row_count?: number
  storage_size_bytes?: number
}

export enum PreAggregationType {
  ROLLUP = 'rollup',
  ORIGINAL_SQL = 'original_sql',
  ROLLUP_LAMBDA = 'rollup_lambda'
}

export enum FilterOperator {
  EQUALS = 'equals',
  NOT_EQUALS = 'not_equals',
  IN = 'in',
  NOT_IN = 'not_in',
  GREATER_THAN = 'greater_than',
  LESS_THAN = 'less_than',
  GREATER_THAN_OR_EQUAL = 'greater_than_or_equal',
  LESS_THAN_OR_EQUAL = 'less_than_or_equal',
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  STARTS_WITH = 'starts_with',
  ENDS_WITH = 'ends_with'
}

export enum TimeGrain {
  SECOND = 'second',
  MINUTE = 'minute',
  HOUR = 'hour',
  DAY = 'day',
  WEEK = 'week',
  MONTH = 'month',
  QUARTER = 'quarter',
  YEAR = 'year'
}

export enum RefreshType {
  EVERY = 'every',
  SQL = 'sql',
  MAX = 'max'
}

export enum PreAggregationStorageMode {
  SOURCE = 'source',
  REMOTE = 'remote'
}

export enum PreAggregationBuildStrategy {
  MATERIALIZED_VIEW = 'materialized_view',
  CTAS = 'ctas',
  SWAP = 'swap'
}

export interface PreAggregationUpsertRequest {
  id?: string
  name?: string
  metric_id: string
  source: DataSourceRef
  dimensions: SemanticDimension[]
  measures: SemanticMeasure[]
  filters?: PreAggregationFilter[]
  partitions?: PreAggregationPartitionConfig
  refresh?: RefreshPolicy
  storage?: PreAggregationStorageConfig
  build?: PreAggregationBuildConfig
  type: PreAggregationType
}

export interface PreAggregationFilters {
  search?: string
  metric_id?: string
  status?: 'pending' | 'building' | 'completed' | 'failed'
  type?: PreAggregationType
  sortBy?: 'name' | 'updated' | 'metric' | 'status'
  sortOrder?: 'asc' | 'desc'
}

export const usePreAggregations = () => {
  const { apiUrl } = useApi()
  const specs: Ref<PreAggregationSpec[]> = ref([])
  const statuses: Ref<PreAggregationStatus[]> = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchSpecs = async (filters?: PreAggregationFilters) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<{ specs: PreAggregationSpec[], total_count: number }>(apiUrl('/api/v1/pre-aggregations'), {
        query: filters
      })
      specs.value = response.specs || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch pre-aggregation specs'
      console.error('Failed to fetch pre-aggregation specs:', err)
    } finally {
      loading.value = false
    }
  }

  const getSpec = async (id: string): Promise<PreAggregationSpec | null> => {
    try {
      const response = await $fetch<PreAggregationSpec>(apiUrl(`/api/v1/pre-aggregations/${id}`))
      return response
    } catch (err) {
      console.error('Failed to fetch pre-aggregation spec:', err)
      return null
    }
  }

  const upsertSpec = async (specData: PreAggregationUpsertRequest): Promise<PreAggregationSpec | null> => {
    try {
      const response = await $fetch<PreAggregationSpec>(apiUrl('/api/v1/pre-aggregations'), {
        method: 'POST',
        body: specData
      })
      // Add or update in local state
      const existingIndex = specs.value.findIndex(s => s.id === response.id)
      if (existingIndex !== -1) {
        specs.value[existingIndex] = response
      } else {
        specs.value.push(response)
      }
      return response
    } catch (err) {
      console.error('Failed to upsert pre-aggregation spec:', err)
      return null
    }
  }

  const deleteSpec = async (id: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/pre-aggregations/${id}`), {
        method: 'DELETE'
      })
      // Remove from local state
      specs.value = specs.value.filter(s => s.id !== id)
      return true
    } catch (err) {
      console.error('Failed to delete pre-aggregation spec:', err)
      return false
    }
  }

  const refreshSpec = async (id: string, dryRun: boolean = false): Promise<any> => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/pre-aggregations/${id}/refresh`), {
        method: 'POST',
        body: { dry_run: dryRun }
      })
      return response
    } catch (err) {
      console.error('Failed to refresh pre-aggregation spec:', err)
      throw err
    }
  }

  const getStatus = async (id: string): Promise<PreAggregationStatus | null> => {
    try {
      const response = await $fetch<PreAggregationStatus>(apiUrl(`/api/v1/pre-aggregations/${id}/status`))
      return response
    } catch (err) {
      console.error('Failed to fetch pre-aggregation status:', err)
      return null
    }
  }

    const fetchAllStatuses = async () => {
    try {
      // Only fetch statuses for specs that have valid IDs
      const validSpecs = specs.value.filter(spec => spec.id && spec.id !== 'undefined')
      if (validSpecs.length === 0) return
      
      const statusPromises = validSpecs.map(spec => getStatus(spec.id))
      const results = await Promise.allSettled(statusPromises)

      statuses.value = results
        .filter((result): result is PromiseFulfilledResult<PreAggregationStatus> =>
          result.status === 'fulfilled' && result.value !== null
        )
        .map(result => result.value)
    } catch (err) {
      console.error('Failed to fetch pre-aggregation statuses:', err)
    }
  }

  const getStatusForSpec = (specId: string): PreAggregationStatus | null => {
    return statuses.value.find(status => status.spec_id === specId) || null
  }

  return {
    specs,
    statuses,
    loading: readonly(loading),
    error: readonly(error),
    fetchSpecs,
    getSpec,
    upsertSpec,
    deleteSpec,
    refreshSpec,
    getStatus,
    fetchAllStatuses,
    getStatusForSpec
  }
}
