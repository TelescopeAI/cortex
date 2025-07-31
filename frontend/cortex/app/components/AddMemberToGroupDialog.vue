<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <UserPlus class="h-5 w-5" />
          <span>Add Member to Group</span>
        </DialogTitle>
        <DialogDescription>
          Add a consumer as a member to this group.
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-4 py-4">
        <!-- Consumer Selection -->
        <div class="space-y-2">
          <Label for="consumer">Consumer *</Label>
          <Select v-model="selectedConsumerId" :disabled="isLoading">
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
      </div>

      <DialogFooter>
        <Button variant="outline" @click="$emit('update:open', false)" :disabled="isLoading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isFormValid || isLoading">
          <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
          Add Member
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useConsumers } from '~/composables/useConsumers'
import { useConsumerGroups } from '~/composables/useConsumerGroups'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { UserPlus, Loader2 } from 'lucide-vue-next'

interface Props {
  open: boolean
  groupId: string
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { consumers, fetchConsumers } = useConsumers()
const { addConsumerToGroup } = useConsumerGroups()

const isLoading = ref(false)
const selectedConsumerId = ref<string>('')
const consumerSearchQuery = ref('')

const isFormValid = computed(() => {
  return selectedConsumerId.value
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

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  isLoading.value = true
  
  try {
    await addConsumerToGroup(props.groupId, selectedConsumerId.value)
    
    emit('added')
    emit('update:open', false)
    resetForm()
  } catch (error) {
    console.error('Failed to add member to group:', error)
    throw error
  } finally {
    isLoading.value = false
  }
}

const resetForm = () => {
  selectedConsumerId.value = ''
  consumerSearchQuery.value = ''
}

// Load data when dialog opens
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    fetchConsumers()
  }
})
</script> 