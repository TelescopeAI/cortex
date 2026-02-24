<template>
  <div class="space-y-4">
    <!-- Header with Add Button -->
    <div v-if="showHeader !== false" class="flex items-center justify-between">
      <div>
        <h4 class="text-sm font-medium">Filters</h4>
        <p class="text-xs text-muted-foreground">
          Define filters to apply to your metric data
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        @click="addFilter"
      >
        <Plus class="h-4 w-4 mr-2" />
        Add Filter
      </Button>
    </div>

    <!-- Filters List -->
    <div v-if="props.filters.length === 0 && showEmptyState !== false" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Filter class="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">No filters defined</p>
      <p class="text-xs text-muted-foreground">Add filters to restrict your data</p>
    </div>

    <div v-else class="space-y-4">
      <Card
        v-for="(filter, index) in props.filters"
        :key="index"
        class="p-5 hover:shadow-md transition-shadow"
      >
        <div class="space-y-5">
          <!-- Filter Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div class="p-1.5 rounded-md bg-orange-50 dark:bg-orange-950">
                <Filter class="h-4 w-4 text-orange-600 dark:text-orange-400" />
              </div>
              <span class="font-medium text-base">{{ filter.name || `Filter ${index + 1}` }}</span>
              <Badge 
                :variant="filter.is_active ? 'default' : 'secondary'"
                class="ml-2"
              >
                {{ filter.is_active ? 'Active' : 'Inactive' }}
              </Badge>
            </div>
            <div class="flex items-center space-x-2">
              <Switch
                :model-value="filter.is_active"
                @update:model-value="(value) => updateFilter(index, 'is_active', value)"
              />
              <Button
                variant="ghost"
                size="sm"
                @click="removeFilter(index)"
                class="hover:bg-red-50 hover:text-red-600"
              >
                <X class="h-4 w-4" />
              </Button>
            </div>
          </div>

          <!-- Sentence-Completion Interface -->
          <div class="space-y-3">
            <!-- Row 1: Filter rows from table [table] where [column] [operator] [value] -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm text-muted-foreground">Pick rows from table</span>
              
              <!-- Table Selection -->
              <Select
                :model-value="filter.table"
                @update:model-value="(value) => value && onTableChange(index, String(value))"
              >
                <SelectTrigger class="w-auto min-w-[180px] h-9">
                  <SelectValue placeholder="Select table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">
                    {{ table.name }}
                  </SelectItem>
                </SelectContent>
              </Select>

              <span class="text-sm text-muted-foreground">where</span>

              <!-- Column Selection -->
              <Select
                :model-value="filter.query"
                @update:model-value="(value) => updateFilter(index, 'query', value)"
                :disabled="!filter.table"
              >
                <SelectTrigger class="w-auto min-w-[180px] h-9 justify-between">
                  <SelectValue placeholder="Select column" as-child>
                    <div class="flex items-center justify-between w-full gap-3">
                      <span>{{ filter.query || 'Select column' }}</span>
                      <Badge 
                        v-if="filter.query && getSelectedColumnType(filter.table, filter.query)"
                        :class="getColumnTypeBadgeClass(getSelectedColumnType(filter.table, filter.query) || '')"
                      >
                        {{ getSelectedColumnType(filter.table, filter.query) }}
                      </Badge>
                    </div>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="column in getColumnsForTable(filter.table)"
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

              <!-- Operator Selection -->
              <Select
                :model-value="filter.operator"
                @update:model-value="(value) => updateFilter(index, 'operator', value)"
              >
                <SelectTrigger class="w-auto min-w-[120px] h-9">
                  <SelectValue placeholder="operator" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="equals">equals</SelectItem>
                  <SelectItem value="not_equals">not equals</SelectItem>
                  <SelectItem value="greater_than">greater than</SelectItem>
                  <SelectItem value="greater_than_equals">≥</SelectItem>
                  <SelectItem value="less_than">less than</SelectItem>
                  <SelectItem value="less_than_equals">≤</SelectItem>
                  <SelectItem value="in">in</SelectItem>
                  <SelectItem value="not_in">not in</SelectItem>
                  <SelectItem value="like">like</SelectItem>
                  <SelectItem value="not_like">not like</SelectItem>
                  <SelectItem value="is_null">is null</SelectItem>
                  <SelectItem value="is_not_null">is not null</SelectItem>
                  <SelectItem value="between">between</SelectItem>
                  <SelectItem value="not_between">not between</SelectItem>
                </SelectContent>
              </Select>

              <!-- Value Input (conditional based on operator) -->
              <template v-if="filter.operator && !['is_null', 'is_not_null'].includes(filter.operator)">
                <!-- Single Value -->
                <Input
                  v-if="!['in', 'not_in', 'between', 'not_between'].includes(filter.operator)"
                  :model-value="filter.value"
                  @update:model-value="(value) => updateFilter(index, 'value', value)"
                  placeholder="value"
                  class="w-auto min-w-[150px] flex-1 h-9"
                />
                
                <!-- Multiple Values (IN, NOT IN) -->
                <Input
                  v-else-if="['in', 'not_in'].includes(filter.operator)"
                  :model-value="Array.isArray(filter.values) ? filter.values.join(', ') : ''"
                  @update:model-value="(value) => updateFilter(index, 'values', String(value).split(',').map((v: string) => v.trim()))"
                  placeholder="val1, val2, val3"
                  class="w-auto min-w-[200px] flex-1 h-9"
                />

                <!-- Range Values (BETWEEN) -->
                <template v-else-if="['between', 'not_between'].includes(filter.operator)">
                  <Input
                    :model-value="filter.min_value"
                    @update:model-value="(value) => updateFilter(index, 'min_value', value)"
                    placeholder="min"
                    class="w-[100px] h-9"
                  />
                  <span class="text-sm text-muted-foreground">and</span>
                  <Input
                    :model-value="filter.max_value"
                    @update:model-value="(value) => updateFilter(index, 'max_value', value)"
                    placeholder="max"
                    class="w-[100px] h-9"
                  />
                </template>
              </template>
            </div>

            <!-- Row 2: Name it as [name] -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-muted-foreground">Name it as</span>
              <Input
                :model-value="filter.name"
                @update:model-value="(value) => updateFilter(index, 'name', value)"
                placeholder="Filter name"
                class="flex-1 h-9"
                :disabled="readOnlyName"
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
              <!-- Filter Type -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Filter Type</Label>
                <Select
                  :model-value="filter.filter_type"
                  @update:model-value="(value) => updateFilter(index, 'filter_type', value)"
                >
                  <SelectTrigger class="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="where">WHERE (Pre-aggregation)</SelectItem>
                    <SelectItem value="having">HAVING (Post-aggregation)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Value Type -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Value Type</Label>
                <Select
                  :model-value="filter.value_type"
                  @update:model-value="(value) => updateFilter(index, 'value_type', value)"
                >
                  <SelectTrigger class="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="string">String</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="timestamp">Timestamp</SelectItem>
                    <SelectItem value="array">Array</SelectItem>
                    <SelectItem value="null">Null</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Custom Expression -->
              <div class="space-y-1.5">
                <div class="flex items-center space-x-2 mb-2">
                  <Switch
                    :model-value="filter.use_custom_expression"
                    @update:model-value="(value) => updateFilter(index, 'use_custom_expression', value)"
                  />
                  <Label class="text-xs font-medium text-muted-foreground">Use Custom SQL Expression</Label>
                </div>
                
                <Textarea
                  v-if="filter.use_custom_expression"
                  :model-value="filter.custom_expression"
                  @update:model-value="(value) => updateFilter(index, 'custom_expression', value)"
                  placeholder="Custom SQL expression (e.g., LENGTH(name) > 10 AND status = 'active')"
                  rows="3"
                  class="font-mono text-xs resize-none"
                />
              </div>

              <!-- Description -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                <Textarea
                  :model-value="filter.description"
                  @update:model-value="(value) => updateFilter(index, 'description', value)"
                  placeholder="Describe what this filter does..."
                  rows="2"
                  class="resize-none"
                />
              </div>

              <!-- $CORTEX_ Parameter Info -->
              <div class="p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div class="flex items-start gap-2">
                  <div class="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5"></div>
                  <div class="flex-1">
                    <p class="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">$CORTEX_ Parameters</p>
                    <p class="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">
                      Use $CORTEX_ prefix in filter values to auto-substitute with consumer properties.
                      Example: $CORTEX_client_id, $CORTEX_currency
                    </p>
                  </div>
                </div>
              </div>

              <!-- Output Formatting -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Output Formatting</Label>
                <OutputFormatEditor
                  v-model="filter.formatting"
                  object-type="filter"
                  @update:model-value="updateFilter(index, 'formatting', $event)"
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
import { Switch } from '~/components/ui/switch'
import { Badge as StatusBadge } from '~/components/ui/badge'
import { Plus, Filter, X, Settings, ChevronDown } from 'lucide-vue-next'
import OutputFormatEditor from './OutputFormatEditor.vue'
import { humanize } from '~/utils/stringCase'

