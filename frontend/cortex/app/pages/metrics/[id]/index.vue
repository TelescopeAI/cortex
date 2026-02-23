<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { ArrowLeft, ArrowRight, Trash2, Loader2, Edit, GitBranch } from 'lucide-vue-next'
import type { SemanticOrderSequence } from '~/types/order'
import { toast } from 'vue-sonner'
import SchemaSheet from '~/components/metric/builder/SchemaSheet.vue'
import MetricQueryHistory from '~/components/MetricQueryHistory.vue'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'
import { useDataSources } from '~/composables/useDataSources'
import type { MetricModifiers } from '~/types/metric-modifiers'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger, } from '~/components/ui/alert-dialog'
import MetricDisplayOverviewContainer from '~/components/metric/display/OverviewContainer.vue'
import MetricDisplayExecuteContainer from '~/components/metric/display/ExecuteContainer.vue'
import type { SemanticMetricVariant } from '~/types/metric_variants'

// Page metadata
definePageMeta({
  title: 'Metric Details',
  layout: 'default'
})

// Get metric ID from route
const route = useRoute()
const metricId = route.params.id as string

// Use composables
const { getMetric, executeMetric, getMetricVersions, updateMetric, deleteMetric } = useMetrics()
const { getModel } = useDataModels()
const { selectedEnvironmentId } = useEnvironments()
const { getVariantsForMetric } = useMetricVariants()

// Component state
const metric = ref<any>(null)
const parentModel = ref<any>(null)
const metricVersions = ref<any[]>([])
const executionResults = ref<any>(null)
const compiledQuery = ref('')
const previewResult = ref<any>(null)
const loading = ref(true)
const executing = ref(false)
const previewing = ref(false)

// Schema support for execution modifiers
const tableSchema = ref<any>(null)
const availableTables = computed(() => tableSchema.value?.tables || [])
const availableColumns = computed(() => {
  if (!tableSchema.value?.tables) return []
  const columns: Array<{ name: string; type: string }> = []
  tableSchema.value.tables.forEach((table: any) => {
    table.columns?.forEach((column: any) => {
      columns.push({ name: `${table.name}.${column.name}`, type: column.type })
    })
  })
  return columns
})

const { getDataSourceSchema } = useDataSources()
const schemaLoading = ref(false)
const schemaError = ref<string | null>(null)

const currentDataSourceId = computed(() =>
  metric.value?.data_source_id || selectedDataSourceId.value || ''
)

const loadTableSchema = async (dataSourceId?: string) => {
  if (!dataSourceId) {
    tableSchema.value = null
    return
  }

  schemaLoading.value = true
  schemaError.value = null

  try {
    tableSchema.value = await getDataSourceSchema(dataSourceId)
  } catch (error: any) {
    console.error('Failed to load table schema:', error)
    schemaError.value = error?.data?.detail || error?.message || 'Failed to load data source schema'
    tableSchema.value = null
  } finally {
    schemaLoading.value = false
  }
}

const reloadCurrentSchema = () => {
  if (currentDataSourceId.value) {
    loadTableSchema(currentDataSourceId.value)
  }
}

// Schema sheet state
const schemaSheetOpen = ref(false)
const selectedDataSourceId = ref<string>('')

// Delete dialog state
const deleteDialogOpen = ref(false)
const isDeleting = ref(false)

// Execution parameters
const executionParams = ref<Record<string, any>>({})
const contextId = ref<string>('')
const useLimit = ref(false)
const limitValue = ref<number>(100)
const offsetValue = ref<number>(0)

// Grouping state
const useGrouped = ref(false)
const groupedValue = ref(false)

// Cache preference state
const requestCacheEnabled = ref<boolean>(true)
const requestCacheTtl = ref<number | undefined>(undefined)

// Modifiers state
const modifiersEnabled = ref(false)
const modifiers = ref<MetricModifiers>([])

// Variants state
const variants = ref<SemanticMetricVariant[]>([])
const variantsLoading = ref(false)


// Schema sheet functions
const onOpenSchema = () => {
  // Set data source ID for schema loading if not already set
  if (metric.value?.data_source_id && !selectedDataSourceId.value) {
    selectedDataSourceId.value = metric.value.data_source_id
  }
  schemaSheetOpen.value = true
}

const onSaveSchema = async (schemaData: any) => {
  if (!metric.value || !selectedEnvironmentId.value) return
  
  try {
    // Call the backend API to update the metric
    const updatedMetric = await updateMetric(metricId, selectedEnvironmentId.value, schemaData)
    
    if (updatedMetric) {
      // Update local state with the response from backend
      Object.assign(metric.value, updatedMetric)
      toast.success('Schema updated successfully')
    }
  } catch (error) {
    console.error('Failed to save schema:', error)
    toast.error('Failed to save schema')
  }
}

