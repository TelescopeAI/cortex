<template>
  <div class="space-y-4">
    <!-- Essential Fields (3 minimum requirements) -->
    <div class="space-y-4 p-4 rounded-lg border border-blue-200 shadow dark:shadow-red-300">
      
      <!-- 1. Name -->
      <div class="space-y-2">
        <Label for="metric-name">Name *</Label>
        <Input
          id="metric-name"
          :model-value="name"
          @update:model-value="(value) => $emit('update:name', value as string)"
          placeholder="Enter metric name"
        />
        <p class="text-xs text-muted-foreground">
          A unique name for your metric.
        </p>
      </div>

      <!-- 2. Data Source -->
      <div class="space-y-2">
        <Label for="data-source">Data Source *</Label>
        <Select :model-value="selectedDataSourceId" @update:model-value="(value) => handleDataSourceChange(value as string)">
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

      <!-- 3. Source Table -->
      <div class="space-y-2">
        <Label for="table-name">Source Table *</Label>
        <Select :model-value="selectedTableName" @update:model-value="(value) => handleTableNameChange(value as string)">
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
    </div>

    <!-- Advanced Configuration (Collapsible) -->
    <Collapsible v-model:open="advancedOpen" class="border rounded-lg">
      <div class="flex items-center justify-between p-4">
        <h3 class="font-semibold text-sm text-gray-500 dark:text-gray-200">Advanced</h3>
        <CollapsibleTrigger as-child>
          <Button variant="ghost" size="sm" class="w-9 p-0">
            <ChevronDown :class="['h-4 w-4 transition-transform', advancedOpen && 'rotate-180']" />
            <span class="sr-only">Toggle advanced</span>
          </Button>
        </CollapsibleTrigger>
      </div>

      <CollapsibleContent class="space-y-4 p-4 border-t">
        <!-- Display Settings -->
        <div class="space-y-4">
          <h4 class="text-sm font-medium text-muted-foreground">Display</h4>
          
          <div class="space-y-2">
            <Label for="metric-alias">Alias</Label>
            <Input
              id="metric-alias"
              :model-value="alias"
              @update:model-value="(value) => handleAliasChange(value as string)"
              placeholder="Auto-generated from name"
            />
            <p class="text-xs text-muted-foreground">
              {{ aliasError || 'Used for programmatic references. Auto-generated from name.' }}
            </p>
          </div>

          <div class="space-y-2">
            <Label for="metric-title">Title</Label>
            <Input
              id="metric-title"
              :model-value="title"
              @update:model-value="(value) => $emit('update:title', value as string)"
              placeholder="Enter display title"
            />
            <p class="text-xs text-muted-foreground">
              Display title for the metric (optional).
            </p>
          </div>

          <div class="space-y-2">
            <Label for="metric-description">Description</Label>
            <Textarea
              id="metric-description"
              :model-value="description"
              @update:model-value="(value) => $emit('update:description', value as string)"
              placeholder="Enter metric description"
              rows="3"
            />
            <p class="text-xs text-muted-foreground">
              Describe what this metric measures and how it's used.
            </p>
          </div>
        </div>

        <!-- Query Settings -->
        <div class="space-y-4 pt-4 border-t">
          <h4 class="text-sm font-medium text-muted-foreground">Query Settings</h4>
          
          <div class="space-y-2">
            <Label>Query Source</Label>
            <div class="flex items-center space-x-3">
              <Switch
                :model-value="useCustomQuery"
                @update:model-value="handleQuerySourceToggle"
              />
              <span class="text-sm text-muted-foreground">
                {{ useCustomQuery ? 'Custom Query' : 'Table Selection' }}
              </span>
            </div>
            <p class="text-xs text-muted-foreground">
              Choose between table-based generation or custom SQL query.
            </p>
          </div>

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
          </div>

          <div class="space-y-2">
            <Label>Group Results</Label>
            <div class="flex items-center space-x-3">
              <Switch
                :model-value="groupedEnabled"
                @update:model-value="handleGroupedToggle"
              />
              <span class="text-sm text-muted-foreground">
                {{ groupedEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </div>
            <p class="text-xs text-muted-foreground">
              When enabled, applies GROUP BY clause for dimensions.
            </p>
          </div>

          <div class="space-y-2">
            <Label>Order Results</Label>
            <div class="flex items-center space-x-3">
              <Switch
                :model-value="orderedEnabled"
                @update:model-value="handleOrderedToggle"
              />
              <span class="text-sm text-muted-foreground">
                {{ orderedEnabled ? 'Enabled' : 'Disabled' }}
              </span>
            </div>
            <p class="text-xs text-muted-foreground">
              When enabled, applies ORDER BY clause to sort results.
            </p>
          </div>
        </div>

        <!-- Performance & Caching -->
        <div class="space-y-4 pt-4 border-t">
          <h4 class="text-sm font-medium text-muted-foreground">Performance & Caching</h4>
          
          <div class="space-y-3">
            <Label>Refresh Policy (Pre-aggregations)</Label>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div class="space-y-1">
                <Label for="rk-type" class="text-xs">Type</Label>
                <Select :model-value="refreshType" @update:model-value="(v) => updateRefreshType(v as string)">
                  <SelectTrigger id="rk-type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="every">Every</SelectItem>
                    <SelectItem value="sql">SQL</SelectItem>
                    <SelectItem value="max">Max</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1" v-if="refreshType === 'every'">
                <Label for="rk-every" class="text-xs">Every</Label>
                <Input id="rk-every" :model-value="props.refresh?.every || ''" placeholder="e.g. 1 hour" @update:model-value="(v) => emitRefresh({ every: v as string })" />
              </div>
              <div class="space-y-1 md:col-span-2" v-if="refreshType === 'sql'">
                <Label for="rk-sql" class="text-xs">SQL</Label>
                <Textarea id="rk-sql" rows="2" :model-value="props.refresh?.sql || ''" placeholder="SELECT NOW()" @update:model-value="(v) => emitRefresh({ sql: v as string })" />
              </div>
              <div class="space-y-1" v-if="refreshType === 'max'">
                <Label for="rk-max" class="text-xs">Max Column</Label>
                <Input id="rk-max" :model-value="props.refresh?.max || ''" placeholder="table.column" @update:model-value="(v) => emitRefresh({ max: v as string })" />
              </div>
            </div>
          </div>

          <div class="space-y-2">
            <Label>Result Cache (Default)</Label>
            <div class="flex items-center space-x-3">
              <Switch :model-value="cacheEnabled" @update:model-value="handleCacheToggle" />
              <Label>{{ cacheEnabled ? 'Enabled' : 'Disabled' }}</Label>
            </div>
            <div v-if="cacheEnabled" class="mt-2 space-y-2">
              <Label for="cache-ttl" class="text-xs">TTL (seconds)</Label>
              <NumberField :model-value="props.cache?.ttl" :min="1" @update:model-value="(v) => emitCache({ ttl: v as number })">
                <NumberFieldContent>
                  <NumberFieldDecrement />
                  <NumberFieldInput id="cache-ttl" placeholder="300" class="w-full" />
                  <NumberFieldIncrement />
                </NumberFieldContent>
              </NumberField>
              <p class="text-xs text-muted-foreground">How long results stay cached by default.</p>
            </div>
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { Switch } from '~/components/ui/switch'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '~/components/ui/collapsible'
import { ChevronDown } from 'lucide-vue-next'
import { useDataSources } from '~/composables/useDataSources'
import { useAliasGenerator } from '~/composables/useAliasGenerator'

interface Props {
  name?: string
  alias?: string
  title?: string
  description?: string
  tableName?: string
  query?: string
  dataSourceId?: string
  limit?: number
  grouped?: boolean
  ordered?: boolean
  availableTables?: Array<{ name: string; columns: any[] }>
  tableSchema?: any
  availableDataSources?: any[]
  refresh?: { type?: 'every' | 'sql' | 'max'; every?: string; sql?: string; max?: string }
  cache?: { enabled?: boolean; ttl?: number }
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:name': [value: string]
  'update:alias': [value: string]
  'update:title': [value: string]
  'update:description': [value: string]
  'update:tableName': [value: string]
  'update:query': [value: string]
  'update:dataSourceId': [value: string]
  'update:limit': [value: number | undefined]
  'update:grouped': [value: boolean]
  'update:ordered': [value: boolean]
  'update:refresh': [value: any]
  'update:cache': [value: any]
}>()

// Alias generation
const { aliasManuallyEdited, generateAlias, getAliasError, markAsManuallyEdited } = useAliasGenerator()

// Collapsible state
const advancedOpen = ref(false)

// Use props directly instead of local refs
const selectedDataSourceId = computed(() => props.dataSourceId)
const selectedTableName = computed(() => props.tableName)

// Computed alias error
const aliasError = computed(() => {
  if (!props.alias) return ''
  return getAliasError(props.alias)
})

// Debug availableTables
const debugAvailableTables = computed(() => {
  console.log('BasicInfoBuilder - availableTables prop:', props.availableTables)
  return props.availableTables || []
})

// Use data sources from props if available, otherwise fallback to useDataSources
const { dataSources } = useDataSources()
const availableDataSources = computed(() => {
  console.log('BasicInfoBuilder - availableDataSources prop:', props.availableDataSources)
  console.log('BasicInfoBuilder - dataSources from composable:', dataSources.value)
  return props.availableDataSources || dataSources.value || []
})

// Computed property for limit toggle
const limitEnabled = computed(() => {
  return props.limit !== undefined && props.limit !== null
})

// Computed property for query source toggle
const useCustomQuery = computed(() => {
  return !!(props.query && props.query.trim())
})

// Computed property for grouped toggle
const groupedEnabled = computed(() => {
  return props.grouped !== undefined ? props.grouped : true
})

// Computed property for ordered toggle  
const orderedEnabled = computed(() => {
  return props.ordered !== undefined ? props.ordered : true
})

// Refresh policy helpers
const refreshType = computed(() => props.refresh?.type || 'every')
const emitRefresh = (partial: any) => {
  const rk = { ...(props.refresh || {}), ...partial }
  emit('update:refresh', rk)
}
const updateRefreshType = (t: string) => emitRefresh({ type: t })

// Cache helpers
const cacheEnabled = computed(() => {
  // If cache object exists, check the enabled property explicitly
  if (props.cache) {
    return props.cache.enabled === true
  }
  // If no cache object, default to false (disabled)
  return false
})

const emitCache = (partial: any) => {
  const c = { ...(props.cache || {}), ...partial }
  emit('update:cache', c)
}

// Handle limit toggle
const handleLimitToggle = (enabled: boolean) => {
  if (enabled) {
    emit('update:limit', 100)
  } else {
    emit('update:limit', undefined)
  }
}

// Handle query source toggle
const handleQuerySourceToggle = (enabled: boolean) => {
  if (enabled) {
    emit('update:tableName', '')
    emit('update:query', 'SELECT * FROM your_table WHERE condition...')
  } else {
    emit('update:query', '')
  }
}

// Handle grouped toggle
const handleGroupedToggle = (enabled: boolean) => {
  emit('update:grouped', enabled)
}

// Handle ordered toggle
const handleOrderedToggle = (enabled: boolean) => {
  emit('update:ordered', enabled)
}

// Handle cache toggle
const handleCacheToggle = (enabled: boolean) => {
  if (enabled) {
    // When enabling cache, set default TTL if not already set
    emitCache({ 
      enabled: true, 
      ttl: props.cache?.ttl || 300  // Default to 5 minutes if no TTL set
    })
  } else {
    // When disabling cache, set enabled to false
    emitCache({ enabled: false })
  }
}

// Handle alias change
const handleAliasChange = (value: string) => {
  markAsManuallyEdited()
  emit('update:alias', value)
}

// Auto-generate alias from name unless manually edited
watch(() => props.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    emit('update:alias', generateAlias(newName))
  }
})

// No need for watchers since we're using computed properties

// Handle data source change
const handleDataSourceChange = (value: string) => {
  console.log('BasicInfoBuilder - Data source changed to:', value)
  emit('update:dataSourceId', value)
}

// Handle table name change
const handleTableNameChange = (value: string) => {
  console.log('BasicInfoBuilder - Table name changed to:', value)
  emit('update:tableName', value)
}
</script> 