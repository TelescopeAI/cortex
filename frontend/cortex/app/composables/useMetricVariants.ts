import { ref, readonly, type Ref } from 'vue'
import type {
  SemanticMetricVariant,
  MetricVariantFilters,
  MetricVariantExecutionRequest,
  MetricVariantExecutionResponse,
  MetricVariantListResponse
} from '~/types/metric_variants'

export const useMetricVariants = () => {
  const { apiUrl } = useApi()

  // State
  const variants: Ref<SemanticMetricVariant[]> = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch all variants with optional filters
   */
  const fetchVariants = async (environmentId: string, filters?: MetricVariantFilters) => {
    loading.value = true
    error.value = null

    try {
      const response = await $fetch<MetricVariantListResponse>(
        apiUrl('/api/v1/metrics/variants'),
        {
          query: {
            environment_id: environmentId,
            ...filters
          }
        }
      )
      variants.value = response.variants || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch variants'
      console.error('Failed to fetch variants:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch variants for a specific source metric
   */
  const getVariantsForMetric = async (metricId: string, environmentId: string): Promise<SemanticMetricVariant[]> => {
    try {
      const response = await $fetch<MetricVariantListResponse>(
        apiUrl('/api/v1/metrics/variants'),
        {
          query: {
            environment_id: environmentId,
            source_metric_id: metricId
          }
        }
      )
      return response.variants || []
    } catch (err) {
      console.error('Failed to fetch variants for metric:', err)
      return []
    }
  }

  /**
   * Fetch a single variant by ID
   */
  const getVariant = async (variantId: string, environmentId: string): Promise<SemanticMetricVariant | null> => {
    try {
      const response = await $fetch<SemanticMetricVariant>(
        apiUrl(`/api/v1/metrics/variants/${variantId}`),
        {
          query: { environment_id: environmentId }
        }
      )
      return response
    } catch (err) {
      console.error('Failed to fetch variant:', err)
      return null
    }
  }

  /**
   * Create a new variant
   */
  const createVariant = async (
    environmentId: string,
    variantData: Partial<SemanticMetricVariant>
  ): Promise<SemanticMetricVariant | null> => {
    try {
      const response = await $fetch<SemanticMetricVariant>(
        apiUrl('/api/v1/metrics/variants'),
        {
          method: 'POST',
          body: {
            environment_id: environmentId,
            ...variantData
          }
        }
      )
      // Add to local state
      variants.value.push(response)
      return response
    } catch (err) {
      console.error('Failed to create variant:', err)
      return null
    }
  }

  /**
   * Update an existing variant
   */
  const updateVariant = async (
    variantId: string,
    environmentId: string,
    variantData: Partial<SemanticMetricVariant>
  ): Promise<SemanticMetricVariant | null> => {
    try {
      const response = await $fetch<SemanticMetricVariant>(
        apiUrl(`/api/v1/metrics/variants/${variantId}`),
        {
          method: 'PUT',
          body: {
            environment_id: environmentId,
            ...variantData
          }
        }
      )
      // Update local state
      const index = variants.value.findIndex(v => v.id === variantId)
      if (index !== -1) {
        variants.value[index] = response
      }
      return response
    } catch (err) {
      console.error('Failed to update variant:', err)
      return null
    }
  }

  /**
   * Delete a variant
   */
  const deleteVariant = async (variantId: string, environmentId: string): Promise<boolean> => {
    try {
      await $fetch(
        apiUrl(`/api/v1/metrics/variants/${variantId}`),
        {
          method: 'DELETE',
          query: { environment_id: environmentId }
        }
      )
      // Remove from local state
      variants.value = variants.value.filter(v => v.id !== variantId)
      return true
    } catch (err) {
      console.error('Failed to delete variant:', err)
      return false
    }
  }

  /**
   * Execute a variant (compiles and executes)
   */
  const executeVariant = async (
    variantId: string,
    executionRequest: MetricVariantExecutionRequest,
    preview: boolean = false
  ): Promise<MetricVariantExecutionResponse | null> => {
    try {
      const response = await $fetch<MetricVariantExecutionResponse>(
        apiUrl(`/api/v1/metrics/variants/${variantId}/execute`),
        {
          method: 'POST',
          body: {
            ...executionRequest,
            preview
          }
        }
      )
      return response
    } catch (err) {
      console.error('Failed to execute variant:', err)
      throw err
    }
  }

  /**
   * Clone a variant
   */
  const cloneVariant = async (
    variantId: string,
    cloneRequest: { name: string; alias?: string; description?: string }
  ): Promise<SemanticMetricVariant | null> => {
    try {
      const response = await $fetch<SemanticMetricVariant>(
        apiUrl(`/api/v1/metrics/variants/${variantId}/clone`),
        {
          method: 'POST',
          body: cloneRequest
        }
      )
      // Add to local state
      variants.value.push(response)
      return response
    } catch (err) {
      console.error('Failed to clone variant:', err)
      throw err
    }
  }

  /**
   * Reset variant overrides to match source
   */
  const resetVariant = async (variantId: string): Promise<SemanticMetricVariant | null> => {
    try {
      const response = await $fetch<SemanticMetricVariant>(
        apiUrl(`/api/v1/metrics/variants/${variantId}/reset`),
        {
          method: 'POST'
        }
      )
      // Update local state
      const index = variants.value.findIndex(v => v.id === variantId)
      if (index !== -1) {
        variants.value[index] = response
      }
      return response
    } catch (err) {
      console.error('Failed to reset variant:', err)
      return null
    }
  }

  /**
   * Detach variant (convert to standalone metric)
   */
  const detachVariant = async (variantId: string): Promise<any | null> => {
    try {
      const response = await $fetch(
        apiUrl(`/api/v1/metrics/variants/${variantId}/detach`),
        {
          method: 'POST'
        }
      )
      // Remove from variants state since it's now a standalone metric
      variants.value = variants.value.filter(v => v.id !== variantId)
      return response
    } catch (err) {
      console.error('Failed to detach variant:', err)
      return null
    }
  }

  /**
   * Override source metric with variant's resolved state
   */
  const overrideSource = async (variantId: string): Promise<any | null> => {
    try {
      const response = await $fetch(
        apiUrl(`/api/v1/metrics/variants/${variantId}/override-source`),
        {
          method: 'POST'
        }
      )
      return response
    } catch (err) {
      console.error('Failed to override source:', err)
      return null
    }
  }

  /**
   * Get resolved (compiled) metric from variant
   */
  const getResolvedMetric = async (variantId: string, environmentId: string): Promise<any | null> => {
    try {
      const response = await $fetch(
        apiUrl(`/api/v1/metrics/variants/${variantId}/resolved`),
        {
          query: { environment_id: environmentId }
        }
      )
      return response
    } catch (err) {
      console.error('Failed to fetch resolved metric:', err)
      return null
    }
  }

  return {
    // State
    variants: readonly(variants),
    loading: readonly(loading),
    error: readonly(error),

    // Methods
    fetchVariants,
    getVariantsForMetric,
    getVariant,
    createVariant,
    updateVariant,
    deleteVariant,
    executeVariant,
    cloneVariant,
    resetVariant,
    detachVariant,
    overrideSource,
    getResolvedMetric
  }
}
