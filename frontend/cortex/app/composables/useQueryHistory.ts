import { ref, type Ref } from 'vue'
import { useApi } from './useApi'

export interface QueryLogEntry {
  id: string
  metric_id: string
  data_model_id: string
  query: string
  parameters: Record<string, any> | null
  context_id: string | null
  meta: Record<string, any> | null
  cache_mode: string | null
  query_hash: string | null
  duration: number
  row_count: number | null
  success: boolean
  error_message: string | null
  executed_at: string
}

export interface QueryHistoryFilters {
  limit?: number
  metric_id?: string
  data_model_id?: string
  dashboard_id?: string
  success?: boolean | null
  cache_mode?: string
  executed_after?: string
  executed_before?: string
}

export interface QueryHistoryResponse {
  entries: QueryLogEntry[]
  total_count: number
}

export const useQueryHistory = () => {
  const { apiUrl } = useApi()
  const queryHistory: Ref<QueryLogEntry[]> = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  const fetchQueryHistory = async (filters?: QueryHistoryFilters) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<QueryHistoryResponse>(apiUrl('/api/v1/query/history'), {
        method: 'POST',
        body: filters || {}
      })
      queryHistory.value = response.entries || []
      totalCount.value = response.total_count || 0
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch query history'
      console.error('Failed to fetch query history:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchMetricQueryHistory = async (metricId: string, filters?: Partial<QueryHistoryFilters>) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await $fetch<QueryHistoryResponse>(apiUrl('/api/v1/query/history'), {
        method: 'POST',
        body: {
          metric_id: metricId,
          success: filters?.success
        }
      })
      queryHistory.value = response.entries || []
      totalCount.value = response.total_count || 0
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch metric query history'
      console.error('Failed to fetch metric query history:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchDashboardQueryHistory = async (dashboardId: string, filters?: Partial<QueryHistoryFilters>) => {
    loading.value = true
    error.value = null
    
    try {
      // For dashboard queries, we'll filter by data_model_id if available
      const response = await $fetch<QueryHistoryResponse>(apiUrl('/api/v1/query/history'), {
        method: 'POST',
        body: {
          ...filters,
          dashboard_id: dashboardId
        }
      })
      queryHistory.value = response.entries || []
      totalCount.value = response.total_count || 0
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch dashboard query history'
      console.error('Failed to fetch dashboard query history:', err)
    } finally {
      loading.value = false
    }
  }

  const getExecutionStats = async (metricId?: string, timeRange: string = '7d') => {
    try {
      const response = await $fetch(apiUrl('/api/v1/query/history/stats'), {
        method: 'POST',
        body: {
          metric_id: metricId,
          time_range: timeRange
        }
      })
      return response
    } catch (err) {
      console.error('Failed to fetch execution stats:', err)
      return null
    }
  }

  const clearHistory = async (olderThan?: string) => {
    try {
      const response = await $fetch(apiUrl('/api/v1/query/history/clear'), {
        method: 'POST',
        body: { older_than: olderThan }
      })
      return response
    } catch (err) {
      console.error('Failed to clear query history:', err)
      return null
    }
  }

  const refreshHistory = () => {
    // This will be called when we need to refresh the current view
    // The specific fetch method should be called based on the current context
    if (queryHistory.value.length > 0) {
      // Re-fetch with current filters - this is a placeholder
      // The actual implementation should be context-aware
      console.log('Refreshing query history...')
    }
  }

  return {
    queryHistory,
    loading,
    error,
    totalCount,
    fetchQueryHistory,
    fetchMetricQueryHistory,
    fetchDashboardQueryHistory,
    getExecutionStats,
    clearHistory,
    refreshHistory
  }
}
