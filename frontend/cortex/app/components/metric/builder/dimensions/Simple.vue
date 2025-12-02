<script setup lang="ts">
import { computed } from 'vue'
import { Plus, X } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Card } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

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
}

interface Props {
  dimension: Dimension
  availableTables: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:dimension': [value: Dimension]
}>()

const updateDimension = (updates: Partial<Dimension>) => {
  emit('update:dimension', { ...props.dimension, ...updates })
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
  
  if (typeUpper.includes('INT') || typeUpper.includes('DECIMAL') || 
      typeUpper.includes('NUMERIC') || typeUpper.includes('FLOAT') || 
      typeUpper.includes('DOUBLE') || typeUpper.includes('REAL') ||
      typeUpper.includes('MONEY')) {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 text-[10px] px-1.5 py-0.5'
  }
  
  if (typeUpper.includes('CHAR') || typeUpper.includes('TEXT') || 
      typeUpper.includes('VARCHAR') || typeUpper.includes('STRING') ||
      typeUpper.includes('CLOB')) {
    return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300 text-[10px] px-1.5 py-0.5'
  }
  
  if (typeUpper.includes('DATE') || typeUpper.includes('TIME') || 
      typeUpper.includes('TIMESTAMP')) {
    return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-[10px] px-1.5 py-0.5'
  }
  
  if (typeUpper.includes('BOOL') || typeUpper.includes('BIT')) {
    return 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300 text-[10px] px-1.5 py-0.5'
  }
  
  return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[10px] px-1.5 py-0.5'
}

const onTableChange = (tableName: string) => {
  if (props.dimension.query) {
    const columns = getColumnsForTable(tableName)
    const columnExists = columns.some((col: any) => col.name === props.dimension.query)
    if (!columnExists) {
      updateDimension({ table: tableName, query: '' })
      return
    }
  }
  updateDimension({ table: tableName })
}

const addCombineColumn = () => {
  const combine = props.dimension.combine || []
  updateDimension({
    combine: [...combine, {
      query: '',
      table: props.dimension.table,
      delimiter: ' '
    }]
  })
}

const removeCombineColumn = (combineIndex: number) => {
  const combine = [...(props.dimension.combine || [])]
  combine.splice(combineIndex, 1)
  updateDimension({ combine })
}

const updateCombineColumn = (combineIndex: number, updates: Partial<CombineColumnSpec>) => {
  const combine = [...(props.dimension.combine || [])]
  combine[combineIndex] = { ...combine[combineIndex], ...updates }
  updateDimension({ combine })
}

const onCombineTableChange = (combineIndex: number, tableName: string) => {
  const combine = [...(props.dimension.combine || [])]
  const combineSpec = combine[combineIndex]
  
  if (combineSpec.query) {
    const columns = getColumnsForTable(tableName)
    const columnExists = columns.some((col: any) => col.name === combineSpec.query)
    if (!columnExists) {
      combine[combineIndex] = { ...combineSpec, table: tableName, query: '' }
      updateDimension({ combine })
      return
    }
  }
  
  combine[combineIndex] = { ...combineSpec, table: tableName }
  updateDimension({ combine })
}
</script>

<template>
  <div class="space-y-3">
    <!-- Row 1: Select [column] from the table [table] -->
    <div class="flex items-center gap-2 flex-wrap">
      <span class="text-sm text-muted-foreground">Select</span>
      
      <Select 
        :model-value="dimension.query" 
        @update:model-value="(val) => updateDimension({ query: val })"
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
      
      <Select :model-value="dimension.table" @update:model-value="onTableChange">
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

    <!-- Combine Columns -->
    <div v-if="dimension.table" class="space-y-2 pt-4 border-t">
      <div class="flex items-center justify-between">
        <Label class="text-xs font-medium text-muted-foreground">Combine Columns</Label>
        <Button
          variant="outline"
          size="sm"
          @click="addCombineColumn"
          class="h-7 text-xs"
        >
          <Plus class="h-3 w-3 mr-1" />
          Add Column
        </Button>
      </div>
      <p class="text-xs text-muted-foreground">
        Concatenate additional columns to this dimension (e.g., first_name + last_name)
      </p>
      
      <div v-if="dimension.combine && dimension.combine.length > 0" class="space-y-2 mt-2">
        <Card 
          v-for="(combineSpec, combineIndex) in dimension.combine"
          :key="combineIndex"
          class="p-3 bg-muted/30"
        >
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <Select 
                :model-value="combineSpec.table" 
                @update:model-value="(val) => onCombineTableChange(combineIndex, val)"
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
                @update:model-value="(val) => updateCombineColumn(combineIndex, { query: val })"
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
                @click="removeCombineColumn(combineIndex)"
                class="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
              >
                <X class="h-3 w-3" />
              </Button>
            </div>

            <div class="flex items-center gap-2">
              <Label class="text-xs text-muted-foreground whitespace-nowrap">Delimiter:</Label>
              <Input
                :model-value="combineSpec.delimiter"
                @update:model-value="(val) => updateCombineColumn(combineIndex, { delimiter: val })"
                placeholder="Space"
                class="h-7 text-xs flex-1"
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
  </div>
</template>

