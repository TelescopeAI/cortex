<template>
  <div class="space-y-4">
    <!-- Add Measure Button -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Measures</h4>
      <div class="flex items-center space-x-2">
        <ColumnSelector
          :available-tables="availableTables"
          button-text="Add Measure"
          @select="addMeasure"
        />
        <Button variant="outline" size="sm" @click="addCustomMeasure">
          <Code class="h-4 w-4 mr-2" />
          Custom Measure
        </Button>
      </div>
    </div>

    <!-- Measures List -->
    <div v-if="props.measures.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Target class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No measures defined</p>
      <p class="text-xs text-muted-foreground">Add a measure to get started</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(measure, index) in props.measures"
        :key="index"
        class="p-5 hover:shadow-md transition-shadow"
      >
        <div class="space-y-5">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div class="p-1.5 rounded-md bg-blue-50 dark:bg-blue-950">
                <Target class="h-4 w-4 text-blue-600 dark:text-blue-400" />
              </div>
              <span class="font-medium text-base">{{ measure.name || 'Unnamed Measure' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeMeasure(index)"
              class="hover:bg-red-50 hover:text-red-600"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Sentence-Completion Interface -->
          <div class="space-y-3">
            <!-- Row 1: Calculate the [type] of [column] -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm text-muted-foreground">Calculate the</span>
              <Select :model-value="measure.type" @update:model-value="(value) => updateMeasure(index, 'type', value)">
                <SelectTrigger class="w-auto min-w-[130px] h-9">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="count">count</SelectItem>
                  <SelectItem value="sum">sum</SelectItem>
                  <SelectItem value="avg">average</SelectItem>
                  <SelectItem value="min">minimum</SelectItem>
                  <SelectItem value="max">maximum</SelectItem>
                  <SelectItem value="count_distinct">distinct count</SelectItem>
                  <SelectItem value="custom">custom</SelectItem>
                </SelectContent>
              </Select>
              <span class="text-sm text-muted-foreground">of</span>
              
              <!-- Column Selection (dropdown based on selected table) -->
              <Select 
                :model-value="measure.query" 
                @update:model-value="(value) => updateMeasure(index, 'query', value)"
                :disabled="!measure.table"
              >
                <SelectTrigger class="w-auto min-w-[200px] h-9 justify-between">
                  <SelectValue placeholder="Select column" as-child>
                    <div class="flex items-center justify-between w-full gap-3">
                      <span>{{ measure.query || 'Select column' }}</span>
                      <Badge 
                        v-if="measure.query && getSelectedColumnType(measure.table, measure.query)"
                        :class="getColumnTypeBadgeClass(getSelectedColumnType(measure.table, measure.query) || '')"
                      >
                        {{ getSelectedColumnType(measure.table, measure.query) }}
                      </Badge>
                    </div>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="column in getColumnsForTable(measure.table)"
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
            </div>

            <!-- Row 2: from the table [table] -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-muted-foreground">from the table</span>
              
              <!-- Table Selection -->
              <Select :model-value="measure.table" @update:model-value="(value) => updateMeasure(index, 'table', value)">
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
            <div v-if="measure.table" class="pt-4 border-t">
              <div class="flex items-center gap-2 mb-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  :class="{ 'bg-accent': !measure.conditional }"
                  @click="toggleConditionalMode(measure, false)"
                >
                  <Target class="h-4 w-4 mr-2" />
                  Simple Column
                </Button>
                
                <Button 
                  variant="outline"
                  size="sm"
                  :class="{ 'bg-accent': measure.conditional }"
                  @click="toggleConditionalMode(measure, true)"
                >
                  <GitBranch class="h-4 w-4 mr-2" />
                  Conditional Logic
                </Button>
              </div>

              <!-- Conditional Builder -->
              <div v-if="measure.conditional" class="mt-4">
                <ConditionalBuilder
                  :model-value="measure.conditions || null"
                  @update:model-value="updateConditions(measure, $event)"
                  :available-tables="availableTables.map((t: any) => t.name)"
                  :available-columns="getAvailableColumnsMap()"
                />
              </div>
            </div>

            <!-- Row 3: Name it as [name] -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-muted-foreground">Name it as</span>
              <Input
                :model-value="measure.name"
                placeholder="Measure name"
                class="flex-1 h-9"
                @update:model-value="(value) => updateMeasure(index, 'name', value)"
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
              <!-- Alias -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Alias</Label>
                <Input
                  :model-value="measure.alias"
                  placeholder="Optional alias for this measure"
                  class="h-9"
                  @update:model-value="(value) => updateMeasure(index, 'alias', value)"
                />
              </div>

              <!-- Description -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                <Textarea
                  :model-value="measure.description"
                  placeholder="Describe what this measure represents..."
                  rows="2"
                  class="resize-none"
                  @update:model-value="(value) => updateMeasure(index, 'description', value)"
                />
              </div>

              <!-- Output Formatting -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Output Formatting</Label>
                <OutputFormatEditor
                  :model-value="measure.formatting"
                  object-type="measure"
                  @update:model-value="(value) => updateMeasure(index, 'formatting', value)"
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
import { ref, computed } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Target, X, Code, Settings, ChevronDown, GitBranch } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import OutputFormatEditor from './OutputFormatEditor.vue'
import ConditionalBuilder from './ConditionalBuilder.vue'
import { toSnakeCase, humanize } from '~/utils/stringCase'
import type { Condition } from '~/types/conditionals'

interface Measure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
  conditional?: boolean
  conditions?: Condition | null
}

