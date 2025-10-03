<template>
  <div class="space-y-6">

    <!-- Builder Tabs -->
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-8">
        <TabsTrigger value="basic">Basic Info</TabsTrigger>
        <TabsTrigger value="measures">Measures</TabsTrigger>
        <TabsTrigger value="dimensions">Dimensions</TabsTrigger>
        <TabsTrigger value="joins">Joins</TabsTrigger>
        <TabsTrigger value="aggregations">Aggregations</TabsTrigger>
        <TabsTrigger value="filters">Filters</TabsTrigger>
        <TabsTrigger value="ordering">Ordering</TabsTrigger>
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
            <!-- Debug info -->
            <div class="mb-4 p-2 bg-gray-100 rounded text-xs">
              <div>MetricSchemaBuilder - schema.data_source_id: {{ schema.data_source_id }}</div>
              <div>MetricSchemaBuilder - schema.table_name: {{ schema.table_name }}</div>
              <div>MetricSchemaBuilder - dataSources.length: {{ dataSources.length }}</div>
            </div>
            
            <BasicInfoBuilder
              v-model:name="schema.name"
              v-model:alias="schema.alias"
              v-model:title="schema.title"
              v-model:description="schema.description"
              v-model:table-name="schema.table_name"
              v-model:query="schema.query"
              v-model:data-source-id="schema.data_source_id"
              v-model:limit="schema.limit"
              v-model:grouped="schema.grouped"
              v-model:ordered="schema.ordered"
              v-model:refresh="schema.refresh"
              v-model:cache="schema.cache"
              :available-tables="availableTables"
              :table-schema="props.tableSchema"
              :available-data-sources="dataSources"
              @update:name="updateSchema"
              @update:alias="updateSchema"
              @update:title="updateSchema"
              @update:description="updateSchema"
              @update:table-name="updateSchema"
              @update:query="updateSchema"
              @update:data-source-id="updateSchema"
              @update:limit="updateSchema"
              @update:grouped="updateSchema"
              @update:ordered="updateSchema"
              @update:refresh="updateSchema"
              @update:cache="updateSchema"
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
              :table-schema="tableSchema"
              @update:measures="updateSchema"
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
              :table-schema="tableSchema"
              @update:dimensions="updateSchema"
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
              v-model="schema.joins"
              :available-tables="availableTables"
              @update:model-value="updateSchema"
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
              @update:aggregations="updateSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Filters Tab -->
      <TabsContent value="filters" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Filters</CardTitle>
            <CardDescription>
              Define filters to apply to your metric data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FiltersBuilder
              v-model:filters="schema.filters"
              :table-schema="tableSchema"
              @update:filters="updateSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Ordering Tab -->
      <TabsContent value="ordering" class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Ordering</CardTitle>
            <CardDescription>
              Define how query results should be sorted
            </CardDescription>
          </CardHeader>
          <CardContent>
            <OrderingBuilder
              v-model:order="schema.order"
              v-model:ordered="schema.ordered"
              :available-columns="availableColumns"
              :available-tables="availableTables"
              :measures="schema.measures"
              :dimensions="schema.dimensions"
              @update:order="updateSchema"
              @update:ordered="updateSchema"
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
              @update:parameters="updateSchema"
            />
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'

// Import builder components
import BasicInfoBuilder from './BasicInfoBuilder.vue'
import MeasuresBuilder from './MeasuresBuilder.vue'
import DimensionsBuilder from './DimensionsBuilder.vue'
import JoinsBuilder from './JoinsBuilder.vue'
import AggregationsBuilder from './AggregationsBuilder.vue'
import FiltersBuilder from './FiltersBuilder.vue'
import OrderingBuilder from './OrderingBuilder.vue'
import ParametersBuilder from './ParametersBuilder.vue'

interface Props {
  selectedDataSourceId?: string
  modelValue?: any
  tableSchema?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any]
  'update:selectedDataSourceId': [value: string | undefined]
}>()

const { getDataSourceSchema, dataSources, refresh: refreshDataSources } = useDataSources()

// Component state
const activeTab = ref('basic')

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
  measures: [],
  dimensions: [],
  joins: [],
  aggregations: [],
  filters: [],
  order: [],
  parameters: {},
  refresh: undefined as any,
  cache: undefined as any,
  tableSchema: undefined as any
})

