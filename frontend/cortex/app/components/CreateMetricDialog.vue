<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child v-if="!hideInitialTrigger">
      <Button size="sm">
        <Plus class="h-4 w-4 mr-2" />
        Add Metric
      </Button>
    </DialogTrigger>
          <DialogContent class="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle class="flex items-center space-x-2">
            <Target class="h-5 w-5" />
            <span>Create Metric</span>
          </DialogTitle>
          <DialogDescription>
            Create a new metric {{ prefilledDataModelId ? 'for this model' : 'within one of your data models' }} using our intuitive schema builder.
          </DialogDescription>
        </DialogHeader>
        
        <Tabs v-model="activeTab" class="w-full">
          <TabsList class="grid w-full grid-cols-2">
            <TabsTrigger value="basic">Basic Information</TabsTrigger>
            <TabsTrigger value="schema">Schema Builder</TabsTrigger>
          </TabsList>

          <!-- Basic Information Tab -->
          <TabsContent value="basic" class="space-y-4 py-4">
            <div class="space-y-2" v-if="!prefilledDataModelId">
              <Label for="metric-model">Data Model *</Label>
              <Select v-model="form.data_model_id" :disabled="isCreating" @update:model-value="onDataModelChange">
                <SelectTrigger>
                  <SelectValue placeholder="Select a data model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="model in models || []" :key="model.id" :value="model.id">
                    {{ model.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div class="space-y-2">
              <Label for="metric-name">Name *</Label>
              <Input
                id="metric-name"
                v-model="form.name"
                placeholder="Enter metric name"
                :disabled="isCreating"
              />
            </div>
            
            <div class="space-y-2">
              <Label for="metric-alias">Alias</Label>
              <Input
                id="metric-alias"
                v-model="form.alias"
                placeholder="Auto-generated from name"
                :disabled="isCreating"
                @input="onAliasInput"
              />
              <p v-if="aliasError" class="text-sm text-red-500">{{ aliasError }}</p>
              <p v-else class="text-xs text-muted-foreground">Only lowercase letters, numbers, and underscores allowed</p>
            </div>
            
            <div class="space-y-2">
              <Label for="metric-title">Title</Label>
              <Input
                id="metric-title"
                v-model="form.title"
                placeholder="Enter display title (optional)"
                :disabled="isCreating"
              />
            </div>
            
            <div class="space-y-2">
              <Label for="metric-description">Description</Label>
              <Textarea
                id="metric-description"
                v-model="form.description"
                placeholder="Describe your metric"
                rows="3"
                :disabled="isCreating"
              />
            </div>
            
            <div class="flex items-center space-x-2">
              <input
                id="metric-public"
                type="checkbox"
                v-model="form.public"
                :disabled="isCreating"
                class="h-4 w-4 rounded border-gray-300"
              />
              <Label for="metric-public" class="text-sm font-normal">
                Make this metric public
              </Label>
            </div>
          </TabsContent>

          <!-- Schema Builder Tab -->
          <TabsContent value="schema" class="space-y-4 py-4">
            <MetricSchemaBuilder
              v-model="schemaData"
              :selected-data-source-id="selectedDataSourceId"
            />
          </TabsContent>
        </Tabs>
      
      <DialogFooter>
        <Button
          variant="outline"
          @click="closeDialog"
          :disabled="isCreating"
        >
          Cancel
        </Button>
        <Button
          @click="handleCreate"
          :disabled="!isFormValid || isCreating"
        >
          <Loader2 v-if="isCreating" class="h-4 w-4 mr-2 animate-spin" />
          Create Metric
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { useMetrics } from '~/composables/useMetrics'
import { useDataModels } from '~/composables/useDataModels'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Plus, Target, Loader2 } from 'lucide-vue-next'
import MetricSchemaBuilder from '~/components/metric-builder/MetricSchemaBuilder.vue'

interface Props {
  prefilledDataModelId?: string
  prefilledDataModelName?: string
  hideInitialTrigger?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  created: [metric: any]
  close: []
}>()

const { createMetric } = useMetrics()
const { models } = useDataModels()

const open = ref(false)
const isCreating = ref(false)
const activeTab = ref('basic')
const schemaData = ref({})
const selectedDataSourceId = ref<string>('')

// Form state
const form = ref({
  data_model_id: props.prefilledDataModelId || '',
  name: '',
  alias: '',
  title: '',
  description: '',
  public: true
})

// Track if alias was manually edited
const aliasManuallyEdited = ref(false)

// Auto-generate alias from name
const generateAlias = (name: string): string => {
  return name
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_{2,}/g, '_')
    .replace(/^_+|_+$/g, '')
}

// Validate alias format
const validateAlias = (alias: string): boolean => {
  // Allow only lowercase letters, numbers, and underscores
  // No spaces, no special characters except underscore
  const aliasRegex = /^[a-z0-9_]+$/
  return aliasRegex.test(alias) && alias.length > 0
}

// Form validation errors
const aliasError = ref('')

// Watch for name changes to auto-generate alias
watch(() => form.value.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    form.value.alias = generateAlias(newName)
  }
})

// Track manual alias edits
const onAliasInput = () => {
  aliasManuallyEdited.value = true
}

// Watch for alias changes to validate
watch(() => form.value.alias, (newAlias) => {
  if (newAlias && !validateAlias(newAlias)) {
    aliasError.value = 'Alias can only contain lowercase letters, numbers, and underscores'
  } else {
    aliasError.value = ''
  }
})

// Computed
const isFormValid = computed(() => {
  return form.value.name.trim() && form.value.data_model_id && !aliasError.value
})

// Methods
const resetForm = () => {
  form.value = {
    data_model_id: props.prefilledDataModelId || '',
    name: '',
    alias: '',
    title: '',
    description: '',
    public: true
  }
  aliasManuallyEdited.value = false
  aliasError.value = ''
}

const closeDialog = () => {
  open.value = false
  resetForm()
  emit('close')
}

const onDataModelChange = async (value: any) => {
  const modelId = value as string
  if (!modelId) return
  
  // Find the selected model and get its data source
  const selectedModel = models.value?.find(m => m.id === modelId)
  if (selectedModel?.data_source_id) {
    selectedDataSourceId.value = selectedModel.data_source_id
    // Trigger schema loading by setting tableSchema to null
    // This will cause the watcher in MetricSchemaBuilder to reload
    if (schemaData.value) {
      schemaData.value = {}
    }
  }
}

// Watch for external open control and handle prefilled data model
watch(() => props.prefilledDataModelId, (newId) => {
  if (newId) {
    form.value.data_model_id = newId
    // Also trigger data source loading for prefilled models
    onDataModelChange(newId)
  }
}, { immediate: true })

const handleCreate = async () => {
  if (!isFormValid.value) {
    return
  }

  isCreating.value = true
  try {
    const metricData = {
      data_model_id: form.value.data_model_id,
      name: form.value.name.trim(),
      alias: form.value.alias.trim() || undefined,
      title: form.value.title.trim() || undefined,
      description: form.value.description.trim() || undefined,
      public: form.value.public,
      // Include schema data from the builder
      ...schemaData.value
    }

    const createdMetric = await createMetric(metricData)
    if (createdMetric) {
      toast.success('Metric created successfully')
      emit('created', createdMetric)
      closeDialog()
    }
  } catch (error) {
    console.error('Failed to create metric:', error)
    toast.error('Failed to create metric')
  } finally {
    isCreating.value = false
  }
}

// Expose methods for external control
defineExpose({
  openDialog: () => {
    open.value = true
  },
  closeDialog
})
</script> 