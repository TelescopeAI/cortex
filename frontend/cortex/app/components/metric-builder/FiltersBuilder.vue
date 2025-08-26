<template>
  <div class="space-y-4">
    <!-- Header with Add Button -->
    <div class="flex items-center justify-between">
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
    <div v-if="filters.length === 0" class="text-center py-8">
      <div class="text-muted-foreground">
        <Filter class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No filters defined</p>
        <p class="text-xs">Add filters to restrict your data</p>
      </div>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="(filter, index) in filters"
        :key="index"
        class="border rounded-lg p-4 space-y-4"
      >
        <!-- Filter Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <Filter class="h-4 w-4 text-muted-foreground" />
            <span class="text-sm font-medium">Filter {{ index + 1 }}</span>
            <Badge :variant="filter.filter_type === 'where' ? 'default' : 'secondary'">
              {{ filter.filter_type === 'where' ? 'WHERE' : 'HAVING' }}
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
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>
        </div>

        <!-- Filter Configuration -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Name -->
          <div class="space-y-2">
            <Label>Filter Name</Label>
            <Input
              :model-value="filter.name"
              @update:model-value="(value) => updateFilter(index, 'name', value)"
              placeholder="e.g., status_filter"
            />
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <Label>Description</Label>
            <Input
              :model-value="filter.description"
              @update:model-value="(value) => updateFilter(index, 'description', value)"
              placeholder="e.g., Filter for active status"
            />
          </div>

                    <!-- Column/Query -->
          <div class="space-y-2">
            <Label>Column/Expression</Label>
            <div class="flex items-center space-x-2">
              <Switch
                :model-value="filter.use_custom_expression"
                @update:model-value="(value) => updateFilter(index, 'use_custom_expression', value)"
              />
              <Label class="text-sm">Custom Expression</Label>
            </div>
            
            <div v-if="!filter.use_custom_expression">
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="outline" class="w-full justify-start">
                    <Database class="h-4 w-4 mr-2" />
                    {{ filter.query || 'Select column' }}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent class="w-80">
                  <DropdownMenuSub v-for="table in availableTables" :key="table.name">
                    <DropdownMenuSubTrigger>
                      <Database class="h-4 w-4 mr-2" />
                      {{ table.name }}
                    </DropdownMenuSubTrigger>
                    <DropdownMenuSubContent>
                      <DropdownMenuItem
                        v-for="column in table.columns"
                        :key="`${table.name}.${column.name}`"
                        @click="selectColumn(index, table.name, column)"
                        class="cursor-pointer"
                      >
                        <span class="font-mono text-sm">{{ column.name }}</span>
                        <span class="text-xs text-muted-foreground ml-2">({{ column.type }})</span>
                      </DropdownMenuItem>
                    </DropdownMenuSubContent>
                  </DropdownMenuSub>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            
            <div v-else>
              <Textarea
                :model-value="filter.custom_expression"
                @update:model-value="(value) => updateFilter(index, 'custom_expression', value)"
                placeholder="Custom SQL expression (e.g., LENGTH(name) > 10 AND status = 'active')"
                rows="3"
                class="font-mono text-sm"
              />
            </div>
          </div>

          <!-- Filter Type -->
          <div class="space-y-2">
            <Label>Filter Type</Label>
            <Select
              :model-value="filter.filter_type"
              @update:model-value="(value) => updateFilter(index, 'filter_type', value)"
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="where">WHERE (Pre-aggregation)</SelectItem>
                <SelectItem value="having">HAVING (Post-aggregation)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Operator -->
          <div class="space-y-2">
            <Label>Operator</Label>
            <Select
              :model-value="filter.operator"
              @update:model-value="(value) => updateFilter(index, 'operator', value)"
            >
              <SelectTrigger>
                <SelectValue placeholder="Select operator" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="equals">Equals (=)</SelectItem>
                <SelectItem value="not_equals">Not Equals (!=)</SelectItem>
                <SelectItem value="greater_than">Greater Than (>)</SelectItem>
                <SelectItem value="greater_than_equals">Greater Than or Equal (>=)</SelectItem>
                <SelectItem value="less_than">Less Than (<)</SelectItem>
                <SelectItem value="less_than_equals">Less Than or Equal (<=)</SelectItem>
                <SelectItem value="in">In (IN)</SelectItem>
                <SelectItem value="not_in">Not In (NOT IN)</SelectItem>
                <SelectItem value="like">Like (LIKE)</SelectItem>
                <SelectItem value="not_like">Not Like (NOT LIKE)</SelectItem>
                <SelectItem value="is_null">Is Null (IS NULL)</SelectItem>
                <SelectItem value="is_not_null">Is Not Null (IS NOT NULL)</SelectItem>
                <SelectItem value="between">Between (BETWEEN)</SelectItem>
                <SelectItem value="not_between">Not Between (NOT BETWEEN)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Value Type -->
          <div class="space-y-2">
            <Label>Value Type</Label>
            <Select
              :model-value="filter.value_type"
              @update:model-value="(value) => updateFilter(index, 'value_type', value)"
            >
              <SelectTrigger>
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
        </div>

        <!-- Value Configuration -->
        <div v-if="filter.operator && !['is_null', 'is_not_null'].includes(filter.operator)" class="space-y-4">
          <div class="border-t pt-4">
            <h5 class="text-sm font-medium mb-3">Filter Values</h5>
            
            <!-- Single Value -->
            <div v-if="!['in', 'not_in', 'between', 'not_between'].includes(filter.operator)" class="space-y-2">
              <Label>Value</Label>
              <Input
                v-if="filter.value_type === 'string'"
                :model-value="filter.value"
                @update:model-value="(value) => updateFilter(index, 'value', value)"
                placeholder="Enter value"
              />
              <NumberField
                v-else-if="filter.value_type === 'number'"
                :model-value="filter.value"
                @update:model-value="(value) => updateFilter(index, 'value', value)"
              >
                <NumberFieldContent>
                  <NumberFieldDecrement />
                  <NumberFieldInput placeholder="Enter number" />
                  <NumberFieldIncrement />
                </NumberFieldContent>
              </NumberField>
                             <Select
                 v-else-if="filter.value_type === 'boolean'"
                 :model-value="filter.value"
                 @update:model-value="(value) => updateFilter(index, 'value', value)"
               >
                 <SelectTrigger>
                   <SelectValue placeholder="Select boolean value" />
                 </SelectTrigger>
                 <SelectContent>
                   <SelectItem value="true">True</SelectItem>
                   <SelectItem value="false">False</SelectItem>
                 </SelectContent>
               </Select>
              <Input
                v-else
                :model-value="filter.value"
                @update:model-value="(value) => updateFilter(index, 'value', value)"
                :type="filter.value_type === 'date' ? 'date' : 'text'"
                placeholder="Enter value"
              />
            </div>

            <!-- Multiple Values (IN, NOT IN) -->
            <div v-else-if="['in', 'not_in'].includes(filter.operator)" class="space-y-2">
              <Label>Values (comma-separated)</Label>
                             <Textarea
                 :model-value="Array.isArray(filter.values) ? filter.values.join(', ') : ''"
                 @update:model-value="(value) => updateFilter(index, 'values', String(value).split(',').map((v: string) => v.trim()))"
                 placeholder="value1, value2, value3"
                 rows="3"
               />
            </div>

            <!-- Range Values (BETWEEN, NOT BETWEEN) -->
            <div v-else-if="['between', 'not_between'].includes(filter.operator)" class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Minimum Value</Label>
                <Input
                  :model-value="filter.min_value"
                  @update:model-value="(value) => updateFilter(index, 'min_value', value)"
                  placeholder="Min value"
                />
              </div>
              <div class="space-y-2">
                <Label>Maximum Value</Label>
                <Input
                  :model-value="filter.max_value"
                  @update:model-value="(value) => updateFilter(index, 'max_value', value)"
                  placeholder="Max value"
                />
              </div>
            </div>
          </div>
        </div>



        <!-- $CORTEX_ Parameter Guidance -->
        <div class="space-y-2">
          <div class="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-center space-x-2 mb-2">
              <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span class="text-sm font-medium text-blue-900">$CORTEX_ Parameters</span>
            </div>
            <p class="text-xs text-blue-700">
              Use $CORTEX_ prefix in filter values to auto-substitute with consumer properties when context_id is provided.
              <br />Example: $CORTEX_client_id, $CORTEX_currency
            </p>
          </div>
        </div>

        <!-- Output Formatting -->
        <OutputFormatEditor
          v-model="filter.formatting"
          object-type="filter"
          @update:model-value="updateFilter(index, 'formatting', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { Switch } from '~/components/ui/switch'