// Available data computed from schema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const availableColumns = computed(() => {
  if (!props.tableSchema?.tables) return []
  const columns: Array<{ name: string; type: string }> = []
  props.tableSchema.tables.forEach((table: any) => {
    if (table.columns) {
      table.columns.forEach((column: any) => {
        columns.push({
          name: `${table.name}.${column.name}`,
          type: column.type
        })
      })
    }
  })
  return columns
})

// Manual update function (following MeasuresBuilder pattern)
const updateSchema = () => {
  emit('update:modelValue', schema.value)
}

// When a new table schema arrives, only set table_name if not already set
watch(
  () => props.tableSchema,
  (newSchema) => {
    console.log('MetricSchemaBuilder: tableSchema changed', {
      newSchema,
      currentTableName: schema.value.table_name,
      hasTables: newSchema?.tables?.length > 0
    })
    
    if (newSchema?.tables && newSchema.tables.length > 0) {
      const first = newSchema.tables[0]?.name
      const existsInNew = newSchema.tables.some((t: any) => t.name === schema.value.table_name)
      console.log('MetricSchemaBuilder: table selection logic', {
        first,
        currentTable: schema.value.table_name,
        existsInNew,
        willUpdate: !schema.value.table_name || !existsInNew
      })
      
      // Only set to first table if no table is currently selected OR current table doesn't exist in new schema
      // Also check if we have a meaningful table name (not just empty string)
      const hasValidTableName = schema.value.table_name && schema.value.table_name.trim() !== ''
      
      // Check if we should preserve the original table name from the parent
      // This prevents overriding during initial load when the schema might not be fully initialized yet
      const shouldPreserveOriginal = props.modelValue?.table_name && 
        props.modelValue.table_name.trim() !== '' && 
        newSchema.tables.some((t: any) => t.name === props.modelValue.table_name)
      
      if (shouldPreserveOriginal) {
        schema.value.table_name = props.modelValue.table_name
        console.log('MetricSchemaBuilder: Preserving original table_name from modelValue:', props.modelValue.table_name)
        updateSchema() // Emit the update to parent
      } else if (!hasValidTableName || !existsInNew) {
        schema.value.table_name = first || ''
        console.log('MetricSchemaBuilder: Updated table_name to:', first)
        updateSchema() // Emit the update to parent
      } else {
        console.log('MetricSchemaBuilder: Keeping existing table_name:', schema.value.table_name)
      }
    }
  },
  { immediate: true }
)

// Watch for modelValue changes from parent
watch(() => props.modelValue, (newValue) => {
  if (newValue && JSON.stringify(newValue) !== JSON.stringify(schema.value)) {
    console.log('MetricSchemaBuilder: modelValue updated, newValue:', newValue)
    schema.value = { ...schema.value, ...newValue }
    console.log('MetricSchemaBuilder: schema after update:', schema.value)
  }
}, { immediate: true })

// Load data sources when component mounts
onMounted(async () => {
  console.log('MetricSchemaBuilder: Mounting, refreshing data sources...')
  await refreshDataSources()
  console.log('MetricSchemaBuilder: Data sources after refresh:', dataSources.value)
})

// Load schema from data source
const loadSchemaFromDataSource = async (dataSourceId: string) => {
  try {
    const loadedSchema = await getDataSourceSchema(dataSourceId)
    schema.value = { ...schema.value, tableSchema: loadedSchema }
    updateSchema()
  } catch (error) {
    console.error('Failed to load schema:', error)
  }
}

// Sync selectedDataSourceId prop with schema.data_source_id (only when prop changes)
watch(() => props.selectedDataSourceId, (newId) => {
  if (newId !== schema.value.data_source_id) {
    schema.value.data_source_id = newId || undefined
  }
}, { immediate: true })

// Emit data source changes back to parent (id only)
watch(
  () => schema.value.data_source_id,
  (newId: any, oldId: any) => {
    if (newId !== oldId) {
      schema.value.table_name = ''
    }
    emit('update:selectedDataSourceId', typeof newId === 'object' ? (newId?.id ?? undefined) : newId)
  },
  { immediate: false }
)

// Auto-load schema when selectedDataSourceId changes
watch(() => props.selectedDataSourceId, (newDataSourceId, oldDataSourceId) => {
  if (newDataSourceId && newDataSourceId !== oldDataSourceId) {
    loadSchemaFromDataSource(newDataSourceId)
  }
}, { immediate: true })
</script> 