// Computed properties
const metricStatus = computed(() => {
  if (!metric.value) return 'unknown'
  // This would be determined by actual validation logic
  return 'valid' // placeholder
})

const hasParameters = computed(() => {
  return metric.value?.parameters && Array.isArray(metric.value.parameters) && metric.value.parameters.length > 0
})

const availableCortexParameters = computed(() => {
  if (!metric.value) return []

  const params: string[] = []

  // Check filters for $CORTEX_ parameters
  if (metric.value.filters) {
    metric.value.filters.forEach((filter: any) => {
      if (filter.query && typeof filter.query === 'string' && filter.query.includes('$CORTEX_')) {
        const matches = filter.query.match(/\$CORTEX_([a-zA-Z_][a-zA-Z0-9_]*)/g)
        if (matches) {
          params.push(...matches.map((m: string) => m.replace('$CORTEX_', '')))
        }
      }
      if (filter.value && typeof filter.value === 'string' && filter.value.includes('$CORTEX_')) {
        const matches = filter.value.match(/\$CORTEX_([a-zA-Z_][a-zA-Z0-9_]*)/g)
        if (matches) {
          params.push(...matches.map((m: string) => m.replace('$CORTEX_', '')))
        }
      }
    })
  }

  // Check custom query for $CORTEX_ parameters
  if (metric.value.query && typeof metric.value.query === 'string') {
    const matches = metric.value.query.match(/\$CORTEX_([a-zA-Z_][a-zA-Z0-9_]*)/g)
    if (matches) {
      params.push(...matches.map((m: string) => m.replace('$CORTEX_', '')))
    }
  }

  // Remove duplicates and return
  return [...new Set(params)]
})

const recentVariants = computed(() => {
  return variants.value.slice(0, 5)
})

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'valid': return 'default'
    case 'invalid': return 'destructive'
    case 'pending': return 'secondary'
    default: return 'outline'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'valid': return '✅'
    case 'invalid': return '⚠️'
    case 'pending': return '🔄'
    default: return '❓'
  }
}

// Get user's locale from browser
const { language } = useNavigatorLanguage()

// Helper function to convert UTC date string to local timezone
const convertUTCToLocal = (dateString: string): Date => {
  // Parse the UTC date string and convert to local timezone
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

// Format relative time using VueUse
const formatRelativeTime = (date: string | Date) => {
  // Convert UTC to local timezone before passing to useTimeAgo
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, { 
    updateInterval: 1000 // Update every second for real-time updates
  })
}

// Format absolute date using VueUse
const formatAbsoluteDate = (date: string | Date) => {
  // Convert UTC to local timezone before passing to useDateFormat
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useDateFormat(localDate, 'MMM D, YYYY', { 
    locales: language.value || 'en-US' 
  })
}

// Event handlers
const onBack = () => {
  navigateTo('/metrics?view=metrics')
}

const onEdit = () => {
  navigateTo(`/metrics/${metricId}/edit`)
}

const onModelClick = () => {
  if (metric.value?.data_model_id) {
    navigateTo(`/metrics/models/${metric.value.data_model_id}`)
  }
}

const onDelete = async () => {
  if (!metric.value || !selectedEnvironmentId.value) return
  
  isDeleting.value = true
  try {
    const success = await deleteMetric(metricId, selectedEnvironmentId.value)
    if (success) {
      toast.success('Metric deleted successfully')
      navigateTo('/metrics')
    } else {
      toast.error('Failed to delete metric')
    }
  } catch (error) {
    console.error('Failed to delete metric:', error)
    toast.error('Failed to delete metric')
  } finally {
    isDeleting.value = false
    deleteDialogOpen.value = false
  }
}

