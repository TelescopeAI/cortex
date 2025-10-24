<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

interface Measure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
}

interface Props {
  measure: Measure
  availableTables: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:measure': [value: Measure]
}>()

const updateMeasure = (updates: Partial<Measure>) => {
  emit('update:measure', { ...props.measure, ...updates })
}

const getColumnsForTable = (tableName?: string) => {
  if (!tableName) return []
  const table = props.availableTables.find((t: any) => t.name === tableName)
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

const onTableChange = (tableName: string) => {
  // Reset query if the selected column doesn't exist in new table
  if (props.measure.query) {
    const columns = getColumnsForTable(tableName)
    const columnExists = columns.some((col: any) => col.name === props.measure.query)
    if (!columnExists) {
      updateMeasure({ table: tableName, query: undefined })
      return
    }
  }
  updateMeasure({ table: tableName })
}
</script>

<template>
  <div class="space-y-3">
    <!-- Row 1: Calculate the [type] of [column] -->
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-sm text-muted-foreground">Calculate the</span>
      <Select :model-value="measure.type" @update:model-value="(val) => updateMeasure({ type: val })">
        <SelectTrigger class="w-auto min-w-[130px] h-9">
          <SelectValue placeholder="Select type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="count">count</SelectItem>
          <SelectItem value="sum">sum</SelectItem>
          <SelectItem value="avg">average</SelectItem>
          <SelectItem value="min">minimum</SelectItem>
          <SelectItem value="max">maximum</SelectItem>
          <SelectItem value="distinct_count">distinct count</SelectItem>
          <SelectItem value="custom">custom</SelectItem>
        </SelectContent>
      </Select>
      <span class="text-sm text-muted-foreground">of</span>
      
      <!-- Column Selection (dropdown based on selected table) -->
      <Select 
        :model-value="measure.query" 
        @update:model-value="(val) => updateMeasure({ query: val })"
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
      <Select :model-value="measure.table" @update:model-value="onTableChange">
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
  </div>
</template>

