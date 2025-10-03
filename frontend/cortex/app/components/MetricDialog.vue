<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="flex items-center space-x-2">
          <Target class="h-5 w-5" />
          <span>{{ isEditing ? 'Edit Metric' : 'Create Metric' }}</span>
        </DialogTitle>
        <DialogDescription>
          {{ isEditing ? 'Edit your metric' : 'Create a new metric' }} {{ prefilledDataModelId ? 'for this model' : 'within one of your data models' }} using our intuitive schema builder.
        </DialogDescription>
      </DialogHeader>
      
      <Tabs v-model="activeTab" class="w-full">
        <TabsList class="grid w-full grid-cols-2">
          <TabsTrigger value="basic">Basic Information</TabsTrigger>
          <TabsTrigger value="schema">Schema Builder</TabsTrigger>
        </TabsList>

        <!-- Basic Information Tab -->
        <TabsContent value="basic" class="space-y-4 py-4">
          <!-- Data Model field - only show for create mode or when prefilled -->
          <div class="space-y-2" v-if="!isEditing && !prefilledDataModelId">
            <Label for="metric-model">Data Model *</Label>
            <Select v-model="form.data_model_id" :disabled="isLoading" @update:model-value="onDataModelChange">
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
          
          <!-- Data Model display - show for edit mode or when prefilled -->
          <div class="space-y-2" v-if="isEditing || prefilledDataModelId">
            <Label for="metric-model">Data Model</Label>
            <div class="flex items-center space-x-2">
              <Input
                :value="getDataModelName(form.data_model_id)"
                :disabled="true"
                class="bg-muted"
              />
              <Button variant="outline" size="sm" :disabled="true">
                <Database class="h-4 w-4" />
              </Button>
            </div>
            <p class="text-xs text-muted-foreground">
              Data model cannot be changed once a metric is created
            </p>
          </div>
          
          <div class="space-y-2">
            <Label for="metric-name">Name *</Label>
            <Input
              id="metric-name"
              v-model="form.name"
              placeholder="Enter metric name"
              :disabled="isLoading"
            />
          </div>
          
          <div class="space-y-2">
            <Label for="metric-alias">Alias</Label>
            <Input
              id="metric-alias"
              v-model="form.alias"
              placeholder="Auto-generated from name"
              :disabled="isLoading"
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
              :disabled="isLoading"
            />
          </div>
          
          <div class="space-y-2">
            <Label for="metric-description">Description</Label>
            <Textarea
              id="metric-description"
              v-model="form.description"
              placeholder="Describe your metric"
              rows="3"
              :disabled="isLoading"
            />
          </div>
          
          <div class="flex items-center space-x-2">
            <input
              id="metric-public"
              type="checkbox"
              v-model="form.public"
              :disabled="isLoading"
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
            v-model:selected-data-source-id="selectedDataSourceId"
            :table-schema="tableSchema"
          />
        </TabsContent>
      </Tabs>
    
    <DialogFooter>
      <Button
        variant="outline"
        @click="closeDialog"
        :disabled="isLoading"
      >
        Cancel
      </Button>
      <Button
        @click="handleSubmit"
        :disabled="!isFormValid || isLoading"
      >
        <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
        {{ isEditing ? 'Update Metric' : 'Create Metric' }}
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { toast } from 'vue-sonner'
import { useMetrics } from '~/composables/useMetrics'
import { useDataModels } from '~/composables/useDataModels'
import { useDataSources } from '~/composables/useDataSources'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Target, Loader2, Database } from 'lucide-vue-next'
import MetricSchemaBuilder from '~/components/metric-builder/MetricSchemaBuilder.vue'

interface Props {
  open: boolean
  isEditing?: boolean
  prefilledDataModelId?: string
  prefilledDataModelName?: string
  metricToEdit?: any // The metric data when editing
}