const onPreview = async () => {
  if (!metric.value || !selectedEnvironmentId.value) return
  
  previewing.value = true
  try {
    const previewRequest: any = {
      parameters: executionParams.value,
      context_id: contextId.value || undefined,
    }
    
    // Add grouping if enabled
    if (useGrouped.value) {
      previewRequest.grouped = groupedValue.value
    }
    
    // Add limit if enabled
    if (useLimit.value) {
      previewRequest.limit = limitValue.value
      if (offsetValue.value > 0) {
        previewRequest.offset = offsetValue.value
      }
    }
    
    if (modifiersEnabled.value && modifiers.value.length > 0) {
      previewRequest.modifiers = modifiers.value.map((modifier) => {
        const payload: any = {}
        if (modifier.measures && modifier.measures.length > 0) payload.measures = modifier.measures
        if (modifier.dimensions && modifier.dimensions.length > 0) payload.dimensions = modifier.dimensions
        if (modifier.joins && modifier.joins.length > 0) payload.joins = modifier.joins
        if (modifier.filters && modifier.filters.length > 0) payload.filters = modifier.filters
        if (modifier.order && modifier.order.length > 0) payload.order = modifier.order as SemanticOrderSequence[]
        if (modifier.limit !== undefined && modifier.limit !== null) payload.limit = modifier.limit
        return payload
      }).filter((entry: any) => Object.keys(entry).length > 0)
    }
    
    const result = await executeMetric(metricId, previewRequest, true) as any
    previewResult.value = result
    // Update compiled query from preview result metadata
    if (result.metadata?.query) {
      compiledQuery.value = result.metadata.query
    }
    console.log('Preview result:', result)
    if (result.success) {
      toast.success('Query preview generated successfully')
    } else {
      toast.error('Query preview failed - check errors')
    }
  } catch (error) {
    console.error('Failed to preview metric:', error)
    toast.error('Failed to generate query preview')
  } finally {
    previewing.value = false
  }
}

const onExecute = async () => {
  if (!metric.value) return
  
  executing.value = true
  try {
    const executionRequest: any = {
      parameters: executionParams.value,
      context_id: contextId.value || undefined,
      cache: { enabled: requestCacheEnabled.value, ttl: requestCacheTtl.value }
    }
    
    // Add limit and offset if enabled
    if (useLimit.value) {
      executionRequest.limit = limitValue.value
      if (offsetValue.value > 0) {
        executionRequest.offset = offsetValue.value
      }
    }
    
    // Add grouping if enabled
    if (useGrouped.value) {
      executionRequest.grouped = groupedValue.value
    }
 
    if (modifiersEnabled.value && modifiers.value.length > 0) {
      executionRequest.modifiers = modifiers.value.map((modifier) => {
        const payload: any = {}
        if (modifier.measures && modifier.measures.length > 0) payload.measures = modifier.measures
        if (modifier.dimensions && modifier.dimensions.length > 0) payload.dimensions = modifier.dimensions
        if (modifier.joins && modifier.joins.length > 0) payload.joins = modifier.joins
        if (modifier.filters && modifier.filters.length > 0) payload.filters = modifier.filters
        if (modifier.order && modifier.order.length > 0) payload.order = modifier.order as SemanticOrderSequence[]
        if (modifier.limit !== undefined && modifier.limit !== null) payload.limit = modifier.limit
        return payload
      }).filter((entry: any) => Object.keys(entry).length > 0)
    }

    if (!selectedEnvironmentId.value) return
    
    const result = await executeMetric(metricId, executionRequest) as any
    executionResults.value = result
    
    // Update compiled query from execution result
    if (result.metadata?.query) {
      compiledQuery.value = result.metadata.query
    }
    
    // Show appropriate toast based on execution result
    if (result.success) {
      toast.success('Metric executed successfully')
    } else {
      toast.error('Metric execution failed - check results for details')
    }
    
    // Refresh query history after execution
    await refreshQueryHistory()
  } catch (error) {
    console.error('Failed to execute metric:', error)
    toast.error('Failed to execute metric')
  } finally {
    executing.value = false
  }
}

// Query history refresh
const queryHistoryRef = ref()
const refreshQueryHistory = async () => {
  if (queryHistoryRef.value) {
    await queryHistoryRef.value.refreshHistory()
  }
}

const onCopyQuery = () => {
  if (metric.value?.query) {
    navigator.clipboard.writeText(metric.value.query)
    toast.success('Query copied to clipboard')
  } else if (compiledQuery.value && compiledQuery.value !== 'No compiled query available') {
    navigator.clipboard.writeText(compiledQuery.value)
    toast.success('Compiled query copied to clipboard')
  } else {
    toast.error('No query available to copy')
  }
}

const onParameterChange = (paramName: string, value: any) => {
  executionParams.value[paramName] = value
}

const handleMetricUpdated = (updatedMetric: any) => {
  // Update the local metric data with the updated data
  Object.assign(metric.value, updatedMetric)
  toast.success('Metric updated successfully')
}

const navigateToVariantsList = () => {
  navigateTo(`/metrics/${metricId}/variants`)
}

const navigateToVariant = (variantId: string) => {
  navigateTo(`/metrics/${metricId}/variants/${variantId}`)
}

