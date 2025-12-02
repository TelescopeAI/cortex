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
          </CardHeader>
          <CardContent class="space-y-4">            
            <BasicInfoBuilder
              v-model:name="schemaBuilder.schema.value.name"
              v-model:alias="schemaBuilder.schema.value.alias"
              v-model:title="schemaBuilder.schema.value.title"
              v-model:description="schemaBuilder.schema.value.description"
              v-model:table-name="schemaBuilder.schema.value.table_name"
              v-model:query="schemaBuilder.schema.value.query"
              v-model:data-source-id="schemaBuilder.schema.value.data_source_id"
              v-model:limit="schemaBuilder.schema.value.limit"
              v-model:grouped="schemaBuilder.schema.value.grouped"
              v-model:ordered="schemaBuilder.schema.value.ordered"
              v-model:refresh="schemaBuilder.schema.value.refresh"
              v-model:cache="schemaBuilder.schema.value.cache"
              :available-tables="availableTables"
              :table-schema="props.tableSchema"
              :available-data-sources="dataSources"
              @update:name="(val) => schemaBuilder.updateField('name', val)"
              @update:alias="(val) => schemaBuilder.updateField('alias', val)"
              @update:title="(val) => schemaBuilder.updateField('title', val)"
              @update:description="(val) => schemaBuilder.updateField('description', val)"
              @update:table-name="(val) => schemaBuilder.updateField('table_name', val)"
              @update:query="(val) => schemaBuilder.updateField('query', val)"
              @update:data-source-id="(val) => schemaBuilder.updateField('data_source_id', val)"
              @update:limit="(val) => schemaBuilder.updateField('limit', val)"
              @update:grouped="(val) => schemaBuilder.updateField('grouped', val)"
              @update:ordered="(val) => schemaBuilder.updateField('ordered', val)"
              @update:refresh="(val) => schemaBuilder.updateField('refresh', val)"
              @update:cache="(val) => schemaBuilder.updateField('cache', val)"
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
              :measures="schemaBuilder.schema.value.measures"
              :table-schema="tableSchema"
              @update:measures="schemaBuilder.updateMeasures"
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
              :dimensions="schemaBuilder.schema.value.dimensions"
              :table-schema="tableSchema"
              @update:dimensions="schemaBuilder.updateDimensions"
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
              :model-value="schemaBuilder.schema.value.joins"
              :available-tables="availableTables"
              @update:model-value="schemaBuilder.updateJoins"
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
              :filters="schemaBuilder.schema.value.filters"
              :table-schema="tableSchema"
              @update:filters="schemaBuilder.updateFilters"
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
              :order="schemaBuilder.schema.value.order"
              :ordered="schemaBuilder.schema.value.ordered"
              :available-columns="availableColumns"
              :available-tables="availableTables"
              :measures="schemaBuilder.schema.value.measures"
              :dimensions="schemaBuilder.schema.value.dimensions"
              @update:order="schemaBuilder.updateOrder"
              @update:ordered="(val) => schemaBuilder.updateField('ordered', val)"
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
import { ref, computed, inject, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'

// Import builder components
import BasicInfoBuilder from './BasicInfoBuilder.vue'
import MeasuresBuilder from './measures/Builder.vue'
import DimensionsBuilder from './dimensions/Builder.vue'
import JoinsBuilder from './JoinsBuilder.vue'
import AggregationsBuilder from './AggregationsBuilder.vue'
import FiltersBuilder from './FiltersBuilder.vue'
import OrderingBuilder from './OrderingBuilder.vue'
import ParametersBuilder from './ParametersBuilder.vue'

interface Props {
  selectedDataSourceId?: string
  tableSchema?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:selectedDataSourceId': [value: string | undefined]
}>()

// Inject schema builder from parent
const schemaBuilder = inject<any>('schemaBuilder')

if (!schemaBuilder) {
  throw new Error('schemaBuilder not provided')
}

const { dataSources, refresh: refreshDataSources } = useDataSources()

// Component state
const activeTab = ref('basic')

// Watch for data source changes and emit them to parent
watch(() => schemaBuilder.schema.value.data_source_id, (newDataSourceId) => {
  if (newDataSourceId) {
    emit('update:selectedDataSourceId', newDataSourceId)
  }
}, { immediate: false })

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
  if (schemaBuilder.schema.value.table_name) {
    tables.add(schemaBuilder.schema.value.table_name)
  }
  
  // Add tables from measures
  schemaBuilder.schema.value.measures?.forEach((measure: any) => {
    if (measure.table) tables.add(measure.table)
  })
  
  // Add tables from dimensions
  schemaBuilder.schema.value.dimensions?.forEach((dimension: any) => {
    if (dimension.table) tables.add(dimension.table)
  })
  
  // Add tables from filters
  schemaBuilder.schema.value.filters?.forEach((filter: any) => {
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
  
  const baseTable = schemaBuilder.schema.value.table_name
  if (!baseTable) return
  
  // Get existing joins (both user-created and auto-generated)
  const existingJoins = schemaBuilder.schema.value.joins || []
  
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
    schemaBuilder.updateJoins([...(existingJoins as any[]), ...newJoins] as any[])
  }
}

// Watch for changes in used tables and auto-generate joins
watch(usedTables, () => {
  autoGenerateJoins()
}, { deep: true, immediate: true })

// Manual join generation triggered by user
const manuallyGenerateJoins = () => {
  autoGenerateJoins()
}
</script> 