interface Filter {
  name: string
  description?: string
  query: string
  table?: string
  operator?: string
  value?: any
  value_type: string
  filter_type: 'where' | 'having'
  is_active: boolean
  custom_expression?: string
  use_custom_expression?: boolean
  values?: any[]
  min_value?: any
  max_value?: any
  formatting?: any[]
}

interface Props {
  filters?: Filter[]
  availableColumns?: Array<{ name: string; type: string }>
  tableSchema?: any
  showHeader?: boolean
  showEmptyState?: boolean
  readOnlyName?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  filters: () => []
})

const emit = defineEmits<{
  'update:filters': [value: Filter[]]
}>()

const showAdvanced = ref<Record<number, boolean>>({})

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const updateFilters = (newFilters: Filter[]) => {
  emit('update:filters', newFilters)
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

const onTableChange = (index: number, tableName: string) => {
  const updated = [...props.filters]
  if (updated[index]) {
    // Reset query if the selected column doesn't exist in new table
    if (updated[index].query) {
      const columns = getColumnsForTable(tableName)
      const columnExists = columns.some((col: any) => col.name === updated[index]?.query)
      if (!columnExists) {
        updated[index].query = ''
      }
    }
    updated[index].table = tableName
    updateFilters(updated)
  }
}

const addFilter = () => {
  const filterNumber = props.filters.length + 1
  const newFilter: Filter = {
    name: `Filter ${filterNumber}`,
    description: '',
    query: '',
    operator: 'equals',
    value: '',
    value_type: 'string',
    filter_type: 'where',
    is_active: true,
    custom_expression: '',
    use_custom_expression: false,
    formatting: []
  }
  updateFilters([...props.filters, newFilter])
}

const removeFilter = (index: number) => {
  const updated = [...props.filters]
  updated.splice(index, 1)
  updateFilters(updated)
}

const updateFilter = (index: number, field: keyof Filter, value: any) => {
  const updated = [...props.filters]
  if (updated[index]) {
    updated[index] = { ...updated[index], [field]: value }
    updateFilters(updated)
  }
}
</script>
