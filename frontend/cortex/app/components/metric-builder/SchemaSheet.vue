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
            @click="() => loadSchemaFromDataSource()"
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
            :selected-data-source-id="selectedDataSourceIdLocal"
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
import { ref, computed, watch, onMounted } from 'vue'
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

const { getDataSourceSchema, getDataSource } = useDataSources()

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



// Local reactive copy of selected data source id (do not mutate prop directly)
const selectedDataSourceIdLocal = ref<string | undefined>(undefined)

// Schema data structure
const schema = ref({
  name: '',
  alias: '',
  title: '',
  description: '',
  table_name: '',
  query: '',
  data_source_id: undefined as string | undefined,
  limit: undefined as number | undefined,
  grouped: true,
  ordered: true,
  order: [],
  measures: [],
  dimensions: [],
  joins: [],
  aggregations: [],
  filters: [],
  parameters: {},
  refresh: undefined as any,
  cache: undefined as any
})

// Initialize schema from metric
watch(() => props.metric, async (newMetric) => {
  if (newMetric) {
    schema.value = {
      name: newMetric.name || '',
      alias: newMetric.alias || '',
      title: newMetric.title || '',
      description: newMetric.description || '',
      table_name: newMetric.table_name || '',
      query: newMetric.query || '',
      data_source_id: newMetric.data_source_id || undefined,
      limit: newMetric.limit || undefined,
      grouped: newMetric.grouped !== undefined ? newMetric.grouped : true,
      ordered: newMetric.ordered !== undefined ? newMetric.ordered : true,
      order: newMetric.order || [],
      measures: newMetric.measures || [],
      dimensions: newMetric.dimensions || [],
      joins: newMetric.joins || [],
      aggregations: newMetric.aggregations || [],
      filters: newMetric.filters || [],
      parameters: newMetric.parameters || {},
      refresh: newMetric.refresh || undefined,
      cache: newMetric.cache || undefined
    }
    
    // Initialize local data source id from metric
    selectedDataSourceIdLocal.value = newMetric.data_source_id || props.selectedDataSourceId
    
    // Load data source schema if we have a data source ID
    if (selectedDataSourceIdLocal.value) {
      try {
        // Verify the data source exists and load its schema
        const dataSource = await getDataSource(selectedDataSourceIdLocal.value)
        if (dataSource) {
          await loadSchemaFromDataSource(selectedDataSourceIdLocal.value)
        } else {
          console.warn(`Data source with ID ${selectedDataSourceIdLocal.value} not found`)
          selectedDataSourceIdLocal.value = undefined
        }
      } catch (error) {
        console.error('Failed to load data source:', error)
        selectedDataSourceIdLocal.value = undefined
      }
    }
  }
}, { immediate: true })

// Sync prop -> local for initial mount
watch(() => props.selectedDataSourceId, (newId) => {
  if (newId) {
    selectedDataSourceIdLocal.value = newId
  }
}, { immediate: true })

// Generated JSON
const generatedJson = computed(() => {
  const cleanSchema = JSON.parse(JSON.stringify(schema.value))
  
  // Remove empty arrays and null values, but preserve data_source_id and refresh
  Object.keys(cleanSchema).forEach(key => {
    if (Array.isArray(cleanSchema[key]) && cleanSchema[key].length === 0) {
      delete cleanSchema[key]
    } else if ((cleanSchema[key] === null || cleanSchema[key] === undefined || cleanSchema[key] === '') && !['data_source_id', 'refresh'].includes(key)) {
      delete cleanSchema[key]
    }
  })
  
  return JSON.stringify(cleanSchema, null, 2)
})

// Load schema from data source (use function declaration for hoisting)
async function loadSchemaFromDataSource(dataSourceId?: string) {
  const src = dataSourceId || selectedDataSourceIdLocal.value || props.selectedDataSourceId
  if (!src) {
    toast.error('Please select a data source first')
    return
  }

  schemaLoading.value = true
  try {
    const schemaData = await getDataSourceSchema(src)
    tableSchema.value = schemaData
    
    // Update the schema with the loaded table schema
    if (schemaData?.tables && schemaData.tables.length > 0) {
      const firstTable = schemaData.tables[0]?.name
      const currentTable = schema.value.table_name
      const tableExists = schemaData.tables.some((t: any) => t.name === currentTable)
      
      console.log('Schema loaded:', {
        tables: schemaData.tables.map((t: any) => t.name),
        currentTable,
        firstTable,
        tableExists,
        originalMetricTable: props.metric?.table_name
      })
      
      // Only override if no table is currently selected OR current table doesn't exist in new schema
      // Also check if we have an original table name from the metric that exists in the new schema
      const originalTable = props.metric?.table_name
      if (originalTable && schemaData.tables.some((t: any) => t.name === originalTable)) {
        // Use the original table name from the metric if it exists in the new schema
        schema.value.table_name = originalTable
        console.log('Using original table_name from metric:', originalTable)
      } else if (!currentTable || currentTable === '' || !tableExists) {
        schema.value.table_name = firstTable || ''
        console.log('Updated table_name to:', firstTable)
      } else {
        console.log('Keeping existing table_name:', currentTable)
      }
    } else {
      schema.value.table_name = ''
    }
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
  console.log('SchemaSheet: handleSchemaUpdate called with:', newSchema)
  
  // Only update fields that have actual values (not undefined, null, or empty string)
  const filteredUpdate: any = {}
  Object.keys(newSchema).forEach(key => {
    const value = newSchema[key]
    if (value !== undefined && value !== null && value !== '') {
      filteredUpdate[key] = value
    }
  })
  
  console.log('SchemaSheet: filtered update:', filteredUpdate)
  schema.value = { ...schema.value, ...filteredUpdate }
  console.log('SchemaSheet: schema after update:', schema.value)
}

// Handle data source updates from child. Do not save automatically; update local and load schema.
const handleDataSourceUpdate = (newDataSourceId: string | undefined) => {
  selectedDataSourceIdLocal.value = newDataSourceId
  if (newDataSourceId) {
    loadSchemaFromDataSource(newDataSourceId)
  }
}

// Handle save
const handleSave = () => {
  const payload = { ...schema.value, data_source_id: selectedDataSourceIdLocal.value }
  emit('save', payload)
  emit('update:open', false)
  isEditing.value = false
}
</script> 