const props = withDefaults(defineProps<Props>(), {
  isEditing: false
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [metric: any]
  updated: [metric: any]
  close: []
}>()

const { createMetric, updateMetric, getMetric } = useMetrics()
const { models, fetchModels, getModel } = useDataModels()
const { getDataSourceSchema } = useDataSources()

const isLoading = ref(false)
const activeTab = ref('basic')
const schemaData = ref<{
  name?: string
  alias?: string
  title?: string
  description?: string
  table_name?: string
  query?: string
  data_source_id?: string
  limit?: number
  ordered?: boolean
  order?: any[]
  measures?: any[]
  dimensions?: any[]
  joins?: any[]
  aggregations?: any[]
  filters?: any[]
  parameters?: any
  tableSchema?: any
}>({})
const selectedDataSourceId = ref<string>('')
const tableSchema = ref<any>(null)

// Form state
const form = ref({
  data_model_id: props.prefilledDataModelId || '',
  name: '',
  alias: '',
  title: '',
  description: '',
  public: true
})

const { 
  generateAlias, 
  validateAlias, 
  getAliasError, 
  aliasManuallyEdited, 
  markAsManuallyEdited
} = useAliasGenerator()

// Form validation errors
const aliasError = ref('')

// Set up watchers for auto-generation and validation
watch(() => form.value.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    form.value.alias = generateAlias(newName)
  }
})

watch(() => form.value.alias, (newAlias) => {
  aliasError.value = getAliasError(newAlias)
})

// Track manual alias edits
const onAliasInput = () => {
  markAsManuallyEdited()
}

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
  schemaData.value = {
    ordered: true,
    order: []
  }
  tableSchema.value = null
  selectedDataSourceId.value = ''
}

const closeDialog = () => {
  emit('update:open', false)
  resetForm()
  emit('close')
}

const onDataModelChange = async (value: any) => {
  const modelId = value as string
  if (!modelId) return
  
  // Data models no longer have data source associations
  // Users will select data sources independently for each metric
  selectedDataSourceId.value = ''
  tableSchema.value = null
}

// Load schema for data source
const loadSchemaForDataSource = async (dataSourceId: string) => {
  try {
    console.log('Loading schema for data source:', dataSourceId)
    tableSchema.value = await getDataSourceSchema(dataSourceId)
    console.log('Schema loaded:', tableSchema.value)
  } catch (error) {
    console.error('Failed to load schema:', error)
    tableSchema.value = null
  }
}

// Load metric data for editing
const loadMetricData = async (metricId: string) => {
  try {
    isLoading.value = true
    const metric = await getMetric(metricId)
    if (metric) {
      // Populate form data
      form.value = {
        data_model_id: metric.data_model_id,
        name: metric.name,
        alias: metric.alias || '',
        title: metric.title || '',
        description: metric.description || '',
        public: metric.public
      }
      
      // Populate schema data
      schemaData.value = {
        name: metric.name,
        alias: metric.alias || '',
        title: metric.title || '',
        description: metric.description || '',
        table_name: metric.table_name,
        query: metric.query,
        data_source_id: metric.data_source_id,
        limit: metric.limit,
        ordered: metric.ordered,
        order: metric.order || [],
        measures: metric.measures || [],
        dimensions: metric.dimensions || [],
        joins: metric.joins || [],
        aggregations: metric.aggregations || [],
        filters: metric.filters || [],
        parameters: metric.parameters || {}
      }
      
      // Set data source and load schema if metric has one
      if (metric.data_source_id) {
        selectedDataSourceId.value = metric.data_source_id
        await loadSchemaForDataSource(metric.data_source_id)
      } else {
        selectedDataSourceId.value = ''
        tableSchema.value = null
      }
    }
  } catch (error) {
    console.error('Failed to load metric data:', error)
    toast.error('Failed to load metric data')
  } finally {
    isLoading.value = false
  }
}

