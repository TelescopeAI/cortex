<template>
  <div class="space-y-4">
    <!-- Add Dimension Button -->
    <div v-if="showHeader !== false" class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Dimensions</h4>
      <ColumnSelector
        :available-tables="availableTables"
        button-text="Add Dimension"
        @select="addDimension"
      />
    </div>

    <!-- Dimensions List -->
    <div v-if="props.dimensions.length === 0 && showEmptyState !== false" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Grid class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No dimensions defined</p>
      <p class="text-xs text-muted-foreground">Add a dimension to enable grouping</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(dimension, index) in props.dimensions"
        :key="index"
        class="p-5 hover:shadow-md transition-shadow"
      >
        <div class="space-y-5">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div class="p-1.5 rounded-md bg-green-50 dark:bg-green-950">
                <Grid class="h-4 w-4 text-green-600 dark:text-green-400" />
              </div>
              <span class="font-medium text-base">{{ dimension.name || 'Unnamed Dimension' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeDimension(index)"
              class="hover:bg-red-50 hover:text-red-600"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Sentence-Completion Interface -->
          <div class="space-y-3">
            <!-- Row 1: Select [column] from the table [table] -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm text-muted-foreground">Select</span>
              
              <!-- Column Selection (dropdown based on selected table) -->
              <Select 
                :model-value="dimension.query" 
                @update:model-value="(value) => updateDimension(index, 'query', value)"
                :disabled="!dimension.table"
              >
                <SelectTrigger class="w-auto min-w-[200px] h-9 justify-between">
                  <SelectValue placeholder="Select column" as-child>
                    <div class="flex items-center justify-between w-full gap-3">
                      <span>{{ dimension.query || 'Select column' }}</span>
                      <Badge 
                        v-if="dimension.query && getSelectedColumnType(dimension.table, dimension.query)"
                        :class="getColumnTypeBadgeClass(getSelectedColumnType(dimension.table, dimension.query) || '')"
                      >
                        {{ getSelectedColumnType(dimension.table, dimension.query) }}
                      </Badge>
                    </div>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="column in getColumnsForTable(dimension.table)"
                    :key="column.name"
                    :value="column.name"
                  >
                    <div class="flex items-center justify-between w-full gap-3">
                      <span>{{ column.name }}</span>
                      <Badge :class="getColumnTypeBadgeClass(column.type)">
                        {{ column.type }}
                      </Badge>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>

              <span class="text-sm text-muted-foreground">from the table</span>
              
              <!-- Table Selection -->
              <Select :model-value="dimension.table" @update:model-value="(value) => updateDimension(index, 'table', value)">
                <SelectTrigger class="w-auto min-w-[180px] h-9">
                  <SelectValue placeholder="Select table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">
                    {{ table.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Conditional Logic Mode Selector -->
            <div v-if="dimension.table" class="pt-4 border-t">
              <div class="flex items-center gap-2 mb-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  :class="{ 'bg-accent': !dimension.conditional }"
                  @click="toggleConditionalMode(dimension, false)"
                >
                  <Grid class="h-4 w-4 mr-2" />
                  Simple Column
                </Button>
                
                <Button 
                  variant="outline"
                  size="sm"
                  :class="{ 'bg-accent': dimension.conditional }"
                  @click="toggleConditionalMode(dimension, true)"
                >
                  <GitBranch class="h-4 w-4 mr-2" />
                  Conditional Logic
                </Button>
              </div>

              <!-- Conditional Builder -->
              <div v-if="dimension.conditional" class="mt-4">
                <ConditionalBuilder
                  :model-value="dimension.conditions || null"
                  @update:model-value="updateConditions(dimension, $event)"
                  :available-tables="availableTables.map((t: any) => t.name)"
                  :available-columns="getAvailableColumnsMap()"
                />
              </div>
            </div>

            <!-- Row 2: Name it as [name] -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-muted-foreground">Name it as</span>
              <Input
                :model-value="dimension.name"
                placeholder="Dimension name"
                class="flex-1 h-9"
                :disabled="readOnlyName"
                @update:model-value="(value) => updateDimension(index, 'name', value)"
              />
            </div>
          </div>

           

          <!-- Advanced Section -->
          <div class="pt-3">
            <button 
              type="button"
              class="flex items-center justify-between w-full text-xs text-muted-foreground hover:text-foreground transition-colors group"
              @click="toggleAdvanced(index)"
            >
              <span class="flex items-center gap-1.5">
                <Settings class="h-3.5 w-3.5" />
                Advanced
              </span>
              <ChevronDown :class="['h-3.5 w-3.5 transition-transform duration-200', showAdvanced[index] && 'rotate-180']" />
            </button>

            <div 
              v-if="showAdvanced[index]" 
              class="mt-4 space-y-4 pt-4 border-t"
            >
            <!-- Combine Columns -->
           <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label class="text-xs font-medium text-muted-foreground">Combine Columns</Label>
                  <Button
                    variant="outline"
                    size="sm"
                    @click="addCombineColumn(dimension)"
                    class="h-7 text-xs"
                  >
                    <Plus class="h-3 w-3 mr-1" />
                    Add Column
                  </Button>
                </div>
                <p class="text-xs text-muted-foreground">
                  Concatenate additional columns to this dimension (e.g., first_name + last_name)
                </p>
                
                <!-- Combine columns list -->
                <div v-if="dimension.combine && dimension.combine.length > 0" class="space-y-2 mt-2">
                  <Card 
                    v-for="(combineSpec, combineIndex) in dimension.combine"
                    :key="combineIndex"
                    class="p-3 bg-muted/30"
                  >
                    <div class="space-y-2">
                      <!-- Column and table selection -->
                      <div class="flex items-center gap-2">
                        <Select 
                          :model-value="combineSpec.table" 
                          @update:model-value="(value) => updateCombineSpec(dimension, combineIndex, 'table', value)"
                        >
                          <SelectTrigger class="w-auto min-w-[120px] h-8 text-xs">
                            <SelectValue placeholder="Table" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">
                              {{ table.name }}
                            </SelectItem>
                          </SelectContent>
                        </Select>

                        <Select 
                          :model-value="combineSpec.query" 
                          @update:model-value="(value) => updateCombineSpec(dimension, combineIndex, 'query', value)"
                          :disabled="!combineSpec.table"
                        >
                          <SelectTrigger class="flex-1 h-8 text-xs">
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem 
                              v-for="column in getColumnsForTable(combineSpec.table)"
                              :key="column.name"
                              :value="column.name"
                            >
                              {{ column.name }}
                            </SelectItem>
                          </SelectContent>
                        </Select>

                        <Button
                          variant="ghost"
                          size="sm"
                          @click="removeCombineColumn(dimension, combineIndex)"
                          class="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                        >
                          <X class="h-3 w-3" />
                        </Button>
                      </div>

                      <!-- Delimiter input -->
                      <div class="flex items-center gap-2">
                        <Label class="text-xs text-muted-foreground whitespace-nowrap">Delimiter:</Label>
                        <Input
                          :model-value="combineSpec.delimiter"
                          placeholder="Space"
                          class="h-7 text-xs flex-1"
                          @update:model-value="(value) => updateCombineSpec(dimension, combineIndex, 'delimiter', value)"
                        />
                        <span class="text-xs text-muted-foreground">(default: space)</span>
                      </div>
                    </div>
                  </Card>
                </div>
                
                <p v-else class="text-xs text-center text-muted-foreground py-4 border border-dashed rounded-md">
                  No columns combined. Click "Add Column" to combine multiple columns.
                </p>
              </div>
              
              <!-- Description -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                <Textarea
                  :model-value="dimension.description"
                  placeholder="Describe what this dimension represents..."
                  rows="2"
                  class="resize-none"
                  @update:model-value="(value) => updateDimension(index, 'description', value)"
                />
              </div>

              <!-- Output Formatting -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Output Formatting</Label>
                <OutputFormatEditor
                  :model-value="dimension.formatting"
                  object-type="dimension"
                  @update:model-value="(value) => updateDimension(index, 'formatting', value)"
                />
              </div>

             
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Grid, X, Settings, ChevronDown, Plus, GitBranch } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import OutputFormatEditor from './OutputFormatEditor.vue'
import ConditionalBuilder from './ConditionalBuilder.vue'
import { humanize } from '~/utils/stringCase'
import type { Condition } from '~/types/conditionals'

interface CombineColumnSpec {
  query: string
  table?: string
  delimiter?: string
}

interface Dimension {
  name: string
  description?: string
  query: string
  table?: string
  formatting?: any[]
  combine?: CombineColumnSpec[]
  conditional?: boolean
  conditions?: Condition | null
}

interface Props {
  dimensions?: Dimension[]
  availableColumns?: Array<{ name: string; type: string }>
  tableSchema?: any
  showHeader?: boolean
  showEmptyState?: boolean
  readOnlyName?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  dimensions: () => []
})

const emit = defineEmits<{
  'update:dimensions': [value: Dimension[]]
}>()

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const showAdvanced = ref<Record<number, boolean>>({})

const updateDimensions = (newDimensions: Dimension[]) => {
  emit('update:dimensions', newDimensions)
}

const updateDimension = (index: number, field: keyof Dimension, value: any) => {
  const updated = [...props.dimensions]
  if (updated[index]) {
    updated[index] = { ...updated[index], [field]: value }
    
    // Handle table change - reset query if column doesn't exist in new table
    if (field === 'table' && value) {
      const columns = getColumnsForTable(value)
      const columnExists = columns.some((col: any) => col.name === updated[index]?.query)
      if (!columnExists) {
        updated[index].query = ''
      }
    }
    
    updateDimensions(updated)
  }
}

const updateCombineSpec = (dimension: Dimension, combineIndex: number, field: string, value: any) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  if (updatedDimension.combine && updatedDimension.combine[combineIndex]) {
    updatedDimension.combine[combineIndex] = { ...updatedDimension.combine[combineIndex], [field]: value }
    
    // Handle table change for combine spec - reset query if column doesn't exist in new table
    if (field === 'table' && value && updatedDimension.combine?.[combineIndex]) {
      const columns = getColumnsForTable(value)
      const columnExists = columns.some((col: any) => col.name === updatedDimension.combine?.[combineIndex]?.query)
      if (!columnExists) {
        updatedDimension.combine[combineIndex].query = ''
      }
    }
  }
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const toggleAdvanced = (index: number) => {
  showAdvanced.value[index] = !showAdvanced.value[index]
}

const getColumnsForTable = (tableName?: string) => {
  if (!tableName) return []
  const table = availableTables.value.find((t: any) => t.name === tableName)
  return table?.columns || []
}

const getSelectedColumnType = (tableName?: string, columnName?: string) => {
  if (!tableName || !columnName) return null
  const columns = getColumnsForTable(tableName)
  const column = columns.find((col: any) => col.name === columnName)
  return column?.type || null
}

const getColumnTypeBadgeClass = (type: string) => {
  const typeUpper = type.toUpperCase()
  
  // Numeric types - blue
  if (typeUpper.includes('INT') || typeUpper.includes('DECIMAL') || 
      typeUpper.includes('NUMERIC') || typeUpper.includes('FLOAT') || 
      typeUpper.includes('DOUBLE') || typeUpper.includes('REAL') ||
      typeUpper.includes('MONEY')) {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 text-[10px] px-1.5 py-0.5'
  }
  
  // Text types - purple
  if (typeUpper.includes('CHAR') || typeUpper.includes('TEXT') || 
      typeUpper.includes('VARCHAR') || typeUpper.includes('STRING') ||
      typeUpper.includes('CLOB')) {
    return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 text-[10px] px-1.5 py-0.5'
  }
  
  // Date/Time types - green
  if (typeUpper.includes('DATE') || typeUpper.includes('TIME') || 
      typeUpper.includes('TIMESTAMP')) {
    return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-[10px] px-1.5 py-0.5'
  }
  
  // Boolean types - amber
  if (typeUpper.includes('BOOL') || typeUpper.includes('BIT')) {
    return 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300 text-[10px] px-1.5 py-0.5'
  }
  
  // Default - gray
  return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[10px] px-1.5 py-0.5'
}

// onTableChange is now handled in updateDimension function

const addDimension = (tableName: string, column: any) => {
  const humanizedName = humanize(column.name)
  
  const newDimension: Dimension = {
    name: humanizedName,
    description: `Dimension based on ${tableName}.${column.name}`,
    query: column.name,
    table: tableName,
    formatting: [],
    combine: []
  }
  
  updateDimensions([...props.dimensions, newDimension])
}

const removeDimension = (index: number) => {
  const updated = [...props.dimensions]
  updated.splice(index, 1)
  updateDimensions(updated)
}

const addCombineColumn = (dimension: Dimension) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  if (!updatedDimension.combine) {
    updatedDimension.combine = []
  }
  updatedDimension.combine.push({
    query: '',
    table: updatedDimension.table,
    delimiter: ' '
  })
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const removeCombineColumn = (dimension: Dimension, combineIndex: number) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  if (updatedDimension.combine) {
    updatedDimension.combine.splice(combineIndex, 1)
  }
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const onCombineTableChange = (dimension: Dimension, combineIndex: number) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  if (updatedDimension.combine && updatedDimension.combine[combineIndex]) {
    const combineSpec = updatedDimension.combine[combineIndex]
    if (combineSpec.query) {
      const columns = getColumnsForTable(combineSpec.table)
      const columnExists = columns.some((col: any) => col.name === combineSpec.query)
      if (!columnExists) {
        combineSpec.query = ''
      }
    }
  }
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const toggleConditionalMode = (dimension: Dimension, isConditional: boolean) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  updatedDimension.conditional = isConditional
  
  // Initialize conditions if switching to conditional mode
  if (isConditional && !updatedDimension.conditions) {
    updatedDimension.conditions = {
      when_clauses: [],
      else_return: ''
    }
  }
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const updateConditions = (dimension: Dimension, conditions: Condition | null) => {
  const dimensionIndex = props.dimensions.findIndex(d => d === dimension)
  if (dimensionIndex === -1) return
  
  const updatedDimension = { ...dimension }
  updatedDimension.conditions = conditions
  
  const updated = [...props.dimensions]
  updated[dimensionIndex] = updatedDimension
  updateDimensions(updated)
}

const getAvailableColumnsMap = (): Record<string, string[]> => {
  const columnsMap: Record<string, string[]> = {}
  
  availableTables.value.forEach((table: any) => {
    columnsMap[table.name] = table.columns.map((col: any) => col.name)
  })
  
  return columnsMap
}
</script>
