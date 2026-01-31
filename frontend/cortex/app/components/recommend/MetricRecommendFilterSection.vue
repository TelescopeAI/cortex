<script setup lang="ts">
import { Separator } from '~/components/ui/separator'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import TableColumnFilter from './TableColumnFilter.vue'

interface Column {
  name: string
  type: string
  nullable?: boolean
  primary_key?: boolean
  foreign_key?: boolean
}

interface Table {
  name: string
  columns: Column[]
}

interface Schema {
  tables: Table[]
}

interface TableSelectionState {
  excluded: boolean
  selectedColumns: string[]
}

interface Props {
  schema: Schema | null
  isLoadingSchema: boolean
  tableSelections: Record<string, TableSelectionState>
  metricTypes: string[]
  timeGrains: string[]
  timeWindowDays: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:tableSelections': [value: Record<string, TableSelectionState>]
  'update:metricTypes': [value: string[]]
  'update:timeGrains': [value: string[]]
  'update:timeWindowDays': [value: number]
}>()

const localMetricTypes = computed({
  get: () => props.metricTypes,
  set: (value: string[]) => emit('update:metricTypes', value)
})

const localTimeGrains = computed({
  get: () => props.timeGrains,
  set: (value: string[]) => emit('update:timeGrains', value)
})

const localTimeWindowDays = computed({
  get: () => props.timeWindowDays,
  set: (value: number) => emit('update:timeWindowDays', value)
})

function updateTableSelection(tableName: string, value: TableSelectionState) {
  emit('update:tableSelections', {
    ...props.tableSelections,
    [tableName]: value
  })
}

function getTableSelection(tableName: string): TableSelectionState {
  if (props.tableSelections[tableName]) {
    return props.tableSelections[tableName]
  }

  // Default: include with all columns
  const table = props.schema?.tables.find(t => t.name === tableName)
  const allColumnNames = table?.columns.map(col => col.name) || []

  return {
    excluded: false,
    selectedColumns: allColumnNames
  }
}

function excludeAllTables() {
  if (!props.schema) return

  const newSelections: Record<string, TableSelectionState> = {}
  props.schema.tables.forEach(table => {
    newSelections[table.name] = {
      excluded: true,
      selectedColumns: []
    }
  })
  emit('update:tableSelections', newSelections)
}

function includeAllTables() {
  if (!props.schema) return

  const newSelections: Record<string, TableSelectionState> = {}
  props.schema.tables.forEach(table => {
    const allColumnNames = table.columns.map(col => col.name)
    newSelections[table.name] = {
      excluded: false,
      selectedColumns: allColumnNames  // All column names
    }
  })
  emit('update:tableSelections', newSelections)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Tables & Columns Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">Tables</h3>
        <div v-if="schema" class="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="includeAllTables"
            class="h-8 text-xs"
          >
            Include All
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="excludeAllTables"
            class="h-8 text-xs"
          >
            Exclude All
          </Button>
        </div>
      </div>

      <div v-if="isLoadingSchema" class="text-sm text-muted-foreground">
        Loading schema...
      </div>

      <div v-else-if="!schema" class="text-sm text-muted-foreground">
        Select a data source to configure filters
      </div>

      <div v-else class="space-y-3">
        <TableColumnFilter
          v-for="table in schema.tables"
          :key="table.name"
          :table="table"
          :model-value="getTableSelection(table.name)"
          @update:model-value="updateTableSelection(table.name, $event)"
        />
      </div>
    </div>

    <div class="flex space-2 items-center justify-between">
      <!-- Metric Types -->
      <div class="flex space-x-2">
        <Label>Metric Types</Label>
        <Select v-model="localMetricTypes" multiple>
          <SelectTrigger>
            <SelectValue placeholder="Select metric types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="count">Count</SelectItem>
            <SelectItem value="sum">Sum</SelectItem>
            <SelectItem value="avg">Average</SelectItem>
            <SelectItem value="min">Min</SelectItem>
            <SelectItem value="max">Max</SelectItem>
            <SelectItem value="count_distinct">Count Distinct</SelectItem>
            <SelectItem value="boolean">Boolean</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <!-- Time Grains -->
      <div class="flex space-x-2">
        <Label>Time Grains</Label>
        <Select v-model="localTimeGrains" multiple>
          <SelectTrigger>
            <SelectValue placeholder="Select time grains" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="day">Daily</SelectItem>
            <SelectItem value="week">Weekly</SelectItem>
            <SelectItem value="month">Monthly</SelectItem>
            <SelectItem value="quarter">Quarterly</SelectItem>
            <SelectItem value="year">Yearly</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <!-- Time Windows -->
      <div class="flex space-x-2">
        <Label>Frequency (days)</Label>
        <NumberField v-model="localTimeWindowDays">
          <NumberFieldContent>
            <NumberFieldDecrement />
            <NumberFieldInput />
            <NumberFieldIncrement />
          </NumberFieldContent>
        </NumberField>
      </div>
    </div>
  </div>
</template>