// Helper function to get data model name
const getDataModelName = (modelId: string): string => {
  if (!modelId) return 'No model selected'
  const model = models.value?.find(m => m.id === modelId)
  return model?.name || 'Unknown model'
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    return
  }

  isLoading.value = true
  try {
    const metricData = {
      data_model_id: form.value.data_model_id,
      public: form.value.public,
      // Include all data from the schema builder (including basic fields)
      ...schemaData.value,
      // Override with form values for fields that are only in the form
      name: schemaData.value.name?.trim() || form.value.name.trim(),
      alias: schemaData.value.alias?.trim() || form.value.alias.trim() || undefined,
      title: schemaData.value.title?.trim() || form.value.title.trim() || undefined,
      description: schemaData.value.description?.trim() || form.value.description.trim() || undefined,
    }

    if (props.isEditing && props.metricToEdit?.id) {
      const updatedMetric = await updateMetric(props.metricToEdit.id, metricData)
      if (updatedMetric) {
        toast.success('Metric updated successfully')
        emit('updated', updatedMetric)
        closeDialog()
      }
    } else {
      const createdMetric = await createMetric(metricData)
      if (createdMetric) {
        toast.success('Metric created successfully')
        emit('created', createdMetric)
        closeDialog()
      }
    }
  } catch (error) {
    console.error('Failed to save metric:', error)
    toast.error(props.isEditing ? 'Failed to update metric' : 'Failed to create metric')
  } finally {
    isLoading.value = false
  }
}

// Watch for external open control and handle prefilled data model
watch(() => props.prefilledDataModelId, (newId) => {
  if (newId) {
    form.value.data_model_id = newId
  }
}, { immediate: true })

// Watch for schema data updates from MetricSchemaBuilder
watch(schemaData, (newSchemaData) => {
  if (newSchemaData.tableSchema) {
    console.log('Updating tableSchema from schemaData:', newSchemaData.tableSchema)
    tableSchema.value = newSchemaData.tableSchema
  }
}, { deep: true })

// Sync basic fields between form and schemaData
watch(() => form.value.name, (newName) => {
  if (schemaData.value.name !== newName) {
    schemaData.value.name = newName
  }
})

watch(() => form.value.alias, (newAlias) => {
  if (schemaData.value.alias !== newAlias) {
    schemaData.value.alias = newAlias
  }
})

watch(() => form.value.title, (newTitle) => {
  if (schemaData.value.title !== newTitle) {
    schemaData.value.title = newTitle
  }
})

watch(() => form.value.description, (newDescription) => {
  if (schemaData.value.description !== newDescription) {
    schemaData.value.description = newDescription
  }
})

// Sync back from schemaData to form
watch(() => schemaData.value.name, (newName) => {
  if (form.value.name !== newName) {
    form.value.name = newName || ''
  }
})

watch(() => schemaData.value.alias, (newAlias) => {
  if (form.value.alias !== newAlias) {
    form.value.alias = newAlias || ''
  }
})

watch(() => schemaData.value.title, (newTitle) => {
  if (form.value.title !== newTitle) {
    form.value.title = newTitle || ''
  }
})

watch(() => schemaData.value.description, (newDescription) => {
  if (form.value.description !== newDescription) {
    form.value.description = newDescription || ''
  }
})

// Load metric data when editing mode is enabled
watch(() => props.open, async (isOpen) => {
  if (isOpen && props.isEditing && props.metricToEdit?.id) {
    // For edit mode, load models first so we can display the data model name
    if (!models.value || models.value.length === 0) {
      await fetchModels()
    }
    await loadMetricData(props.metricToEdit.id)
  } else if (isOpen && !props.isEditing) {
    // For create mode, ensure models are loaded
    if (!models.value || models.value.length === 0) {
      await fetchModels()
    }
    
    // If we have a prefilled data model ID, load its schema
    if (props.prefilledDataModelId) {
      try {
        const model = await getModel(props.prefilledDataModelId)
        // Data models no longer have data source associations
        // Users will select data sources independently for each metric
        selectedDataSourceId.value = ''
        tableSchema.value = null
      } catch (error) {
        console.error('Failed to load prefilled model:', error)
      }
    }
  }
}, { immediate: true })
</script> 