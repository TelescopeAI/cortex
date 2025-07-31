<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <Users class="h-5 w-5" />
          <span>Create Consumer Group</span>
        </DialogTitle>
        <DialogDescription>
          Add a new consumer group to your environment.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4 py-4">
        <div class="space-y-2">
          <Label for="name">Name *</Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="Enter group name"
            :disabled="isLoading"
            required
          />
        </div>
        
                  <div class="space-y-2">
            <Label for="alias">Alias</Label>
            <Input
              id="alias"
              v-model="form.alias"
              placeholder="Auto-generated from name"
              :disabled="isLoading"
              @input="markAsManuallyEdited"
            />
            <p v-if="aliasError" class="text-sm text-red-500">{{ aliasError }}</p>
            <p class="text-xs text-muted-foreground">Only lowercase letters, numbers, and underscores allowed</p>
          </div>
        
        <div class="space-y-2">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="form.description"
            placeholder="Enter group description"
            rows="3"
            :disabled="isLoading"
          />
        </div>
        

        
        <div class="space-y-2">
          <Label for="properties">Properties (JSON)</Label>
          <Textarea
            id="properties"
            v-model="form.properties"
            placeholder='{"key": "value"}'
            rows="4"
            class="font-mono text-sm"
            :disabled="isLoading"
          />
          <p class="text-xs text-muted-foreground">Optional key-value pairs in JSON format</p>
        </div>
      </form>
      
      <DialogFooter>
        <Button
          variant="outline"
          @click="$emit('update:open', false)"
          :disabled="isLoading"
        >
          Cancel
        </Button>
        <Button
          @click="handleSubmit"
          :disabled="!isFormValid || isLoading"
        >
          <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
          Create Group
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Users, Loader2 } from 'lucide-vue-next'

interface Props {
  open: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [group: any]
}>()

const { createConsumerGroup } = useConsumerGroups()
const { selectedEnvironmentId } = useEnvironments()
const { 
  generateAlias, 
  validateAlias, 
  getAliasError, 
  aliasManuallyEdited, 
  markAsManuallyEdited
} = useAliasGenerator()

const isLoading = ref(false)
const form = ref({
  name: '',
  alias: '',
  description: '',
  properties: ''
})

const aliasError = ref('')

const isFormValid = computed(() => {
  return form.value.name.trim() && 
         selectedEnvironmentId.value && 
         validateAlias(form.value.alias) &&
         !aliasError.value
})

const resetForm = () => {
  form.value = {
    name: '',
    alias: '',
    description: '',
    properties: ''
  }
  aliasError.value = ''
  aliasManuallyEdited.value = false
}

// Set up watchers for auto-generation and validation
watch(() => form.value.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    form.value.alias = generateAlias(newName)
  }
})

watch(() => form.value.alias, (newAlias) => {
  aliasError.value = getAliasError(newAlias)
})

const handleSubmit = async () => {
  if (!isFormValid.value) return

  isLoading.value = true
  try {
    // Parse properties if provided
    let properties = null
    if (form.value.properties.trim()) {
      try {
        properties = JSON.parse(form.value.properties)
      } catch (error) {
        toast.error('Invalid JSON format for properties')
        return
      }
    }

    const groupData = {
      environment_id: selectedEnvironmentId.value!,
      name: form.value.name.trim(),
      alias: form.value.alias.trim() || undefined,
      description: form.value.description.trim() || undefined,
      properties
    }

    const createdGroup = await createConsumerGroup(groupData)
    
    if (createdGroup) {
      toast.success('Consumer group created successfully')
      emit('created', createdGroup)
      emit('update:open', false)
      resetForm()
    }
  } catch (error) {
    console.error('Failed to create consumer group:', error)
    toast.error('Failed to create consumer group')
  } finally {
    isLoading.value = false
  }
}


</script> 