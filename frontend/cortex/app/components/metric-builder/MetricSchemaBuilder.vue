<template>
  <div class="space-y-6">
    <!-- Header with Preview Toggle -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold">Metric Schema Builder</h3>
        <p class="text-sm text-muted-foreground">Build your metric schema using the visual builder or JSON editor</p>
      </div>
      <div class="flex items-center space-x-2">
        <Button 
          variant="outline" 
          size="sm" 
          @click="showJsonPreview = !showJsonPreview"
        >
          <Code class="h-4 w-4 mr-2" />
          {{ showJsonPreview ? 'Hide' : 'Show' }} JSON
        </Button>
        <Button
          variant="outline"
          size="sm"
          @click="loadSchemaFromDataSource"
          :disabled="!selectedDataSourceId || schemaLoading"
        >
          <Database class="h-4 w-4 mr-2" />
          {{ schemaLoading ? 'Loading...' : 'Load Schema' }}
        </Button>
      </div>
    </div>

    <!-- JSON Preview -->
    <Card v-if="showJsonPreview">
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
          rows="20"
          class="font-mono text-sm"
          placeholder="Schema JSON will appear here as you build..."
        />
      </CardContent>
    </Card>

    <!-- Builder Tabs -->
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-6">
        <TabsTrigger value="basic">Basic Info</TabsTrigger>
        <TabsTrigger value="measures">Measures</TabsTrigger>
        <TabsTrigger value="dimensions">Dimensions</TabsTrigger>
        <TabsTrigger value="joins">Joins</TabsTrigger>
        <TabsTrigger value="aggregations">Aggregations</TabsTrigger>
        <TabsTrigger value="parameters">Parameters</TabsTrigger>
      </TabsList>

      <!-- Basic Information Tab -->
      <TabsContent value="basic" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>
              Configure the basic properties of your metric
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <BasicInfoBuilder
              v-model:table-name="schema.table_name"
              v-model:query="schema.query"
              v-model:data-source="schema.data_source"
              :available-tables="availableTables"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Measures Tab -->
      <TabsContent value="measures" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Measures</CardTitle>
            <CardDescription>
              Define quantitative measurements for your metric
            </CardDescription>
          </CardHeader>
          <CardContent>
            <MeasuresBuilder
              v-model:measures="schema.measures"
              :available-columns="availableColumns"
              :table-schema="tableSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Dimensions Tab -->
      <TabsContent value="dimensions" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Dimensions</CardTitle>
            <CardDescription>
              Define categorical attributes for grouping and filtering
            </CardDescription>
          </CardHeader>
          <CardContent>
            <DimensionsBuilder
              v-model:dimensions="schema.dimensions"
              :available-columns="availableColumns"
              :table-schema="tableSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Joins Tab -->
      <TabsContent value="joins" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Joins</CardTitle>
            <CardDescription>
              Define relationships between tables
            </CardDescription>
          </CardHeader>
          <CardContent>
            <JoinsBuilder
              v-model:joins="schema.joins"
              :available-tables="availableTables"
              :table-schema="tableSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Aggregations Tab -->
      <TabsContent value="aggregations" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Aggregations</CardTitle>
            <CardDescription>
              Define how data should be aggregated
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AggregationsBuilder
              v-model:aggregations="schema.aggregations"
              :available-columns="availableColumns"
              :measures="schema.measures"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Parameters Tab -->
      <TabsContent value="parameters" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Parameters</CardTitle>
            <CardDescription>
              Define runtime parameters for dynamic queries
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ParametersBuilder
              v-model:parameters="schema.parameters"
            />
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Textarea } from '~/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Code, Database } from 'lucide-vue-next'
import { useDataSources } from '~/composables/useDataSources'
import { toast } from 'vue-sonner'

// Import builder components
import BasicInfoBuilder from './BasicInfoBuilder.vue'
import MeasuresBuilder from './MeasuresBuilder.vue'
import DimensionsBuilder from './DimensionsBuilder.vue'
import JoinsBuilder from './JoinsBuilder.vue'
import AggregationsBuilder from './AggregationsBuilder.vue'
import ParametersBuilder from './ParametersBuilder.vue'

interface Props {
  selectedDataSourceId?: string
  modelValue?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const { getDataSourceSchema } = useDataSources()

// Component state
const activeTab = ref('basic')
const showJsonPreview = ref(false)
const schemaLoading = ref(false)
const tableSchema = ref<any>(null)

// Schema data structure
const schema = ref({
  table_name: '',
  query: '',
  data_source: 'default',
  measures: [],
  dimensions: [],
  joins: [],
  aggregations: [],
  parameters: {}
})

// Available data computed from schema
const availableTables = computed(() => {
  if (!tableSchema.value?.tables) return []
  return tableSchema.value.tables.map((table: any) => ({
    name: table.name,
    columns: table.columns
  }))
})

const availableColumns = computed(() => {
  if (!schema.value.table_name || !tableSchema.value?.tables) return []
  
  const selectedTable = tableSchema.value.tables.find(
    (table: any) => table.name === schema.value.table_name
  )
  
  return selectedTable?.columns || []
})

// Generated JSON
const generatedJson = computed(() => {
  const cleanSchema = JSON.parse(JSON.stringify(schema.value))
  
  // Remove empty arrays and null values
  Object.keys(cleanSchema).forEach(key => {
    if (Array.isArray(cleanSchema[key]) && cleanSchema[key].length === 0) {
      delete cleanSchema[key]
    } else if (cleanSchema[key] === null || cleanSchema[key] === '') {
      delete cleanSchema[key]
    }
  })
  
  return JSON.stringify(cleanSchema, null, 2)
})

// Load schema from data source
const loadSchemaFromDataSource = async () => {
  if (!props.selectedDataSourceId) {
    toast.error('Please select a data source first')
    return
  }

  schemaLoading.value = true
  try {
    tableSchema.value = await getDataSourceSchema(props.selectedDataSourceId)
    toast.success('Schema loaded successfully')
  } catch (error) {
    console.error('Failed to load schema:', error)
    toast.error('Failed to load schema from data source')
  } finally {
    schemaLoading.value = false
  }
}

// Watch for changes and emit to parent
watch(schema, (newSchema) => {
  emit('update:modelValue', newSchema)
}, { deep: true })

// Watch for modelValue changes from parent
watch(() => props.modelValue, (newValue) => {
  if (newValue && JSON.stringify(newValue) !== JSON.stringify(schema.value)) {
    schema.value = { ...schema.value, ...newValue }
  }
}, { immediate: true })

// Auto-load schema if data source is provided
watch(() => props.selectedDataSourceId, (newId) => {
  if (newId) {
    // Always reload schema when data source changes
    tableSchema.value = null
    loadSchemaFromDataSource()
  }
}, { immediate: true })
</script> 