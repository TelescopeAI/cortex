<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Separator } from '~/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { ArrowLeft, Edit, PlayCircle, Settings, Copy, History, Code, Save, Loader2, CheckCircle, XCircle, Database } from 'lucide-vue-next'
import ExecutionResultViewer from '@/components/ExecutionResultViewer.vue'
import { toast } from 'vue-sonner'
import SchemaSheet from '~/components/metric-builder/SchemaSheet.vue'
import CodeHighlight from '~/components/CodeHighlight.vue'
import KeyValuePairs from '~/components/KeyValuePairs.vue'
import ContextIdBuilder from '~/components/ContextIdBuilder.vue'
import MetricQueryHistory from '~/components/MetricQueryHistory.vue'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Metric Details',
  layout: 'default'
})

// Get metric ID from route
const route = useRoute()
const metricId = route.params.id as string

// Use composables
const { getMetric, executeMetric, validateMetric, getMetricVersions, updateMetric } = useMetrics()
const { getModel } = useDataModels()

// Component state
const metric = ref<any>(null)
const parentModel = ref<any>(null)
const metricVersions = ref<any[]>([])
const executionResults = ref<any>(null)
const compiledQuery = ref('')
const validationResult = ref<any>(null)
const loading = ref(true)
const executing = ref(false)
const validating = ref(false)


// Schema sheet state
const schemaSheetOpen = ref(false)
const selectedDataSourceId = ref<string>('')

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

// Schema sheet functions
const onOpenSchema = () => {
  // Set data source ID for schema loading if not already set
  if (parentModel.value?.data_source_id && !selectedDataSourceId.value) {
    selectedDataSourceId.value = parentModel.value.data_source_id
  }
  schemaSheetOpen.value = true
}

