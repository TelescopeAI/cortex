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
import { ArrowLeft, Edit, PlayCircle, Settings, Copy, History, Code, Save, Loader2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import MetricSchemaBuilder from '~/components/metric-builder/MetricSchemaBuilder.vue'

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
const loading = ref(true)
const executing = ref(false)
const validating = ref(false)
const compiling = ref(false)

// Schema editing state
const isEditingSchema = ref(false)
const schemaData = ref<any>({})
const selectedDataSourceId = ref<string>('')
const isSavingSchema = ref(false)

// Execution parameters
const executionParams = ref<Record<string, any>>({})

// Schema editing functions
const onEditSchema = () => {
  isEditingSchema.value = true
  // Initialize schema data from current metric
  if (metric.value) {
    schemaData.value = {
      table_name: metric.value.table_name,
      query: metric.value.query,
      data_source: metric.value.data_source,
      measures: metric.value.measures || [],
      dimensions: metric.value.dimensions || [],
      joins: metric.value.joins || [],
      aggregations: metric.value.aggregations || [],
      parameters: metric.value.parameters || {}
    }
  }
  // Set data source ID for schema loading
  if (parentModel.value?.data_source_id) {
    selectedDataSourceId.value = parentModel.value.data_source_id
  }
}

const onSaveSchema = async () => {
  if (!metric.value) return
  
  isSavingSchema.value = true
  try {
    // Call the backend API to update the metric
    const updatedMetric = await updateMetric(metricId, {
      table_name: schemaData.value.table_name,
      query: schemaData.value.query,
      data_source: schemaData.value.data_source,
      measures: schemaData.value.measures,
      dimensions: schemaData.value.dimensions,
      joins: schemaData.value.joins,
      aggregations: schemaData.value.aggregations,
      parameters: schemaData.value.parameters
    })
    
    if (updatedMetric) {
      // Update local state with the response from backend
      Object.assign(metric.value, updatedMetric)
      isEditingSchema.value = false
      toast.success('Schema updated successfully')
    }
  } catch (error) {
    console.error('Failed to save schema:', error)
    toast.error('Failed to save schema')
  } finally {
    isSavingSchema.value = false
  }
}

const onCancelSchemaEdit = () => {
  isEditingSchema.value = false
  // Reset schema data to original values
  if (metric.value) {
    schemaData.value = {
      table_name: metric.value.table_name,
      query: metric.value.query,
      data_source: metric.value.data_source,
      measures: metric.value.measures || [],
      dimensions: metric.value.dimensions || [],
      joins: metric.value.joins || [],
      aggregations: metric.value.aggregations || [],
      parameters: metric.value.parameters || {}
    }
  }
}

// Computed properties
const metricStatus = computed(() => {
  if (!metric.value) return 'unknown'
  // This would be determined by actual validation logic
  return 'valid' // placeholder
})

const hasParameters = computed(() => {
  return metric.value?.parameters && metric.value.parameters.length > 0
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

const formatRelativeTime = (date: string | Date) => {
  const now = new Date()
  const target = new Date(date)
  const diffMs = now.getTime() - target.getTime()
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 1) return 'just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return target.toLocaleDateString()
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
    console.log('Validation result:', result)
    // Show validation results
  } catch (error) {
    console.error('Failed to validate metric:', error)
  } finally {
    validating.value = false
  }
}

const onCompile = async () => {
  if (!metric.value) return
  
  compiling.value = true
  try {
    const result = await compileMetric(metricId)
    compiledQuery.value = (result as any)?.sql || (result as any)?.query || 'No compiled query available'
  } catch (error) {
    console.error('Failed to compile metric:', error)
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
  if (metric.value?.sql_query) {
    navigator.clipboard.writeText(metric.value.sql_query)
    // Show toast notification
  }
}

const onParameterChange = (paramName: string, value: any) => {
  executionParams.value[paramName] = value
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
  } finally {
    loading.value = false
  }
}

// Initialize parameters from metric definition
const initializeParameters = () => {
  if (metric.value?.parameters) {
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
          <div class="space-y-4">
            <div class="h-6 bg-muted rounded w-1/4 animate-pulse"></div>
            <div class="h-32 bg-muted rounded animate-pulse"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Content -->
    <div v-else-if="metric" class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <Button variant="ghost" size="sm" @click="onBack">
            <ArrowLeft class="h-4 w-4 mr-2" />
            Back to Metrics
          </Button>
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight">
              🎯 {{ metric.name }}
            </h1>
            <p class="text-sm text-muted-foreground">
              {{ metric.title || 'Metric Details' }}
            </p>
          </div>
        </div>
        
        <div class="flex items-center space-x-2">
          <Button variant="outline" size="sm" @click="onValidate" :disabled="validating">
            <Settings class="h-4 w-4 mr-2" />
            {{ validating ? 'Validating...' : 'Validate' }}
          </Button>
          <Button variant="outline" size="sm" @click="onCompile" :disabled="compiling">
            <Code class="h-4 w-4 mr-2" />
            {{ compiling ? 'Compiling...' : 'Compile' }}
          </Button>
          <Button variant="outline" size="sm" @click="onExecute" :disabled="executing">
            <PlayCircle class="h-4 w-4 mr-2" />
            {{ executing ? 'Executing...' : 'Execute' }}
          </Button>
          <Button variant="outline" size="sm" @click="onEditSchema" :disabled="isEditingSchema">
            <Edit class="h-4 w-4 mr-2" />
            Edit Schema
          </Button>
          <Button size="sm" @click="onEdit">
            <Edit class="h-4 w-4 mr-2" />
            Edit
          </Button>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="schema">Schema</TabsTrigger>
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
                  <div>{{ formatRelativeTime(metric.created_at) }}</div>
                </div>
                <div class="space-y-1">
                  <div class="text-muted-foreground">Last Updated</div>
                  <div>{{ formatRelativeTime(metric.updated_at) }}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Schema Tab -->
        <TabsContent value="schema" class="space-y-6">
          <div v-if="!isEditingSchema" class="space-y-6">
            <!-- Schema Overview -->
            <Card>
              <CardHeader>
                <CardTitle>Schema Overview</CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div class="space-y-2">
                    <div class="text-sm font-medium text-muted-foreground">Table</div>
                    <div class="text-sm font-mono">{{ metric.table_name || 'Not specified' }}</div>
                  </div>
                  <div class="space-y-2">
                    <div class="text-sm font-medium text-muted-foreground">Measures</div>
                    <div class="text-sm">{{ metric.measures?.length || 0 }}</div>
                  </div>
                  <div class="space-y-2">
                    <div class="text-sm font-medium text-muted-foreground">Dimensions</div>
                    <div class="text-sm">{{ metric.dimensions?.length || 0 }}</div>
                  </div>
                  <div class="space-y-2">
                    <div class="text-sm font-medium text-muted-foreground">Parameters</div>
                    <div class="text-sm">{{ Object.keys(metric.parameters || {}).length }}</div>
                  </div>
                </div>
                
                <div class="flex justify-end">
                  <Button @click="onEditSchema">
                    <Edit class="h-4 w-4 mr-2" />
                    Edit Schema
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- Schema Builder (when editing) -->
          <div v-else class="space-y-6">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold">Edit Metric Schema</h3>
              <div class="flex items-center space-x-2">
                <Button variant="outline" @click="onCancelSchemaEdit" :disabled="isSavingSchema">
                  Cancel
                </Button>
                <Button @click="onSaveSchema" :disabled="isSavingSchema">
                  <Save v-if="!isSavingSchema" class="h-4 w-4 mr-2" />
                  <Loader2 v-else class="h-4 w-4 mr-2 animate-spin" />
                  {{ isSavingSchema ? 'Saving...' : 'Save Schema' }}
                </Button>
              </div>
            </div>

            <MetricSchemaBuilder
              v-model="schemaData"
              :selected-data-source-id="selectedDataSourceId"
            />
          </div>
        </TabsContent>

        <!-- Query Tab -->
        <TabsContent value="query" class="space-y-6">
          <Card>
            <CardHeader class="flex flex-row items-center justify-between">
              <CardTitle>SQL Query</CardTitle>
              <Button variant="outline" size="sm" @click="onCopyQuery">
                <Copy class="h-4 w-4 mr-2" />
                Copy
              </Button>
            </CardHeader>
            <CardContent class="space-y-4">
              <div v-if="metric.sql_query" class="space-y-2">
                <div class="bg-muted p-4 rounded text-sm font-mono overflow-x-auto">
                  <pre>{{ metric.sql_query }}</pre>
                </div>
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

          <!-- Compiled Query -->
          <Card v-if="compiledQuery">
            <CardHeader>
              <CardTitle>Compiled Query</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="bg-muted p-4 rounded text-sm font-mono overflow-x-auto">
                <pre>{{ compiledQuery }}</pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Execute Tab -->
        <TabsContent value="execute" class="space-y-6">
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
              <div class="bg-muted p-4 rounded text-sm font-mono overflow-x-auto">
                <pre>{{ JSON.stringify(executionResults, null, 2) }}</pre>
              </div>
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
                    <TableCell>{{ formatRelativeTime(version.created_at) }}</TableCell>
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
  </div>
</template> 