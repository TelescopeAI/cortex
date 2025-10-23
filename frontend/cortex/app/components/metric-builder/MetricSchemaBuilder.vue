<template>
  <div class="space-y-6">

    <!-- Builder Tabs -->
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-8">
        <TabsTrigger value="basic">Basic</TabsTrigger>
        <TabsTrigger value="measures">Measures</TabsTrigger>
        <TabsTrigger value="dimensions">Dimensions</TabsTrigger>
        <TabsTrigger value="joins">Joins</TabsTrigger>
        <TabsTrigger value="filters">Filters</TabsTrigger>
        <TabsTrigger value="ordering">Ordering</TabsTrigger>
        <!-- <TabsTrigger value="parameters">Parameters</TabsTrigger> -->
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
              @generate-joins="manuallyGenerateJoins"
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
      <!-- <TabsContent value="parameters" class="space-y-4">
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
      </TabsContent> -->
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
  measures: [] as any[],
  dimensions: [] as any[],
  joins: [] as any[],
  aggregations: [] as any[],
  filters: [] as any[],
  order: [] as any[],
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

// Track which join pairs are auto-generated
const autoGeneratedPairs = ref<Set<string>>(new Set())

// Track which tables are being used
const usedTables = computed(() => {
  const tables = new Set<string>()
  
  // Add base table
  if (schema.value.table_name) {
    tables.add(schema.value.table_name)
  }
  
  // Add tables from measures
  schema.value.measures?.forEach((measure: any) => {
    if (measure.table) tables.add(measure.table)
  })
  
  // Add tables from dimensions
  schema.value.dimensions?.forEach((dimension: any) => {
    if (dimension.table) tables.add(dimension.table)
  })
  
  // Add tables from filters
  schema.value.filters?.forEach((filter: any) => {
    if (filter.table) tables.add(filter.table)
  })
  
  return Array.from(tables)
})

// Find common columns between two tables
const findCommonColumns = (table1Name: string, table2Name: string) => {
  if (!props.tableSchema?.tables) return []
  
  const table1 = props.tableSchema.tables.find((t: any) => t.name === table1Name)
  const table2 = props.tableSchema.tables.find((t: any) => t.name === table2Name)
  
  if (!table1 || !table2) return []
  
  const commonColumns: Array<{ column: string; table1: string; table2: string }> = []
  
  table1.columns?.forEach((col1: any) => {
    table2.columns?.forEach((col2: any) => {
      // Check for exact name match or foreign key patterns
      if (col1.name === col2.name) {
        commonColumns.push({
          column: col1.name,
          table1: table1Name,
          table2: table2Name
        })
      }
      // Check for foreign key patterns (e.g., user_id in one table, id in another)
      else if (
        (col1.name === 'id' && col2.name === `${table1Name}_id`) ||
        (col2.name === 'id' && col1.name === `${table2Name}_id`)
      ) {
        commonColumns.push({
          column: col1.name === 'id' ? col2.name : col1.name,
          table1: table1Name,
          table2: table2Name
        })
      }
    })
  })
  
  return commonColumns
}