const createVariant = () => {
  navigateTo(`/metrics/${metricId}/variants/create`)
}

// Data loading
const loadMetric = async () => {
  try {
    if (!selectedEnvironmentId.value) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Environment not selected'
      })
    }
    
    metric.value = await getMetric(metricId, selectedEnvironmentId.value)
    if (!metric.value) {
      throw createError({
        statusCode: 404,
        statusMessage: 'Metric not found'
      })
    }
  } catch (error) {
    console.error('Failed to load metric:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to load metric'
    })
  }
}

const loadParentModel = async () => {
  if (!metric.value?.data_model_id || !selectedEnvironmentId.value) return
  
  try {
    parentModel.value = await getModel(metric.value.data_model_id, selectedEnvironmentId.value)
  } catch (error) {
    console.error('Failed to load parent model:', error)
  }
}

const loadMetricVersions = async () => {
  try {
    metricVersions.value = await getMetricVersions(metricId)
  } catch (error) {
    console.error('Failed to load metric versions:', error)
    metricVersions.value = []
  }
}

const loadVariants = async () => {
  if (!selectedEnvironmentId.value) return

  variantsLoading.value = true
  try {
    variants.value = await getVariantsForMetric(metricId, selectedEnvironmentId.value)
  } catch (error) {
    console.error('Failed to load variants:', error)
    variants.value = []
  } finally {
    variantsLoading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    await loadMetric()
    await Promise.all([
      loadParentModel(),
      loadMetricVersions(),
      loadVariants()
    ])

    // Set selected data source ID for schema loading
    if (metric.value?.data_source_id) {
      selectedDataSourceId.value = metric.value.data_source_id
    }
  } finally {
    loading.value = false
  }
}

// Initialize parameters from metric definition
const initializeParameters = () => {
  if (metric.value?.parameters && Array.isArray(metric.value.parameters)) {
    const params: Record<string, any> = {}
    metric.value.parameters.forEach((param: any) => {
      if (param.default_value !== undefined) {
        params[param.name] = param.default_value
      }
    })
    executionParams.value = params
  }
}

// Watch for metric changes to initialize grouped value
watch(() => metric.value, (newMetric) => {
  if (newMetric) {
    // Initialize groupedValue based on metric's grouped setting
    groupedValue.value = newMetric.grouped !== undefined ? newMetric.grouped : true
  }
}, { immediate: true })

// Initialize
onMounted(() => {
  loadData().then(() => {
    initializeParameters()
    if (currentDataSourceId.value) {
      loadTableSchema(currentDataSourceId.value)
    }
  })
})

watch(currentDataSourceId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadTableSchema(newId)
  }
})
</script>

