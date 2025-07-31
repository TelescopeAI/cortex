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
          <span>Edit Consumer</span>
        </DialogTitle>
        <DialogDescription>
          Update consumer information and settings.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4 py-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="edit-first-name">First Name *</Label>
            <Input
              id="edit-first-name"
              v-model="form.first_name"
              placeholder="Enter first name"
              :disabled="isLoading"
              required
            />
          </div>
          
          <div class="space-y-2">
            <Label for="edit-last-name">Last Name *</Label>
            <Input
              id="edit-last-name"
              v-model="form.last_name"
              placeholder="Enter last name"
              :disabled="isLoading"
              required
            />
          </div>
        </div>
        
        <div class="space-y-2">
          <Label for="edit-email">Email *</Label>
          <Input
            id="edit-email"
            v-model="form.email"
            type="email"
            placeholder="Enter email address"
            :disabled="isLoading"
            required
          />
        </div>
        
        <div class="space-y-2">
          <Label for="edit-organization">Organization</Label>
          <Input
            id="edit-organization"
            v-model="form.organization"
            placeholder="Enter organization"
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
          Update Consumer
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
  consumer: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  updated: [consumer: any]
}>()

const { updateConsumer } = useConsumers()

const open = ref(false)
const isLoading = ref(false)
const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  organization: '',
  properties: ''
})

const isFormValid = computed(() => {
  return form.value.first_name.trim() && 
         form.value.last_name.trim() && 
         form.value.email.trim()
})

const resetForm = () => {
  form.value = {
    first_name: '',
    last_name: '',
    email: '',
    organization: '',
    properties: ''
  }
}

const loadConsumerData = () => {
  if (props.consumer) {
    form.value = {
      first_name: props.consumer.first_name || '',
      last_name: props.consumer.last_name || '',
      email: props.consumer.email || '',
      organization: props.consumer.organization || '',
      properties: props.consumer.properties ? JSON.stringify(props.consumer.properties, null, 2) : ''
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

    const consumerData = {
      first_name: form.value.first_name.trim(),
      last_name: form.value.last_name.trim(),
      email: form.value.email.trim(),
      organization: form.value.organization.trim() || undefined,
      properties
    }

    const updatedConsumer = await updateConsumer(props.consumer.id, consumerData)
    
    if (updatedConsumer) {
      toast.success('Consumer updated successfully')
      emit('updated', updatedConsumer)
      open.value = false
    }
  } catch (error) {
    console.error('Failed to update consumer:', error)
    toast.error('Failed to update consumer')
  } finally {
    isLoading.value = false
  }
}

// Load consumer data when dialog opens
watch(() => open.value, (isOpen) => {
  if (isOpen) {
    loadConsumerData()
  }
})
</script> 