import { Badge } from '~/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Plus, Filter, Trash2, Database } from 'lucide-vue-next'
import OutputFormatEditor from './OutputFormatEditor.vue'

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
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:filters': [value: Filter[]]
}>()

const filters = ref<Filter[]>(props.filters || [])

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

// Watch for prop changes
watch(() => props.filters, (newFilters) => {
  if (newFilters && JSON.stringify(newFilters) !== JSON.stringify(filters.value)) {
    filters.value = [...newFilters]
  }
}, { deep: true })

// Watch for local changes and emit
watch(filters, (newFilters) => {
  emit('update:filters', newFilters)
}, { deep: true })

const addFilter = () => {
  const newFilter: Filter = {
    name: `filter_${filters.value.length + 1}`,
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
  filters.value.push(newFilter)
}

const removeFilter = (index: number) => {
  filters.value.splice(index, 1)
}

const updateFilter = (index: number, field: keyof Filter, value: any) => {
  if (filters.value[index]) {
    filters.value[index] = { ...filters.value[index], [field]: value }
  }
}

const selectColumn = (index: number, tableName: string, column: any) => {
  if (filters.value[index]) {
    filters.value[index] = {
      ...filters.value[index],
      query: column.name,
      table: tableName,
      use_custom_expression: false
    }
    emit('update:filters', filters.value)
  }
}
</script> 