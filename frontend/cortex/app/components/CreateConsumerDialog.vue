<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <UserPlus class="h-5 w-5" />
          <span>Create Consumer</span>
        </DialogTitle>
        <DialogDescription>
          Add a new consumer to your environment.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4 py-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="first-name">First Name *</Label>
            <Input
              id="first-name"
              v-model="form.first_name"
              placeholder="Enter first name"
              :disabled="isLoading"
              required
            />
          </div>
          
          <div class="space-y-2">
            <Label for="last-name">Last Name *</Label>
            <Input
              id="last-name"
              v-model="form.last_name"
              placeholder="Enter last name"
              :disabled="isLoading"
              required
            />
          </div>
        </div>
        
        <div class="space-y-2">
          <Label for="email">Email *</Label>
          <Input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="Enter email address"
            :disabled="isLoading"
            required
          />
        </div>
        
        <div class="space-y-2">
          <Label for="organization">Organization</Label>
          <Input
            id="organization"
            v-model="form.organization"
            placeholder="Enter organization"
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
          Create Consumer
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
import { UserPlus, Loader2 } from 'lucide-vue-next'

interface Props {
  open: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [consumer: any]
}>()

const { createConsumer } = useConsumers()
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
  first_name: '',
  last_name: '',
  email: '',
  organization: '',
  properties: ''
})

const aliasError = ref('')

const isFormValid = computed(() => {
  return form.value.first_name.trim() && 
         form.value.last_name.trim() && 
         form.value.email.trim() && 
         selectedEnvironmentId.value
})

const resetForm = () => {
  form.value = {
    first_name: '',
    last_name: '',
    email: '',
    organization: '',
    properties: ''
  }
  aliasError.value = ''
  aliasManuallyEdited.value = false
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
      environment_id: selectedEnvironmentId.value!,
      first_name: form.value.first_name.trim(),
      last_name: form.value.last_name.trim(),
      email: form.value.email.trim(),
      organization: form.value.organization.trim() || undefined,
      properties
    }

    const createdConsumer = await createConsumer(consumerData)
    
    if (createdConsumer) {
      toast.success('Consumer created successfully')
      emit('created', createdConsumer)
      emit('update:open', false)
      resetForm()
    }
  } catch (error) {
    console.error('Failed to create consumer:', error)
    toast.error('Failed to create consumer')
  } finally {
    isLoading.value = false
  }
}


</script> 