const onSaveSchema = async (schemaData: any) => {
  if (!metric.value) return
  
  try {
    // Call the backend API to update the metric
    const updatedMetric = await updateMetric(metricId, schemaData)
    
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

const onValidate = async () => {
  if (!metric.value) return
  
  validating.value = true
  try {
    const result = await validateMetric(metricId) as any
    validationResult.value = result
    // Update compiled query if validation succeeded and query is available
    if (result.compiled_query) {
      compiledQuery.value = result.compiled_query
    }
    console.log('Validation result:', result)
    toast.success('Validation completed')
    // Reload metric to get updated validation status and compiled query
    await loadMetric()
  } catch (error) {
    console.error('Failed to validate metric:', error)
    toast.error('Validation failed')
  } finally {
    validating.value = false
  }
}

const onExecute = async () => {
  if (!metric.value) return
  
  executing.value = true
  try {
    const executionRequest: any = {
      parameters: executionParams.value,
      context_id: contextId.value || undefined,
      cache: { enabled: requestCacheEnabled.value }
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
    
    const result = await executeMetric(metricId, executionRequest) as any
    executionResults.value = result
    
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

// Data loading
const loadMetric = async () => {
  try {
    metric.value = await getMetric(metricId)
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
  if (!metric.value?.data_model_id) return
  
  try {
    parentModel.value = await getModel(metric.value.data_model_id)
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

const loadData = async () => {
  loading.value = true
  try {
    await loadMetric()
    await Promise.all([
      loadParentModel(),
      loadMetricVersions()
    ])
    
    // Set selected data source ID for schema loading
    if (parentModel.value?.data_source_id) {
      selectedDataSourceId.value = parentModel.value.data_source_id
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
  })
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
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
            <Button variant="outline" size="sm" @click="onOpenSchema">
              <Edit class="h-4 w-4 mr-2" />
              Edit Schema
            </Button>
          </div>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="query">Query</TabsTrigger>
          <TabsTrigger value="execute">Execute</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-6">
          <!-- Basic Information -->
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent class="space-y-6">
              <!-- Status and Model -->
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Status</div>
                  <Badge :variant="getStatusBadgeVariant(metricStatus)">
                    {{ getStatusIcon(metricStatus) }} {{ metricStatus }}
                  </Badge>
                </div>
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Parent Model</div>
                  <Button 
                    variant="link" 
                    class="p-0 h-auto text-sm justify-start"
                    @click="onModelClick"
                  >
                    📁 {{ parentModel?.name || 'Unknown Model' }}
                  </Button>
                </div>
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Visibility</div>
                  <Badge variant="outline">
                    {{ metric.public ? '🌐 Public' : '🔒 Private' }}
                  </Badge>
                </div>
              </div>

              <Separator />

              <!-- Names and Identifiers -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Name</div>
                  <div class="text-sm font-mono bg-muted p-2 rounded">{{ metric.name }}</div>
                </div>
                <div v-if="metric.alias" class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Alias</div>
                  <div class="text-sm font-mono bg-muted p-2 rounded">{{ metric.alias }}</div>
                </div>
              </div>

              <!-- Data Source Information -->
              <div v-if="parentModel?.data_source" class="space-y-2">
                <div class="text-sm font-medium text-muted-foreground">Data Source</div>
                <div class="text-sm font-mono bg-muted p-2 rounded">{{ parentModel.data_source.name }}</div>
              </div>

              <!-- Grouping Configuration -->
              <div class="space-y-2">
                <div class="text-sm font-medium text-muted-foreground">Grouping Configuration</div>
                <div class="flex items-center space-x-2">
                  <Badge :variant="metric.grouped ? 'default' : 'secondary'">
                    {{ metric.grouped ? '📊 Grouped' : '📋 Ungrouped' }}
                  </Badge>
                  <span class="text-sm text-muted-foreground">
                    {{ metric.grouped ? 'Results will be grouped by dimensions' : 'Results will not be grouped' }}
                  </span>
                </div>
              </div>

              <!-- Description -->
              <div v-if="metric.description" class="space-y-2">
                <div class="text-sm font-medium text-muted-foreground">Description</div>
                <p class="text-sm">{{ metric.description }}</p>
              </div>

              <!-- Parameters -->
              <div v-if="hasParameters" class="space-y-2">
                <div class="text-sm font-medium text-muted-foreground">Parameters</div>
                <div class="space-y-2">
                  <div 
                    v-for="param in metric.parameters" 
                    :key="param.name"
                    class="flex items-center justify-between p-3 bg-muted rounded"
                  >
                    <div class="space-y-1">
                      <div class="font-medium text-sm">{{ param.name }}</div>
                      <div class="text-xs text-muted-foreground">
                        {{ param.type }}{{ param.required ? ' (required)' : ' (optional)' }}
                      </div>
                      <div v-if="param.description" class="text-xs text-muted-foreground">
                        {{ param.description }}
                      </div>
                    </div>
                    <div v-if="param.default_value !== undefined" class="text-xs text-muted-foreground">
                      Default: {{ param.default_value }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Timestamps -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="space-y-1">
                  <div class="text-muted-foreground">Created</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(metric.created_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(metric.created_at) }}</div>
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="text-muted-foreground">Last Updated</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(metric.updated_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(metric.updated_at) }}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>



        <!-- Query Tab -->
        <TabsContent value="query" class="space-y-6">
          <!-- Action Buttons -->
          <Card>
            <CardHeader>
              <CardTitle>Query Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="flex gap-4">
                <Button @click="onValidate" :disabled="validating" class="flex-1">
                  <Settings class="h-4 w-4 mr-2" />
                  {{ validating ? 'Validating & Compiling...' : 'Validate & Compile Query' }}
                </Button>
              </div>
            </CardContent>
          </Card>

          <!-- Validation Results -->
          <Card v-if="validationResult">
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <CheckCircle v-if="validationResult.is_valid" class="h-5 w-5 text-green-500" />
                <XCircle v-else class="h-5 w-5 text-red-500" />
                <span>Validation Results</span>
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center space-x-2">
                <Badge :variant="validationResult.is_valid ? 'default' : 'destructive'">
                  {{ validationResult.is_valid ? 'Valid' : 'Invalid' }}
                </Badge>
              </div>
              
              <div v-if="validationResult.warnings && validationResult.warnings.length > 0" class="space-y-2">
                <h4 class="font-medium text-sm">Warnings:</h4>
                <div class="space-y-1">
                  <div v-for="warning in validationResult.warnings" :key="warning" class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                    {{ warning }}
                  </div>
                </div>
              </div>
              

            </CardContent>
          </Card>

          <!-- Compilation Results -->
          <Card v-if="compiledQuery || (validationResult && !validationResult.is_valid)">
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <Code class="h-5 w-5" />
                <span>Compiled Query</span>
                <Button v-if="compiledQuery" variant="outline" size="sm" @click="onCopyQuery" class="ml-auto">
                  <Copy class="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div v-if="compiledQuery">
                <CodeHighlight lang="sql" :code="compiledQuery" />
              </div>
              
              <!-- Show compilation errors here if validation failed -->
              <div v-if="validationResult && !validationResult.is_valid && validationResult.errors" class="space-y-2">
                <h4 class="font-medium text-sm text-red-600">Compilation Errors:</h4>
                <div class="space-y-1">
                  <div v-for="error in validationResult.errors" :key="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {{ error }}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Original SQL Query - only show if metric has custom SQL query -->
          <Card v-if="metric.query">
            <CardHeader>
              <CardTitle>Original SQL Query</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <CodeHighlight lang="sql" :code="metric.query" />
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Execute Tab -->
        <TabsContent value="execute" class="space-y-6 min-w-0">
          <!-- Context ID Input -->
          <Card>
            <CardHeader>
              <CardTitle>Execution Context</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <ContextIdBuilder v-model="contextId" />
            </CardContent>
          </Card>

          <!-- Cache Preference -->
          <Card>
            <CardHeader>
              <CardTitle>Cache Preference</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center space-x-3">
                <Switch id="cache-enabled" v-model="requestCacheEnabled" />
                <Label for="cache-enabled">Enabled</Label>
              </div>
              <p class="text-xs text-muted-foreground">This overrides the metric default defined in the schema.</p>
            </CardContent>
          </Card>

          <!-- Parameter Input -->
          <Card v-if="hasParameters">
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <KeyValuePairs
                :model-value="executionParams"
                @update:model-value="(value) => executionParams = value || {}"
                :is-loading="executing"
              />
              <div class="text-xs text-muted-foreground">
                <p>Available parameters from metric schema: {{ metric.parameters?.map((p: any) => p.name).join(', ') || 'None' }}</p>
                <p class="mt-1">Use $CORTEX_ prefix in metric schema to auto-substitute with consumer properties when context_id is provided.</p>
                <p v-if="availableCortexParameters.length > 0" class="mt-1">
                  <span class="font-medium">$CORTEX_ parameters found:</span> {{ availableCortexParameters.join(', ') }}
                </p>
              </div>
            </CardContent>
          </Card>

          <!-- Limit and Offset Controls -->
          <Card>
            <CardHeader>
              <CardTitle>Query Limits</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center space-x-2">
                <Switch
                  id="use-limit"
                  v-model="useLimit"
                />
                <Label for="use-limit">Enable custom limit and offset</Label>
              </div>
              
              <div v-if="useLimit" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label for="limit-value">Limit</Label>
                    <Input
                      id="limit-value"
                      v-model.number="limitValue"
                      type="number"
                      min="1"
                      max="10000"
                      placeholder="100"
                    />
                    <div class="text-xs text-muted-foreground">
                      Maximum number of rows to return (1-10,000)
                    </div>
                  </div>
                  
                  <div class="space-y-2">
                    <Label for="offset-value">Offset</Label>
                    <Input
                      id="offset-value"
                      v-model.number="offsetValue"
                      type="number"
                      min="0"
                      placeholder="0"
                    />
                    <div class="text-xs text-muted-foreground">
                      Number of rows to skip (0+)
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Grouping Control -->
          <Card>
            <CardHeader>
              <CardTitle>Query Grouping</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center space-x-2">
                <Switch
                  id="use-grouped"
                  v-model="useGrouped"
                />
                <Label for="use-grouped">Override metric grouping</Label>
              </div>
              
              <div v-if="useGrouped" class="space-y-4">
                <div class="flex items-center space-x-3">
                  <Switch
                    id="grouped-value"
                    v-model="groupedValue"
                  />
                  <Label for="grouped-value">
                    {{ groupedValue ? 'Enable grouping' : 'Disable grouping' }}
                  </Label>
                </div>
                <div class="text-xs text-muted-foreground">
                  <p v-if="groupedValue">
                    Results will be grouped by dimensions (applies GROUP BY clause).
                  </p>
                  <p v-else>
                    Results will not be grouped (no GROUP BY clause applied).
                  </p>
                  <p class="mt-1">
                    Current metric setting: <span class="font-medium">{{ metric?.grouped ? 'Grouped' : 'Ungrouped' }}</span>
                  </p>
                </div>
              </div>
              
              <div v-else class="text-xs text-muted-foreground">
                Using metric's default grouping setting: <span class="font-medium">{{ metric?.grouped ? 'Grouped' : 'Ungrouped' }}</span>
              </div>
            </CardContent>
          </Card>

          <!-- Execute Button -->
          <Card>
            <CardHeader>
              <CardTitle>Execute Metric</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <Button 
                @click="onExecute" 
                :disabled="executing"
                class="w-full"
              >
                <PlayCircle class="h-4 w-4 mr-2" />
                {{ executing ? 'Executing...' : 'Execute Metric' }}
              </Button>
            </CardContent>
          </Card>

          <!-- Execution Results -->
          <Card v-if="executionResults">
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <CheckCircle v-if="executionResults.success" class="h-5 w-5 text-green-500" />
                <XCircle v-else class="h-5 w-5 text-red-500" />
                <span>Execution Results</span>
                <Badge :variant="executionResults.success ? 'default' : 'destructive'">
                  {{ executionResults.success ? 'Success' : 'Failed' }}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <!-- Show errors if execution failed -->
              <div v-if="!executionResults.success && executionResults.errors && executionResults.errors.length > 0" class="space-y-2">
                <h4 class="font-medium text-sm text-red-600">Execution Errors:</h4>
                <div class="space-y-1">
                  <div v-for="error in executionResults.errors" :key="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {{ error }}
                  </div>
                </div>
              </div>
              
              <!-- Show data if execution was successful -->
              <div v-if="executionResults.success && executionResults.data">
                <ExecutionResultViewer :data="executionResults.data || []" :metadata="executionResults.metadata || {}" />
              </div>
              
              <!-- Show message if no data returned -->
              <div v-if="executionResults.success && (!executionResults.data || executionResults.data.length === 0)" class="text-center py-8">
                <Database class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No data returned</h3>
                <p class="text-sm text-muted-foreground">
                  The query executed successfully but returned no results.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- History Tab -->
        <TabsContent value="history" class="space-y-6">
          <MetricQueryHistory 
            :metric-id="metric?.id || ''" 
            @refresh="refreshQueryHistory"
            ref="queryHistoryRef"
          />
        </TabsContent>
      </Tabs>
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