interface Props {
  measures?: Measure[]
  availableColumns?: Array<{ name: string; type: string }>
  tableSchema?: any
}

const props = withDefaults(defineProps<Props>(), {
  measures: () => []
})

const emit = defineEmits<{
  'update:measures': [value: Measure[]]
}>()

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const showAdvanced = ref<Record<number, boolean>>({})

const updateMeasures = (newMeasures: Measure[]) => {
  console.log('[MeasuresBuilder] updateMeasures called with:', newMeasures)
  emit('update:measures', newMeasures)
}

const updateMeasure = (index: number, field: keyof Measure, value: any) => {
  console.log('[MeasuresBuilder] updateMeasure called:', { index, field, value })
  
  const updated = [...props.measures]
  if (updated[index]) {
    const currentMeasure = updated[index]
    console.log('[MeasuresBuilder] Current measure before update:', currentMeasure)
    
    // Handle name change - auto-fill alias only (not query)
    if (field === 'name') {
      const newNameStr = String(value)
      const snakeCaseName = toSnakeCase(newNameStr)
      
      console.log('[MeasuresBuilder] Name change - newNameStr:', newNameStr, 'snakeCaseName:', snakeCaseName)
      console.log('[MeasuresBuilder] Current alias:', currentMeasure.alias, 'Current query:', currentMeasure.query)
      
      updated[index] = { 
        ...currentMeasure, 
        name: newNameStr,
        // Auto-fill alias only if it's empty or was auto-filled before
        alias: (!currentMeasure.alias || currentMeasure.alias === toSnakeCase(currentMeasure.name)) ? snakeCaseName : currentMeasure.alias,
        // DO NOT update query - it should remain as the original column name
      }
      
      console.log('[MeasuresBuilder] Updated measure after name change:', updated[index])
    }
    // Default update for other fields
    else {
      updated[index] = { ...currentMeasure, [field]: value }
      console.log('[MeasuresBuilder] Updated measure after field change:', updated[index])
    }
    
    updateMeasures(updated)
  }
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

// onTableChange and handleNameChange are now handled in updateMeasure function

const addMeasure = (tableName: string, column: any) => {
  const humanizedName = humanize(column.name)
  const snakeCaseName = toSnakeCase(humanizedName)
  
  const newMeasure: Measure = {
    name: humanizedName,
    alias: snakeCaseName,
    query: column.name,
    table: tableName,
    description: `Measure based on ${tableName}.${column.name}`,
    type: getDefaultType(column.type),
    formatting: [],
    conditional: false,
    conditions: null
  }
  
  updateMeasures([...props.measures, newMeasure])
}

const addCustomMeasure = () => {
  const newMeasure: Measure = {
    name: 'Custom Measure',
    alias: 'custom_measure',
    query: 'custom_measure',
    table: undefined, // User will select table manually
    description: 'Custom measure',
    type: 'custom',
    formatting: [],
    conditional: false,
    conditions: null
  }
  
  updateMeasures([...props.measures, newMeasure])
}

const removeMeasure = (index: number) => {
  const updated = [...props.measures]
  updated.splice(index, 1)
  updateMeasures(updated)
}

const getDefaultType = (columnType: string): string => {
  const type = columnType.toLowerCase()
  
  if (type.includes('int') || type.includes('decimal') || type.includes('float') || type.includes('numeric')) {
    return 'sum'
  } else if (type.includes('date') || type.includes('timestamp')) {
    return 'count'
  } else {
    return 'count'
  }
}

const toggleConditionalMode = (measure: Measure, isConditional: boolean) => {
  const measureIndex = props.measures.findIndex(m => m === measure);
  if (measureIndex === -1) return;
  
  const updated = [...props.measures];
  const currentMeasure = updated[measureIndex];
  if (!currentMeasure) return;
  
  updated[measureIndex] = {
    ...currentMeasure,
    conditional: isConditional,
    conditions: (isConditional && !currentMeasure.conditions) ? {
      when_clauses: [],
      else_return: 0
    } : currentMeasure.conditions
  };
  
  updateMeasures(updated);
}

const updateConditions = (measure: Measure, conditions: Condition | null) => {
  const measureIndex = props.measures.findIndex(m => m === measure);
  if (measureIndex === -1) return;
  
  const updated = [...props.measures];
  const currentMeasure = updated[measureIndex];
  if (!currentMeasure) return;
  
  updated[measureIndex] = {
    ...currentMeasure,
    conditions: conditions
  };
  
  updateMeasures(updated);
}

const getAvailableColumnsMap = (): Record<string, string[]> => {
  const columnsMap: Record<string, string[]> = {}
  
  availableTables.value.forEach((table: any) => {
    columnsMap[table.name] = table.columns.map((col: any) => col.name)
  })
  
  return columnsMap
}
</script>
