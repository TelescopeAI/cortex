<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Separator } from '~/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import { ArrowLeft, Edit, PlayCircle, Settings, Copy, History, Code, Save, Loader2, CheckCircle, XCircle } from 'lucide-vue-next'
import ExecutionResultViewer from '@/components/ExecutionResultViewer.vue'
import { toast } from 'vue-sonner'
import SchemaSheet from '~/components/metric-builder/SchemaSheet.vue'
import CodeHighlight from '~/components/CodeHighlight.vue'
import EditMetricDialog from '~/components/EditMetricDialog.vue'
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
const { getMetric, executeMetric, validateMetric, compileMetric, getMetricVersions, updateMetric } = useMetrics()
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
const compiling = ref(false)

// Schema dialog state
const schemaDialogOpen = ref(false)
const selectedDataSourceId = ref<string>('')

// Execution parameters
const executionParams = ref<Record<string, any>>({})

// Schema dialog functions
const onOpenSchema = () => {
  // Set data source ID for schema loading if not already set
  if (parentModel.value?.data_source_id && !selectedDataSourceId.value) {
    selectedDataSourceId.value = parentModel.value.data_source_id
  }
  schemaDialogOpen.value = true
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
    const result = await validateMetric(metricId)
    validationResult.value = result
    console.log('Validation result:', result)
    toast.success('Validation completed')
  } catch (error) {
    console.error('Failed to validate metric:', error)
    toast.error('Validation failed')
  } finally {
    validating.value = false
  }
}

const onCompile = async () => {
  if (!metric.value) return
  
  compiling.value = true
  try {
    const result = await compileMetric(metricId)
    compiledQuery.value = (result as any)?.compiled_query || (result as any)?.sql || (result as any)?.query || 'No compiled query available'
    toast.success('Query compiled successfully')
  } catch (error) {
    console.error('Failed to compile metric:', error)
    toast.error('Compilation failed')
  } finally {
    compiling.value = false
  }
}

const onExecute = async () => {
  if (!metric.value) return
  
  executing.value = true
  try {
    const result = await executeMetric(metricId, {
      parameters: executionParams.value
    })
    executionResults.value = result
  } catch (error) {
    console.error('Failed to execute metric:', error)
  } finally {
    executing.value = false
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
            <EditMetricDialog
              :metric="metric"
              @updated="handleMetricUpdated"
            />
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
                  {{ validating ? 'Validating...' : 'Validate Query' }}
                </Button>
                <Button @click="onCompile" :disabled="compiling" class="flex-1">
                  <Code class="h-4 w-4 mr-2" />
                  {{ compiling ? 'Compiling...' : 'Compile Query' }}
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
              
              <div v-if="validationResult.errors && validationResult.errors.length > 0" class="space-y-2">
                <h4 class="font-medium text-sm">Errors:</h4>
                <div class="space-y-1">
                  <div v-for="error in validationResult.errors" :key="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {{ error }}
                  </div>
                </div>
              </div>
              
              <div v-if="validationResult.warnings && validationResult.warnings.length > 0" class="space-y-2">
                <h4 class="font-medium text-sm">Warnings:</h4>
                <div class="space-y-1">
                  <div v-for="warning in validationResult.warnings" :key="warning" class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                    {{ warning }}
                  </div>
                </div>
              </div>
              
              <div v-if="validationResult.compiled_query" class="space-y-2">
                <CodeHighlight lang="sql" :code="validationResult.compiled_query" />
              </div>
            </CardContent>
          </Card>

          <!-- Compilation Results -->
          <Card v-if="compiledQuery">
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <Code class="h-5 w-5" />
                <span>Compiled Query</span>
                <Button variant="outline" size="sm" @click="onCopyQuery" class="ml-auto">
                  <Copy class="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent class="">
              <CodeHighlight lang="sql" :code="compiledQuery" />
            </CardContent>
          </Card>

          <!-- Original SQL Query -->
          <Card>
            <CardHeader>
              <CardTitle>Original SQL Query</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div v-if="metric.query">
                <CodeHighlight lang="sql" :code="metric.query" />
              </div>
              <div v-else class="text-center py-8">
                <Code class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No SQL query</h3>
                <p class="text-sm text-muted-foreground">
                  This metric doesn't have a SQL query defined yet.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Execute Tab -->
        <TabsContent value="execute" class="space-y-6 min-w-0">
          <!-- Parameter Input -->
          <Card v-if="hasParameters">
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div 
                v-for="param in metric.parameters" 
                :key="param.name"
                class="space-y-2"
              >
                <label class="text-sm font-medium">
                  {{ param.name }}
                  <span v-if="param.required" class="text-destructive">*</span>
                </label>
                <Input
                  :model-value="executionParams[param.name]"
                  @update:model-value="onParameterChange(param.name, $event)"
                  :placeholder="param.description || `Enter ${param.name}`"
                  :type="param.type === 'number' ? 'number' : 'text'"
                />
                <div v-if="param.description" class="text-xs text-muted-foreground">
                  {{ param.description }}
                </div>
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
              <CardTitle>Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ExecutionResultViewer :data="executionResults.data || []" :metadata="executionResults.metadata || {}" />
            </CardContent>
          </Card>
        </TabsContent>

        <!-- History Tab -->
        <TabsContent value="history" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Version History</CardTitle>
            </CardHeader>
            <CardContent>
              <div v-if="metricVersions.length === 0" class="text-center py-8">
                <History class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No version history</h3>
                <p class="text-sm text-muted-foreground">
                  Version history will appear here as you make changes to this metric.
                </p>
              </div>

              <Table v-else>
                <TableHeader>
                  <TableRow>
                    <TableHead>Version</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Changes</TableHead>
                    <TableHead class="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="version in metricVersions" :key="version.id">
                    <TableCell class="font-medium">{{ version.version }}</TableCell>
                    <TableCell>
                      <div class="space-y-1">
                        <div>{{ formatAbsoluteDate(version.created_at) }}</div>
                        <div class="text-xs text-muted-foreground">{{ formatRelativeTime(version.created_at) }}</div>
                      </div>
                    </TableCell>
                    <TableCell>{{ version.change_summary || 'No summary' }}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
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
      :open="schemaDialogOpen"
      :metric="metric"
      :selected-data-source-id="selectedDataSourceId"
      @update:open="schemaDialogOpen = $event"
      @save="onSaveSchema"
    />
  </div>
</template> 