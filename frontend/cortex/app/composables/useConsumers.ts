import { ref, computed } from 'vue'
import { useStorage } from '@vueuse/core'

interface Consumer {
  id: string
  environment_id: string
  first_name: string
  last_name: string
  email: string
  organization?: string
  properties?: any
  created_at: string
  updated_at: string
}

interface ConsumerCreateRequest {
  environment_id: string
  first_name: string
  last_name: string
  email: string
  organization?: string
  properties?: any
}

interface ConsumerUpdateRequest {
  first_name?: string
  last_name?: string
  email?: string
  organization?: string
  properties?: any
}

export const useConsumers = () => {
  const { apiUrl } = useApi()
  const selectedEnvironmentId = useStorage<string | null>('selectedEnvironmentId', null)
  
  const consumers = ref<Consumer[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const fetchConsumers = async () => {
    if (!selectedEnvironmentId.value) {
      consumers.value = []
      return
    }
    
    loading.value = true
    error.value = null
    try {
      const response = await $fetch<Consumer[]>(apiUrl(`/api/v1/environments/${selectedEnvironmentId.value}/consumers`))
      consumers.value = response
    } catch (err) {
      error.value = err as Error
      console.error('Failed to fetch consumers:', err)
    } finally {
      loading.value = false
    }
  }

  const getConsumer = async (id: string): Promise<Consumer | null> => {
    try {
      const response = await $fetch<Consumer>(apiUrl(`/api/v1/consumers/${id}`))
      return response
    } catch (err) {
      console.error('Failed to fetch consumer:', err)
      return null
    }
  }

  const createConsumer = async (data: ConsumerCreateRequest): Promise<Consumer | null> => {
    try {
      const response = await $fetch<Consumer>(apiUrl('/api/v1/consumers'), {
        method: 'POST',
        body: data
      })
      return response
    } catch (err) {
      console.error('Failed to create consumer:', err)
      throw err
    }
  }

  const updateConsumer = async (id: string, data: ConsumerUpdateRequest): Promise<Consumer | null> => {
    try {
      const response = await $fetch<Consumer>(apiUrl(`/api/v1/consumers/${id}`), {
        method: 'PUT',
        body: data
      })
      return response
    } catch (err) {
      console.error('Failed to update consumer:', err)
      throw err
    }
  }

  const deleteConsumer = async (id: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/consumers/${id}`), {
        method: 'DELETE'
      })
      return true
    } catch (err) {
      console.error('Failed to delete consumer:', err)
      return false
    }
  }

  const getConsumersByEnvironment = async (environmentId: string): Promise<Consumer[]> => {
    try {
      const response = await $fetch<Consumer[]>(apiUrl(`/api/v1/environments/${environmentId}/consumers`))
      return response
    } catch (err) {
      console.error('Failed to fetch consumers by environment:', err)
      return []
    }
  }

  return {
    consumers: computed(() => consumers.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchConsumers,
    getConsumer,
    createConsumer,
    updateConsumer,
    deleteConsumer,
    getConsumersByEnvironment
  }
} 