<template>
  <div class="py-6 space-y-6">
    <!-- Loading state -->
    <div v-if="loading" class="space-y-6">
      <div class="flex items-center space-x-4">
        <div class="h-8 w-8 bg-muted rounded animate-pulse"></div>
        <div class="h-8 w-64 bg-muted rounded animate-pulse"></div>
      </div>
      <Card>
        <CardContent class="pt-6">
          <div class="space-y-4 min-w-0">
            <div class="h-6 bg-muted rounded w-1/4 animate-pulse"></div>
            <div class="h-32 bg-muted rounded animate-pulse"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Content -->
    <div v-else-if="metric" class="space-y-6">
      <div class="flex flex-col space-y-4"></div>
      <!-- Header -->
      <div class="flex flex-col space-y-4">
        <Button variant="ghost" size="sm" @click="onBack" class="w-fit">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Metrics
        </Button>
        
        <div class="flex flex-col gap-y-4 items-start justify-between">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight">
              {{ metric.name }}
            </h1>
            <p class="text-sm text-muted-foreground">
              {{ metric.title || '' }}
            </p>
          </div>
          <div class="flex flex-col space-y-2">
            <div class="flex space-x-2">
              <Button variant="outline" size="sm" @click="onOpenSchema">
                <Edit class="h-4 w-4 mr-2" />
                Edit
              </Button>
              <AlertDialog v-model:open="deleteDialogOpen">
                <AlertDialogTrigger as-child>
                  <Button variant="outline" size="sm">
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Metric</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete the metric "{{ metric.name }}"? This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction 
                      @click="onDelete" 
                      :disabled="isDeleting"
                      class="bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      <Loader2 v-if="isDeleting" class="h-4 w-4 mr-2 animate-spin" />
                      {{ isDeleting ? 'Deleting...' : 'Delete' }}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="execute">Execute</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-6">
          <MetricDisplayOverviewContainer
            :metric="metric"
            :parent-model="parentModel"
            :metric-status="metricStatus"
            :format-relative-time="formatRelativeTime"
            :format-absolute-date="formatAbsoluteDate"
            :get-status-badge-variant="getStatusBadgeVariant"
            @model-click="onModelClick"
          />
        </TabsContent>



        <!-- Query Tab -->
        <TabsContent value="query" class="space-y-6">
          <MetricDisplayQueryContainer
            :validating="previewing"
            :validation-result="previewResult"
            :compiled-query="compiledQuery"
            :original-query="metric.query"
            @validate="onPreview"
            @copy-query="onCopyQuery"
          />
        </TabsContent>

        <!-- Execute Tab -->
        <TabsContent value="execute" class="space-y-6 min-w-0">
          <MetricDisplayExecuteContainer
            :validating="previewing"
            :validation-result="previewResult"
            :compiled-query="compiledQuery"
            :original-query="metric?.query || ''"
            :context-id="contextId"
            :cache-enabled="requestCacheEnabled"
            :cache-ttl="requestCacheTtl"
            :execution-params="executionParams"
            :use-limit="useLimit"
            :limit-value="limitValue"
            :offset-value="offsetValue"
            :use-grouped="useGrouped"
            :grouped-value="groupedValue"
            :metric-grouped="metric?.grouped !== undefined ? metric.grouped : true"
            :modifiers-enabled="modifiersEnabled"
            :modifiers="modifiers"
            :parameters="metric?.parameters || []"
            :available-cortex-parameters="availableCortexParameters"
            :table-schema="tableSchema"
            :available-tables="availableTables"
            :available-columns="availableColumns"
            :metric="metric"
            :schema-loading="schemaLoading"
            :schema-error="schemaError"
            :has-parameters="hasParameters"
            :executing="executing"
            :execution-results="executionResults"
            @update:context-id="contextId = $event"
            @update:cache-enabled="requestCacheEnabled = $event"
            @update:cache-ttl="requestCacheTtl = $event"
            @update:execution-params="executionParams = $event"
            @update:use-limit="useLimit = $event"
            @update:limit-value="limitValue = $event"
            @update:offset-value="offsetValue = $event"
            @update:use-grouped="useGrouped = $event"
            @update:grouped-value="groupedValue = $event"
            @update:modifiers-enabled="modifiersEnabled = $event"
            @update:modifiers="modifiers = $event"
            @validate="onPreview"
            @copy-query="onCopyQuery"
            @reload-schema="reloadCurrentSchema"
            @execute="onExecute"
          />
        </TabsContent>

        <TabsContent value="history" class="space-y-6">
          <MetricQueryHistory
            :metric-id="metric?.id || ''"
            @refresh="refreshQueryHistory"
            ref="queryHistoryRef"
          />
        </TabsContent>
      </Tabs>

      <!-- Variants Section -->
      <Card class="mt-6">
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle class="flex items-center gap-2">
              <GitBranch class="h-5 w-5 text-purple-600 dark:text-purple-400" />
              Variants
              <Badge variant="secondary">
                {{ variants.length }}
              </Badge>
            </CardTitle>
            <Button @click="navigateToVariantsList">
              View All
              <ArrowRight class="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <!-- Loading state -->
          <div v-if="variantsLoading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div v-for="i in 3" :key="i" class="h-40 rounded-lg border bg-card animate-pulse"></div>
          </div>

          <!-- Show 5 most recent variants -->
          <div v-else-if="variants.length > 0" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <MetricVariantsListCard
              v-for="variant in recentVariants"
              :key="variant.id"
              :variant="variant"
              :source-metric-name="metric.name"
              @click="navigateToVariant(variant.id)"
            />
          </div>

          <!-- Empty state -->
          <div v-else class="py-8 text-center text-muted-foreground">
            <GitBranch class="h-8 w-8 mx-auto mb-2 opacity-50" />
            <Button variant="outline" size="sm" class="mt-2" @click="createVariant">
              Add
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Error state -->
    <div v-else class="text-center py-12">
      <h3 class="text-lg font-medium text-muted-foreground mb-2">Metric not found</h3>
      <p class="text-sm text-muted-foreground mb-4">
        The requested metric could not be found or you don't have permission to view it.
      </p>
      <Button @click="onBack">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Metrics
      </Button>
    </div>

    <!-- Schema Sheet -->
    <SchemaSheet
      :open="schemaSheetOpen"
      :metric="metric"
      :selected-data-source-id="selectedDataSourceId"
      @update:open="schemaSheetOpen = $event"
      @save="onSaveSchema"
    />

  </div>
</template>