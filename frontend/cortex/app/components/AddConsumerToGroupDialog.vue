<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <UserPlus class="h-5 w-5" />
          <span>{{ props.consumer ? 'Add to Group' : 'Add Consumer to Group' }}</span>
        </DialogTitle>
        <DialogDescription>
          {{ props.consumer ? `Add ${props.consumer.first_name} ${props.consumer.last_name} to an existing consumer group.` : 'Add a consumer to an existing consumer group.' }}
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-4 py-4">
        <!-- Consumer Selection -->
        <div class="space-y-2">
          <Label for="consumer">Consumer *</Label>
          <div v-if="props.consumer" class="text-sm bg-muted p-3 rounded-md">
            <div class="font-medium">{{ props.consumer.first_name }} {{ props.consumer.last_name }}</div>
            <div class="text-muted-foreground">{{ props.consumer.email }}</div>
          </div>
          <Select v-else v-model="selectedConsumerId" :disabled="isLoading">
            <SelectTrigger>
              <SelectValue placeholder="Select a consumer" />
            </SelectTrigger>
            <SelectContent>
              <div class="p-2">
                <Input
                  v-model="consumerSearchQuery"
                  placeholder="Search consumers..."
                  class="mb-2"
                />
              </div>
              <SelectItem 
                v-for="consumer in filteredConsumers" 
                :key="consumer.id" 
                :value="consumer.id"
              >
                <div class="flex flex-col">
                  <span class="font-medium">{{ consumer.first_name }} {{ consumer.last_name }} ({{ consumer.email }})</span>
                </div>
              </SelectItem>
              <div v-if="filteredConsumers.length === 0" class="p-2 text-sm text-muted-foreground">
                No consumers found
              </div>
            </SelectContent>
          </Select>
        </div>

        <!-- Group Selection -->
        <div class="space-y-2">
          <Label for="group">Group *</Label>
          <Select v-model="selectedGroupId" :disabled="isLoading">
            <SelectTrigger>
              <SelectValue placeholder="Select a group" />
            </SelectTrigger>
            <SelectContent>
              <div class="p-2">
                <Input
                  v-model="groupSearchQuery"
                  placeholder="Search groups..."
                  class="mb-2"
                />
              </div>
              <SelectItem 
                v-for="group in filteredGroups" 
                :key="group.id" 
                :value="group.id"
              >
                <div class="flex flex-col">
                  <span class="font-medium">{{ group.name }} ({{ group.description || 'No description' }})</span>
                </div>
              </SelectItem>
              <div v-if="filteredGroups.length === 0" class="p-2 text-sm text-muted-foreground">
                {{ props.consumer && props.consumer.groups && props.consumer.groups.length > 0 
                   ? 'No available groups (consumer is already a member of all groups)' 
                   : 'No groups found' }}
              </div>
            </SelectContent>
          </Select>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)" :disabled="isLoading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isFormValid || isLoading">
          <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
          Add to Group
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useConsumers } from '~/composables/useConsumers'
import { useConsumerGroups } from '~/composables/useConsumerGroups'
import { toast } from 'vue-sonner'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { UserPlus, Loader2 } from 'lucide-vue-next'

interface Props {
  open: boolean
  consumer?: any // Optional consumer to pre-fill
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { consumers, fetchConsumers } = useConsumers()
const { consumerGroups, fetchConsumerGroups, addConsumerToGroup } = useConsumerGroups()

const isLoading = ref(false)
const selectedConsumerId = ref<string>('')
const selectedGroupId = ref<string>('')
const consumerSearchQuery = ref('')
const groupSearchQuery = ref('')

const isFormValid = computed(() => {
  const hasConsumer = props.consumer || selectedConsumerId.value
  return hasConsumer && selectedGroupId.value
})

const filteredConsumers = computed(() => {
  if (!consumers.value) return []
  
  return consumers.value.filter(consumer => {
    const searchTerm = consumerSearchQuery.value.toLowerCase()
    return consumer.first_name.toLowerCase().includes(searchTerm) ||
           consumer.last_name.toLowerCase().includes(searchTerm) ||
           consumer.email.toLowerCase().includes(searchTerm)
  })
})

const filteredGroups = computed(() => {
  if (!consumerGroups.value) return []
  
  return consumerGroups.value.filter(group => {
    const searchTerm = groupSearchQuery.value.toLowerCase()
    const matchesSearch = group.name.toLowerCase().includes(searchTerm) ||
           (group.description && group.description.toLowerCase().includes(searchTerm))
    
    // If we have a pre-filled consumer, filter out groups they're already part of
    if (props.consumer && props.consumer.groups) {
      const isAlreadyMember = props.consumer.groups.some((consumerGroup: any) => consumerGroup.id === group.id)
      return matchesSearch && !isAlreadyMember
    }
    
    return matchesSearch
  })
})

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  
  try {
    const consumerId = props.consumer ? props.consumer.id : selectedConsumerId.value
    await addConsumerToGroup(selectedGroupId.value, consumerId)
    
    toast.success('Consumer added to group successfully')
    emit('added')
    emit('update:open', false)
    resetForm()
  } catch (error) {
    console.error('Failed to add consumer to group:', error)
    toast.error('Failed to add consumer to group')
  } finally {
    isLoading.value = false
  }
}

const resetForm = () => {
  selectedConsumerId.value = ''
  selectedGroupId.value = ''
  consumerSearchQuery.value = ''
  groupSearchQuery.value = ''
}

// Load data when dialog opens
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    fetchConsumers()
    fetchConsumerGroups()
  }
})
</script> 