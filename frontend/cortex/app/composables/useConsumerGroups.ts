import { ref, computed } from 'vue'
import { useStorage } from '@vueuse/core'

interface ConsumerGroup {
  id: string
  environment_id: string
  name: string
  description?: string
  alias?: string
  properties?: any
  consumers?: any[]
  created_at: string
  updated_at: string
}

interface ConsumerGroupCreateRequest {
  environment_id: string
  name: string
  description?: string
  alias?: string
  properties?: any
}

interface ConsumerGroupUpdateRequest {
  name?: string
  description?: string
  alias?: string
  properties?: any
}

export const useConsumerGroups = () => {
  const { apiUrl } = useApi()
  const selectedEnvironmentId = useStorage<string | null>('selectedEnvironmentId', null)
  
  const consumerGroups = ref<ConsumerGroup[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const fetchConsumerGroups = async () => {
    if (!selectedEnvironmentId.value) {
      consumerGroups.value = []
      return
    }
    
    loading.value = true
    error.value = null
    try {
      const response = await $fetch<ConsumerGroup[]>(apiUrl(`/api/v1/environments/${selectedEnvironmentId.value}/consumers/groups`))
      consumerGroups.value = response
    } catch (err) {
      error.value = err as Error
      console.error('Failed to fetch consumer groups:', err)
    } finally {
      loading.value = false
    }
  }

  const getConsumerGroup = async (id: string): Promise<ConsumerGroup | null> => {
    try {
      const response = await $fetch<ConsumerGroup>(apiUrl(`/api/v1/consumers/groups/${id}/detail`))
      return response
    } catch (err) {
      console.error('Failed to fetch consumer group:', err)
      return null
    }
  }

  const createConsumerGroup = async (data: ConsumerGroupCreateRequest): Promise<ConsumerGroup | null> => {
    try {
      const response = await $fetch<ConsumerGroup>(apiUrl('/api/v1/consumers/groups'), {
        method: 'POST',
        body: data
      })
      return response
    } catch (err) {
      console.error('Failed to create consumer group:', err)
      throw err
    }
  }

  const updateConsumerGroup = async (id: string, data: ConsumerGroupUpdateRequest): Promise<ConsumerGroup | null> => {
    try {
      const response = await $fetch<ConsumerGroup>(apiUrl(`/api/v1/consumers/groups/${id}`), {
        method: 'PUT',
        body: data
      })
      return response
    } catch (err) {
      console.error('Failed to update consumer group:', err)
      throw err
    }
  }

  const deleteConsumerGroup = async (id: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/consumers/groups/${id}`), {
        method: 'DELETE'
      })
      return true
    } catch (err) {
      console.error('Failed to delete consumer group:', err)
      return false
    }
  }

  const getConsumerGroupsByEnvironment = async (environmentId: string): Promise<ConsumerGroup[]> => {
    try {
      const response = await $fetch<ConsumerGroup[]>(apiUrl(`/api/v1/environments/${environmentId}/consumers/groups`))
      return response
    } catch (err) {
      console.error('Failed to fetch consumer groups by environment:', err)
      return []
    }
  }

  const addConsumerToGroup = async (groupId: string, consumerId: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/consumers/groups/${groupId}/members`), {
        method: 'POST',
        body: { consumer_id: consumerId }
      })
      return true
    } catch (err) {
      console.error('Failed to add consumer to group:', err)
      throw err
    }
  }

  const removeConsumerFromGroup = async (groupId: string, consumerId: string): Promise<boolean> => {
    try {
      await $fetch(apiUrl(`/api/v1/consumers/groups/${groupId}/members/${consumerId}`), {
        method: 'DELETE'
      })
      return true
    } catch (err) {
      console.error('Failed to remove consumer from group:', err)
      throw err
    }
  }

  const checkConsumerInGroup = async (groupId: string, consumerId: string): Promise<boolean> => {
    try {
      const response = await $fetch<{ is_member: boolean }>(apiUrl(`/api/v1/consumers/groups/${groupId}/members/${consumerId}`))
      return response.is_member
    } catch (err) {
      console.error('Failed to check consumer in group:', err)
      return false
    }
  }

  return {
    consumerGroups: computed(() => consumerGroups.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchConsumerGroups,
    getConsumerGroup,
    createConsumerGroup,
    updateConsumerGroup,
    deleteConsumerGroup,
    getConsumerGroupsByEnvironment,
    addConsumerToGroup,
    removeConsumerFromGroup,
    checkConsumerInGroup
  }
} 