// Auto-generate joins when multiple tables are detected
const autoGenerateJoins = () => {
  const tables = usedTables.value
  
  // Need at least 2 tables to create a join
  if (tables.length < 2) {
    return
  }
  
  const baseTable = schema.value.table_name
  if (!baseTable) return
  
  // Get existing joins (both user-created and auto-generated)
  const existingJoins = schema.value.joins || []
  
  // Track which table pairs already have joins
  const existingPairs = new Set(
    existingJoins.map((join: any) => 
      [join.left_table, join.right_table].sort().join('|')
    )
  )
  
  const newJoins: any[] = []
  
  // Strategy 1: Create joins from base table to all other tables
  tables.forEach(tableName => {
    if (tableName === baseTable) return
    
    const pairKey = [baseTable, tableName].sort().join('|')
    
    // Skip if join already exists
    if (existingPairs.has(pairKey)) return
    
    // Find common columns
    const commonColumns = findCommonColumns(baseTable, tableName)
    
    if (commonColumns.length > 0) {
      // Use the first common column (or prioritize 'id' patterns)
      const bestMatch = commonColumns.find(c => 
        c.column.includes('id') || c.column === 'id'
      ) || commonColumns[0]
      
      if (bestMatch) {
        // Determine which column to use for each table
        let leftColumn = bestMatch.column
        let rightColumn = bestMatch.column
        
        // Handle foreign key patterns intelligently
        const baseTableId = `${baseTable.replace(/s$/, '')}_id` // e.g., "matches" -> "match_id"
        const targetTableId = `${tableName.replace(/s$/, '')}_id` // e.g., "players" -> "player_id"
        
        // Check various FK patterns
        if (baseTable.toLowerCase().includes('id') || bestMatch.column === 'id') {
          // Base table has an id column
          if (bestMatch.column.toLowerCase().includes(baseTable.toLowerCase())) {
            leftColumn = 'id'
            rightColumn = bestMatch.column
          } else if (bestMatch.column.toLowerCase().includes(tableName.toLowerCase())) {
            leftColumn = bestMatch.column
            rightColumn = 'id'
          } else {
            // Default: use the same column name
            leftColumn = bestMatch.column
            rightColumn = bestMatch.column
          }
        } else {
          leftColumn = bestMatch.column
          rightColumn = bestMatch.column
        }
        
        const newJoin = {
          name: `${baseTable}_${tableName}_join`,
          join_type: 'left',
          left_table: baseTable,
          right_table: tableName,
          conditions: [{
            left_table: baseTable,
            left_column: leftColumn,
            right_table: tableName,
            right_column: rightColumn,
            operator: '='
          }],
          _autogenerated: true // Internal flag for UI only
        }
        
        newJoins.push(newJoin)
        
        // Track this pair as auto-generated
        autoGeneratedPairs.value.add(pairKey)
        existingPairs.add(pairKey)
      }
    }
  })
  
  // Note: We only auto-generate joins from the base table to other tables (Strategy 1).
  // Complex multi-hop joins (e.g., table1 -> table2 -> table3) should be created manually
  // by the user to ensure correct join ordering and avoid SQL errors.
  
  // Add new joins to schema
  if (newJoins.length > 0) {
    schema.value.joins = [...(existingJoins as any[]), ...newJoins] as any[]
  }
}

// Watch for changes in used tables and auto-generate joins
watch(usedTables, () => {
  autoGenerateJoins()
}, { deep: true, immediate: true })

// Manual join generation triggered by user
const manuallyGenerateJoins = () => {
  autoGenerateJoins()
  updateSchema()
}

// Manual update function (following MeasuresBuilder pattern)
const updateSchema = () => {
  // Remove _autogenerated flag before emitting (internal UI state only)
  const cleanedSchema = {
    ...schema.value,
    joins: schema.value.joins?.map((join: any) => {
      const { _autogenerated, ...cleanJoin } = join
      return cleanJoin
    })
  }
  emit('update:modelValue', cleanedSchema)
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
      const currentTableName = schema.value.table_name
      
      console.log('MetricSchemaBuilder: table selection logic', {
        first,
        currentTable: currentTableName,
        existsInNew,
        willUpdate: !currentTableName || !existsInNew
      })
      
      // Only set to first table if no table is currently selected OR current table doesn't exist in new schema
      // Also check if we have a meaningful table name (not just empty string)
      const hasValidTableName = currentTableName && currentTableName.trim() !== ''
      
      // Check if we should preserve the original table name from the parent
      // This prevents overriding during initial load when the schema might not be fully initialized yet
      const shouldPreserveOriginal = props.modelValue?.table_name && 
        props.modelValue.table_name.trim() !== '' && 
        newSchema.tables.some((t: any) => t.name === props.modelValue.table_name)
      
      let newTableName = currentTableName
      
      if (shouldPreserveOriginal) {
        newTableName = props.modelValue.table_name
        console.log('MetricSchemaBuilder: Preserving original table_name from modelValue:', props.modelValue.table_name)
      } else if (!hasValidTableName || !existsInNew) {
        newTableName = first || ''
        console.log('MetricSchemaBuilder: Updated table_name to:', first)
      } else {
        console.log('MetricSchemaBuilder: Keeping existing table_name:', currentTableName)
      }
      
      // Only emit update if table_name actually changed
      if (newTableName !== currentTableName) {
        schema.value.table_name = newTableName
        updateSchema() // Emit the update to parent
      }
    }
  },
  { immediate: true }
)

// Watch for modelValue changes from parent
watch(() => props.modelValue, (newValue) => {
  if (newValue && JSON.stringify(newValue) !== JSON.stringify(schema.value)) {
    console.log('MetricSchemaBuilder: modelValue updated, newValue:', newValue)
    // Ensure arrays are properly copied (not referenced)
    schema.value = {
      ...schema.value,
      ...newValue,
      // Explicitly handle arrays to ensure they're properly copied
      measures: newValue.measures ? [...newValue.measures] : schema.value.measures,
      dimensions: newValue.dimensions ? [...newValue.dimensions] : schema.value.dimensions,
      joins: newValue.joins ? [...newValue.joins] : schema.value.joins,
      filters: newValue.filters ? [...newValue.filters] : schema.value.filters,
      order: newValue.order ? [...newValue.order] : schema.value.order,
    }
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