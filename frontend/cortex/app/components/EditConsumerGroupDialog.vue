<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Edit class="h-4 w-4 mr-2" />
        Edit
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <Edit class="h-5 w-5" />
          <span>Edit Consumer Group</span>
        </DialogTitle>
        <DialogDescription>
          Update consumer group information and settings.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4 py-4">
        <div class="space-y-2">
          <Label for="edit-name">Name *</Label>
          <Input
            id="edit-name"
            v-model="form.name"
            placeholder="Enter group name"
            :disabled="isLoading"
            required
          />
        </div>
        
        <div class="space-y-2">
          <Label for="edit-alias">Alias</Label>
          <Input
            id="edit-alias"
            v-model="form.alias"
            placeholder="Enter group alias"
            :disabled="isLoading"
          />
        </div>
        
        <div class="space-y-2">
          <Label for="edit-description">Description</Label>
          <Textarea
            id="edit-description"
            v-model="form.description"
            placeholder="Enter group description"
            rows="3"
            :disabled="isLoading"
          />
        </div>
        
        <div class="space-y-2">
          <Label for="edit-properties">Properties (JSON)</Label>
          <Textarea
            id="edit-properties"
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
          @click="open = false"
          :disabled="isLoading"
        >
          Cancel
        </Button>
        <Button
          @click="handleSubmit"
          :disabled="!isFormValid || isLoading"
        >
          <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
          Update Group
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Edit, Loader2 } from 'lucide-vue-next'

interface Props {
  group: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  updated: [group: any]
}>()

const { updateConsumerGroup } = useConsumerGroups()

const open = ref(false)
const isLoading = ref(false)
const form = ref({
  name: '',
  alias: '',
  description: '',
  properties: ''
})

const isFormValid = computed(() => {
  return form.value.name.trim()
})

const resetForm = () => {
  form.value = {
    name: '',
    alias: '',
    description: '',
    properties: ''
  }
}

const loadGroupData = () => {
  if (props.group) {
    form.value = {
      name: props.group.name || '',
      alias: props.group.alias || '',
      description: props.group.description || '',
      properties: props.group.properties ? JSON.stringify(props.group.properties, null, 2) : ''
    }
  }
}

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
      name: form.value.name.trim(),
      alias: form.value.alias.trim() || undefined,
      description: form.value.description.trim() || undefined,
      properties
    }

    const updatedGroup = await updateConsumerGroup(props.group.id, groupData)
    
    if (updatedGroup) {
      toast.success('Consumer group updated successfully')
      emit('updated', updatedGroup)
      open.value = false
    }
  } catch (error) {
    console.error('Failed to update consumer group:', error)
    toast.error('Failed to update consumer group')
  } finally {
    isLoading.value = false
  }
}

// Load group data when dialog opens
watch(() => open.value, (isOpen) => {
  if (isOpen) {
    loadGroupData()
  }
})
</script> 