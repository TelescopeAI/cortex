import { ref, type Ref } from 'vue'

export interface DataModel {
  id: string
  name: string
  alias?: string
  description?: string
  version: number
  is_active: boolean
  parent_version_id?: string
  config: Record<string, any>
  is_valid: boolean
  validation_errors?: string[]
  metrics_count?: number // This comes from the API response, not the model itself
  created_at: string
  updated_at: string
}

export interface ModelFilters {
  search?: string
  dataSource?: string
  status?: 'valid' | 'invalid' | 'pending'
  sortBy?: 'name' | 'updated' | 'metrics_count' | 'validation_status'
  sortOrder?: 'asc' | 'desc'
}

export const useDataModels = () => {
  const { apiUrl } = useApi()
  const models: Ref<DataModel[]> = ref([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchModels = async (filters?: ModelFilters) => {
    loading.value = true
    error.value = null
    
    try {
      // Use the correct backend endpoint with proper URL construction
      const response = await $fetch(apiUrl('/api/v1/data/models'), {
        query: filters
      }) as { models: DataModel[], total_count: number, page: number, page_size: number }
      models.value = response.models || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch models'
      console.error('Failed to fetch models:', err)
    } finally {
      loading.value = false
    }
  }

  const getModel = async (id: string): Promise<DataModel | null> => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/data/models/${id}`)) as DataModel
      return response
    } catch (err) {
      console.error('Failed to fetch model:', err)
      return null
    }
  }

  const createModel = async (modelData: Partial<DataModel>): Promise<DataModel | null> => {
    try {
      const response = await $fetch(apiUrl('/api/v1/data/models'), {
        method: 'POST',
        body: modelData
      }) as DataModel
      // Add to local state
      models.value.push(response)
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create model'
      console.error('Failed to create model:', err)
      return null
    }
  }

  const updateModel = async (id: string, modelData: Partial<DataModel>): Promise<DataModel | null> => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/data/models/${id}`), {
        method: 'PUT',
        body: modelData
      }) as DataModel
      // Update local state
      const index = models.value.findIndex(m => m.id === id)
      if (index !== -1) {
        models.value[index] = response
      }
      return response
    } catch (err) {
      console.error('Failed to update model:', err)
      return null
    }
  }

  const deleteModel = async (id: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/data/models/${id}`), {
        method: 'DELETE'
      })
      // Remove from local state
      models.value = models.value.filter(m => m.id !== id)
      return true
    } catch (err) {
      console.error('Failed to delete model:', err)
      return false
    }
  }

  const executeModel = async (id: string, executionRequest: any) => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/data/models/${id}/execute`), {
        method: 'POST',
        body: executionRequest
      })
      return response
    } catch (err) {
      console.error('Failed to execute model:', err)
      throw err
    }
  }

  const validateModel = async (id: string) => {
    try {
      const response = await $fetch(apiUrl(`/api/v1/data/models/${id}/validate`), {
        method: 'POST',
        body: {
          validate_dependencies: true,
          validate_syntax: true
        }
      })
      return response
    } catch (err) {
      console.error('Failed to validate model:', err)
      throw err
    }
  }

  return {
    models: readonly(models),
    loading: readonly(loading),
    error: readonly(error),
    fetchModels,
    getModel,
    createModel,
    updateModel,
    deleteModel,
    executeModel,
    validateModel
  }
} 