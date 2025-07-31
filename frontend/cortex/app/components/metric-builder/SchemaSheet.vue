<template>
  <Sheet :open="open" @update:open="$emit('update:open', $event)">
    <SheetContent 
      :side="isSmallScreen ? 'bottom' : 'right'" 
      :class="[
        'flex flex-col',
        'p-4',
        isSmallScreen 
          ? '!w-full !h-[90vh]' 
          :'!w-[95vw] sm:!w-[85vw] md:!w-[75vw] lg:!w-[65vw] xl:!w-[50vw] !max-w-[50vw] sm:!max-w-none'
      ]"
    >
      <SheetHeader>
        <SheetTitle class="flex items-center space-x-2">
          <Code class="h-5 w-5" />
          <span>Metric Schema</span>
        </SheetTitle>
        <SheetDescription>
          View and edit the metric schema configuration
        </SheetDescription>
      </SheetHeader>

      <div class="flex items-center justify-between mb-4 px-4">
        <div class="flex items-center space-x-2">
          <Button
            :variant="isEditing ? 'default' : 'outline'"
            size="sm"
            @click="handleEditToggle(!isEditing)"
            class="flex items-center"
          >
            <Edit class="h-4 w-4 mr-2" />
            {{ isEditing ? 'Editing' : 'Edit' }}
          </Button>
          <span class="text-sm text-muted-foreground">
            {{ isEditing ? 'Editing mode' : 'View mode' }}
          </span>
        </div>
        
        <div v-if="isEditing" class="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            @click="loadSchemaFromDataSource"
            :disabled="!selectedDataSourceId || schemaLoading"
          >
            <Database class="h-4 w-4 mr-2" />
            {{ schemaLoading ? 'Loading...' : 'Load Schema' }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="showJsonPreview = !showJsonPreview"
          >
            <Code class="h-4 w-4 mr-2" />
            {{ showJsonPreview ? 'Hide' : 'Show' }} JSON
          </Button>
        </div>
      </div>

      <!-- JSON Preview (only in edit mode) -->
      <Card v-if="showJsonPreview && isEditing" class="mb-4">
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <Code class="h-5 w-5" />
            <span>Generated Schema JSON</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            :model-value="generatedJson"
            readonly
            rows="15"
            class="font-mono text-sm"
            placeholder="Schema JSON will appear here as you build..."
          />
        </CardContent>
      </Card>

      <!-- Schema Content -->
      <div class="flex-1 overflow-y-auto min-h-0">
        <!-- Edit Mode -->
        <div v-if="isEditing">
          <MetricSchemaBuilder
            :selected-data-source-id="selectedDataSourceId"
            :model-value="schema"
            :table-schema="tableSchema"
            @update:model-value="handleSchemaUpdate"
            @update:selected-data-source-id="handleDataSourceUpdate"
          />
        </div>

        <!-- View Mode -->
        <div v-else>
          <SchemaViewer :metric="metric" />
        </div>
      </div>

      <SheetFooter v-if="isEditing" class="mt-6">
        <Button variant="outline" @click="$emit('update:open', false)">
          Cancel
        </Button>
        <Button @click="handleSave">
          Save Changes
        </Button>
      </SheetFooter>
    </SheetContent>
  </Sheet>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from '~/components/ui/sheet'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Textarea } from '~/components/ui/textarea'

import { Code, Database, Edit } from 'lucide-vue-next'
import { useDataSources } from '~/composables/useDataSources'
import { toast } from 'vue-sonner'

// Import builder components
import MetricSchemaBuilder from './MetricSchemaBuilder.vue'
import SchemaViewer from '~/components/metric-builder/SchemaViewer.vue'

interface Props {
  open: boolean
  metric: any
  selectedDataSourceId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  'save': [value: any]
}>()

const { getDataSourceSchema } = useDataSources()

// Component state
const isEditing = ref(false)
const showJsonPreview = ref(false)
const schemaLoading = ref(false)
const tableSchema = ref<any>(null)

// Screen size detection
const windowWidth = ref(0)
const isSmallScreen = computed(() => windowWidth.value < 768)

// Update window width on mount and resize
onMounted(() => {
  if (process.client) {
    windowWidth.value = window.innerWidth
    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })
  }
})



// Schema data structure
const schema = ref({
  table_name: '',
  query: '',
  data_source_id: undefined as string | undefined,
  limit: undefined as number | undefined,
  measures: [],
  dimensions: [],
  joins: [],
  aggregations: [],
  filters: [],
  parameters: {}
})

// Initialize schema from metric
watch(() => props.metric, (newMetric) => {
  if (newMetric) {
    schema.value = {
      table_name: newMetric.table_name || '',
      query: newMetric.query || '',
      data_source_id: newMetric.data_source_id || undefined,
      limit: newMetric.limit || undefined,
      measures: newMetric.measures || [],
      dimensions: newMetric.dimensions || [],
      joins: newMetric.joins || [],
      aggregations: newMetric.aggregations || [],
      filters: newMetric.filters || [],
      parameters: newMetric.parameters || {}
    }
    
    // Auto-load schema if we have a data source ID and no schema loaded yet
    if (newMetric.data_source_id && !tableSchema.value) {
      loadSchemaFromDataSource(newMetric.data_source_id)
    }
  }
}, { immediate: true })

// Auto-load schema when selectedDataSourceId changes
watch(() => props.selectedDataSourceId, (newDataSourceId) => {
  if (newDataSourceId && !tableSchema.value) {
    loadSchemaFromDataSource(newDataSourceId)
  }
}, { immediate: true })

// Generated JSON
const generatedJson = computed(() => {
  const cleanSchema = JSON.parse(JSON.stringify(schema.value))
  
  // Remove empty arrays and null values, but preserve data_source_id
  Object.keys(cleanSchema).forEach(key => {
    if (Array.isArray(cleanSchema[key]) && cleanSchema[key].length === 0) {
      delete cleanSchema[key]
    } else if ((cleanSchema[key] === null || cleanSchema[key] === undefined || cleanSchema[key] === '') && key !== 'data_source_id') {
      delete cleanSchema[key]
    }
  })
  
  return JSON.stringify(cleanSchema, null, 2)
})

// Load schema from data source
const loadSchemaFromDataSource = async (dataSourceId?: string) => {
  const sourceId = dataSourceId || props.selectedDataSourceId
  if (!sourceId) {
    toast.error('Please select a data source first')
    return
  }

  schemaLoading.value = true
  try {
    tableSchema.value = await getDataSourceSchema(sourceId)
    toast.success('Schema loaded successfully')
  } catch (error) {
    console.error('Failed to load schema:', error)
    toast.error('Failed to load schema from data source')
  } finally {
    schemaLoading.value = false
  }
}

// Handle edit toggle
const handleEditToggle = (pressed: boolean) => {
  isEditing.value = pressed
  if (!pressed) {
    showJsonPreview.value = false
  }
}

// Handle schema updates
const handleSchemaUpdate = (newSchema: any) => {
  schema.value = { ...schema.value, ...newSchema }
}

// Handle data source updates
const handleDataSourceUpdate = (newDataSourceId: string | undefined) => {
  emit('save', { ...schema.value, data_source_id: newDataSourceId })
}

// Handle save
const handleSave = () => {
  emit('save', schema.value)
  emit('update:open', false)
  isEditing.value = false
}
</script> 