<template>
  <div class="space-y-4">
    <!-- Data Source Selection -->
    <div class="space-y-2">
      <Label for="data-source">Data Source</Label>
      <Select :model-value="dataSourceId" @update:model-value="(value) => handleDataSourceChange(value as string)">
        <SelectTrigger>
          <SelectValue placeholder="Select a data source" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem
            v-for="source in availableDataSources"
            :key="source.id"
            :value="source.id"
          >
            {{ source.name }} ({{ source.source_type }})
          </SelectItem>
        </SelectContent>
      </Select>
      <p class="text-xs text-muted-foreground">
        Choose the data source for your metric.
      </p>
    </div>

    <!-- Table vs Custom Query Toggle -->
    <div class="space-y-2">
      <Label>Query Source</Label>
      <div class="flex items-center space-x-3">
        <Switch
          :model-value="useCustomQuery"
          @update:model-value="handleQuerySourceToggle"
        />
        <span class="text-sm text-muted-foreground">
          {{ useCustomQuery ? 'Custom Query' : 'Table Selection' }} ({{ useCustomQuery ? 'Custom' : 'Default' }})
        </span>
      </div>
      <p class="text-xs text-muted-foreground">
        Choose between table-based generation or custom SQL query.
      </p>
    </div>

    <!-- Table Selection (shown when toggle is off) -->
    <div v-if="!useCustomQuery" class="space-y-2">
      <Label for="table-name">Source Table</Label>
                  <Select :model-value="tableName" @update:model-value="(value) => $emit('update:tableName', value as string)">
              <SelectTrigger>
                <SelectValue placeholder="Select a table" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="table in debugAvailableTables"
                  :key="table.name"
                  :value="table.name"
                >
                  {{ table.name }}
                </SelectItem>
              </SelectContent>
            </Select>
      <p class="text-xs text-muted-foreground">
        Choose the primary table for your metric data.
      </p>
    </div>

    <!-- Custom Query (shown when toggle is on) -->
    <div v-if="useCustomQuery" class="space-y-2">
      <Label for="custom-query">Custom SQL Query</Label>
      <Textarea
        id="custom-query"
        :model-value="query"
        @update:model-value="(value) => $emit('update:query', value as string)"
        placeholder="SELECT * FROM your_table WHERE condition..."
        rows="4"
        class="font-mono text-sm"
      />
      <p class="text-xs text-muted-foreground">
        Provide a custom SQL query to override table-based generation.
      </p>
    </div>

    <!-- Default Limit -->
    <div class="space-y-2">
      <Label>Limit Results</Label>
      <div class="flex items-center space-x-3">
        <Switch
          :model-value="limitEnabled"
          @update:model-value="handleLimitToggle"
        />
        <div v-if="limitEnabled" class="flex items-center space-x-2">
          <NumberField 
            :model-value="props.limit"
            :min="1"
            @update:model-value="(value) => emit('update:limit', value)"
          >
            <NumberFieldContent>
              <NumberFieldDecrement />
              <NumberFieldInput placeholder="100" class="w-fit" />
              <NumberFieldIncrement />
            </NumberFieldContent>
          </NumberField>
          <span class="text-sm text-muted-foreground">results</span>
        </div>
      </div>
      <p class="text-xs text-muted-foreground">
        Set limits for query results. Can be overridden at execution time.
      </p>
    </div>

    <!-- Info Alert -->
    <div class="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div>
          <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200">
            Query Source Selection
          </h4>
          <p class="mt-1 text-sm text-blue-700 dark:text-blue-300">
            Use the toggle to switch between table-based generation (default) and custom SQL queries. 
            Table selection enables column discovery for measures and dimensions, while custom queries provide full SQL control.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { Switch } from '~/components/ui/switch'
import { useDataSources } from '~/composables/useDataSources'

interface Props {
  tableName?: string
  query?: string
  dataSourceId?: string
  limit?: number
  availableTables?: Array<{ name: string; columns: any[] }>
  tableSchema?: any
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:tableName': [value: string]
  'update:query': [value: string]
  'update:dataSourceId': [value: string]
  'update:limit': [value: number | undefined]
}>()

// Debug availableTables
const debugAvailableTables = computed(() => {
  console.log('BasicInfoBuilder - availableTables prop:', props.availableTables)
  return props.availableTables || []
})

// Use data sources from tableSchema if available, otherwise fallback to useDataSources
const { dataSources } = useDataSources()
const availableDataSources = computed(() => {
  console.log('BasicInfoBuilder - tableSchema prop:', props.tableSchema)
  // If we have tableSchema, we can derive the data source from it
  // For now, fallback to the composable
  return dataSources.value || []
})

// Computed property for limit toggle
const limitEnabled = computed(() => {
  return props.limit !== undefined && props.limit !== null
})

// Computed property for query source toggle
const useCustomQuery = computed(() => {
  return !!(props.query && props.query.trim())
})

// Handle limit toggle
const handleLimitToggle = (enabled: boolean) => {
  if (enabled) {
    emit('update:limit', 100) // Default value when enabling
  } else {
    emit('update:limit', undefined) // Clear limit when disabling
  }
}

// Handle query source toggle
const handleQuerySourceToggle = (enabled: boolean) => {
  if (enabled) {
    // Switch to custom query - clear table name and set default query
    emit('update:tableName', '')
    emit('update:query', 'SELECT * FROM your_table WHERE condition...')
  } else {
    // Switch to table selection - clear custom query
    emit('update:query', '')
  }
}

// Handle data source change
const handleDataSourceChange = (value: string) => {
  console.log('BasicInfoBuilder - Data source changed to:', value)
  emit('update:dataSourceId', value)
}
</script> 