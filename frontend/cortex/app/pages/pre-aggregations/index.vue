<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '~/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Separator } from '~/components/ui/separator'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Progress } from '~/components/ui/progress'
import { Switch } from '~/components/ui/switch'
import { Checkbox } from '~/components/ui/checkbox'
import { 
  Filter, 
  Plus, 
  MoreHorizontal, 
  PlayCircle, 
  Edit, 
  Settings, 
  Target, 
  Database, 
  Loader2, 
  RefreshCw as Refresh, 
  Clock, 
  AlertCircle, 
  CheckCircle, 
  ChevronDown,
  Trash2,
  Eye,
  Zap
} from 'lucide-vue-next'
import ExpandableSearch from '~/components/ExpandableSearch.vue'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { 
  PreAggregationSpec, 
  PreAggregationUpsertRequest, 
  PreAggregationFilters,
  TimeGrain,
  FilterOperator
} from '~/composables/usePreAggregations'
import { 
  PreAggregationType,
  RefreshType,
  PreAggregationStorageMode,
  PreAggregationBuildStrategy
} from '~/composables/usePreAggregations'
import { toast } from 'vue-sonner'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Pre-Aggregations Management',
  layout: 'default'
})

// Use composables for data management
const { specs, statuses, loading, fetchSpecs, upsertSpec, deleteSpec, refreshSpec, fetchAllStatuses, getStatusForSpec } = usePreAggregations()
const { metrics, fetchMetrics } = useMetrics()

// Component state
const searchQuery = ref('')
const selectedMetric = ref<string | null>(null)
const selectedStatus = ref<string | null>(null)
const selectedType = ref<PreAggregationType | null>(null)

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const isCreating = ref(false)
const isRefreshing = ref<Record<string, boolean>>({})
const isDryRun = ref(false)

// Form state
const specForm = ref<PreAggregationUpsertRequest>({
  name: '',
  metric_id: '',
  source: {
    data_source_id: '',
    engine: 'postgres',
    table: ''
  },
  dimensions: [],
  measures: [],
  type: PreAggregationType.ROLLUP,
  filters: [],
  partitions: undefined,
  refresh: {
    type: RefreshType.EVERY,
    every: '1h'
  },
  storage: {
    mode: PreAggregationStorageMode.SOURCE
  },
  build: {
    strategy: PreAggregationBuildStrategy.MATERIALIZED_VIEW
  }
})

const editingSpec = ref<PreAggregationSpec | null>(null)

// Form validation
const specFormErrors = ref({
  name: '',
  metric_id: '',
  dimensions: '',
  measures: ''
})

// Computed properties
const filteredSpecs = computed(() => {
  if (!specs.value || specs.value.length === 0) return []
  
  return specs.value.filter(spec => {
    const matchesSearch = !searchQuery.value || 
      spec.name?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      spec.id.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesMetric = !selectedMetric.value || 
      spec.metric_id === selectedMetric.value
    
    const status = getStatusForSpec(spec.id)
    const matchesStatus = !selectedStatus.value || 
      status?.status === selectedStatus.value
    
    const matchesType = !selectedType.value || 
      spec.type === selectedType.value
    
    return matchesSearch && matchesMetric && matchesStatus && matchesType
  })
})

const availableMetrics = computed(() => {
  return metrics.value || []
})

const selectedMetricObj = computed(() => {
  if (!specForm.value.metric_id) return null
  return availableMetrics.value.find(m => m.id === specForm.value.metric_id)
})

const availableDimensions = computed(() => {
  const metric = selectedMetricObj.value
  if (!metric?.dimensions) return []
  return metric.dimensions.map((d: any) => ({
    name: d.name,
    description: d.description,
    query: d.query || d.name,
    table: d.table,
    formatting: d.formatting
  }))
})

const availableMeasures = computed(() => {
  const metric = selectedMetricObj.value
  if (!metric?.measures) return []
  return metric.measures.map((m: any) => ({
    name: m.name,
    description: m.description,
    type: m.type,
    formatting: m.formatting,
    alias: m.alias,
    query: m.query || m.name,
    table: m.table
  }))
})

// Form validation computed
const isSpecFormValid = computed(() => {
  return specForm.value.metric_id !== '' &&
         specForm.value.dimensions.length > 0 &&
         specForm.value.measures.length > 0 &&
         !specFormErrors.value.metric_id &&
         !specFormErrors.value.dimensions &&
         !specFormErrors.value.measures
})

// Utility functions
const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case 'completed': return 'default'
    case 'building': return 'secondary'
    case 'failed': return 'destructive'
    case 'pending': return 'outline'
    default: return 'outline'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed': return CheckCircle
    case 'building': return Loader2
    case 'failed': return AlertCircle
    case 'pending': return Clock
    default: return Clock
  }
}

const getTypeIcon = (type: PreAggregationType) => {
  switch (type) {
    case PreAggregationType.ROLLUP: return Database
    case PreAggregationType.ORIGINAL_SQL: return Target
    case PreAggregationType.ROLLUP_LAMBDA: return Zap
    default: return Database
  }
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Get user's locale from browser
const { language } = useNavigatorLanguage()

// Helper function to convert UTC date string to local timezone
const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

// Format relative time using VueUse
const formatRelativeTime = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, { 
    updateInterval: 1000
  })
}

// Format absolute date using VueUse
const formatAbsoluteDate = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useDateFormat(localDate, 'MMM D, YYYY HH:mm', { 
    locales: language.value || 'en-US' 
  })
}

// Event handlers
const onSpecClick = (specId: string) => {
  navigateTo(`/pre-aggregations/${specId}`)
}

const onCreateSpec = () => {
  editingSpec.value = null
  resetSpecForm()
  showCreateDialog.value = true
}

const onEditSpec = (spec: PreAggregationSpec) => {
  editingSpec.value = spec
  populateFormFromSpec(spec)
  showEditDialog.value = true
}

const onDeleteSpec = async (specId: string) => {
  if (confirm('Are you sure you want to delete this pre-aggregation spec?')) {
    const success = await deleteSpec(specId)
    if (success) {
      toast.success('Pre-aggregation spec deleted successfully')
    } else {
      toast.error('Failed to delete pre-aggregation spec')
    }
  }
}

const onRefreshSpec = async (specId: string, dryRun: boolean = false) => {
  isRefreshing.value[specId] = true
  try {
    const result = await refreshSpec(specId, dryRun)
    if (dryRun) {
      toast.success(`Dry run completed: ${result.preview || 'Ready to build'}`)
    } else {
      toast.success('Pre-aggregation refresh started')
      // Refresh statuses after a delay
      setTimeout(fetchAllStatuses, 1000)
    }
  } catch (error) {
    toast.error(`Failed to ${dryRun ? 'preview' : 'refresh'} pre-aggregation`)
  } finally {
    isRefreshing.value[specId] = false
  }
}

// Form handlers
const resetSpecForm = () => {
  specForm.value = {
    name: '',
    metric_id: '',
    source: {
      data_source_id: '',
      engine: 'postgres',
      table: ''
    },
    dimensions: [],
    measures: [],
    type: PreAggregationType.ROLLUP,
    filters: [],
    partitions: undefined,
    refresh: {
      type: RefreshType.EVERY,
      every: '1h'
    },
    storage: {
      mode: PreAggregationStorageMode.SOURCE
    },
    build: {
      strategy: PreAggregationBuildStrategy.MATERIALIZED_VIEW
    }
  }
  specFormErrors.value = {
    name: '',
    metric_id: '',
    dimensions: '',
    measures: ''
  }
}

const populateFormFromSpec = (spec: PreAggregationSpec) => {
  specForm.value = {
    id: spec.id,
    name: spec.name || '',
    metric_id: spec.metric_id,
    source: { ...spec.source },
    dimensions: [...spec.dimensions],
    measures: [...spec.measures],
    type: spec.type,
    filters: spec.filters ? [...spec.filters] : [],
    partitions: spec.partitions ? { ...spec.partitions } : undefined,
    refresh: spec.refresh ? { ...spec.refresh } : {
      type: RefreshType.EVERY,
      every: '1h'
    },
    storage: spec.storage ? { ...spec.storage } : {
      mode: PreAggregationStorageMode.SOURCE
    },
    build: spec.build ? { ...spec.build } : {
      strategy: PreAggregationBuildStrategy.MATERIALIZED_VIEW
    }
  }
}

const generateSpecId = () => {
  return crypto.randomUUID()
}

const populateSourceFromMetric = (metric: any) => {
  if (metric?.data_source) {
    specForm.value.source = {
      data_source_id: metric.data_source.id || metric.data_source_id,
      engine: metric.data_source.engine || 'postgres',
      schema: metric.data_source.schema,
      table: metric.table_name || metric.name
    }
  }
}

const handleCreateSpec = async () => {
  if (!isSpecFormValid.value) {
    validateForm()
    return
  }

  isCreating.value = true
  try {
    // Generate ID for new spec
    const specData = {
      ...specForm.value,
      id: generateSpecId()
    }
    
    // Populate source from selected metric
    const selectedMetric = availableMetrics.value.find(m => m.id === specForm.value.metric_id)
    if (selectedMetric) {
      populateSourceFromMetric(selectedMetric)
      specData.source = specForm.value.source
    }
    
    const createdSpec = await upsertSpec(specData)
    if (createdSpec) {
      showCreateDialog.value = false
      showEditDialog.value = false
      resetSpecForm()
      toast.success('Pre-aggregation spec created successfully')
      // Refresh statuses
      await fetchAllStatuses()
    }
  } catch (error) {
    console.error('Failed to create spec:', error)
    toast.error('Failed to create pre-aggregation spec')
  } finally {
    isCreating.value = false
  }
}

const handleUpdateSpec = async () => {
  if (!isSpecFormValid.value) {
    validateForm()
    return
  }

  isCreating.value = true
  try {
    const updatedSpec = await upsertSpec(specForm.value)
    if (updatedSpec) {
      showEditDialog.value = false
      resetSpecForm()
      toast.success('Pre-aggregation spec updated successfully')
      // Refresh statuses
      await fetchAllStatuses()
    }
  } catch (error) {
    console.error('Failed to update spec:', error)
    toast.error('Failed to update pre-aggregation spec')
  } finally {
    isCreating.value = false
  }
}

const validateForm = () => {
  if (!specForm.value.metric_id) {
    specFormErrors.value.metric_id = 'Metric is required'
  }
  if (specForm.value.dimensions.length === 0) {
    specFormErrors.value.dimensions = 'At least one dimension is required'
  }
  if (specForm.value.measures.length === 0) {
    specFormErrors.value.measures = 'At least one measure is required'
  }
}

const onDimensionToggle = (dimension: any, checked: boolean | "indeterminate") => {
  if (checked === true) {
    const exists = specForm.value.dimensions.find(d => d.name === dimension.name)
    if (!exists) {
      specForm.value.dimensions.push(dimension)
    }
  } else {
    specForm.value.dimensions = specForm.value.dimensions.filter(d => d.name !== dimension.name)
  }
  specFormErrors.value.dimensions = ''
}

const onMeasureToggle = (measure: any, checked: boolean | "indeterminate") => {
  if (checked === true) {
    const exists = specForm.value.measures.find(m => m.name === measure.name)
    if (!exists) {
      specForm.value.measures.push(measure)
    }
  } else {
    specForm.value.measures = specForm.value.measures.filter(m => m.name !== measure.name)
  }
  specFormErrors.value.measures = ''
}

// Watch for form changes
watch(() => specForm.value.metric_id, (newMetricId, oldMetricId) => {
  specFormErrors.value.metric_id = ''
  
  // Populate source from selected metric
  if (newMetricId) {
    const selectedMetric = availableMetrics.value.find(m => m.id === newMetricId)
    if (selectedMetric) {
      populateSourceFromMetric(selectedMetric)
    }
  }
  
  // Only reset dimensions and measures when metric actually changes (not on initial load or when going from empty to value)
  if (oldMetricId && newMetricId && newMetricId !== oldMetricId) {
    specForm.value.dimensions = []
    specForm.value.measures = []
  }
})

// Initialize data
onMounted(async () => {
  await Promise.all([
    fetchSpecs(),
    fetchMetrics()
  ])
  await fetchAllStatuses()
})

// Auto-refresh statuses every 30 seconds
let statusInterval: NodeJS.Timeout | null = null
onMounted(() => {
  statusInterval = setInterval(fetchAllStatuses, 30000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div class="space-y-1">
        <h2 class="text-2xl font-semibold tracking-tight">⚡ Pre-Aggregations</h2>
        <p class="text-sm text-muted-foreground">
          Manage materialized rollups and pre-computed aggregations for faster query performance
        </p>
      </div>
      
      <div class="flex items-center space-x-2">
        <Button variant="outline" size="sm" @click="fetchAllStatuses">
          <Refresh class="h-4 w-4 mr-2" />
          Refresh Status
        </Button>
        
        <Button size="sm" @click="onCreateSpec">
          <Plus class="h-4 w-4 mr-2" />
          Create Pre-Aggregation
        </Button>
      </div>
    </div>

    <!-- Filters and Search -->
    <Card>
      <CardContent class="pt-6">
        <div class="flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4">
          <!-- Search -->
          <ExpandableSearch
            v-model="searchQuery"
            :placeholder="['Search pre-aggregations...', 'Search by name...']"
            default-mode="minimal"
            full-width="350px"
            :expand-on-focus="true"
            expand-to="full"
          />
          
          <!-- Metric Filter -->
          <Select v-model="selectedMetric">
            <SelectTrigger class="w-[200px]">
              <SelectValue placeholder="All Metrics" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">All Metrics</SelectItem>
              <SelectItem v-for="metric in availableMetrics" :key="metric.id" :value="metric.id">
                {{ metric.title || metric.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          
          <!-- Status Filter -->
          <Select v-model="selectedStatus">
            <SelectTrigger class="w-[140px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="building">Building</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>

          <!-- Type Filter -->
          <Select v-model="selectedType">
            <SelectTrigger class="w-[140px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">All Types</SelectItem>
              <SelectItem :value="PreAggregationType.ROLLUP">Rollup</SelectItem>
              <SelectItem :value="PreAggregationType.ORIGINAL_SQL">Original SQL</SelectItem>
              <SelectItem :value="PreAggregationType.ROLLUP_LAMBDA">Rollup Lambda</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- Pre-Aggregations List -->
    <div v-if="loading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card v-for="i in 6" :key="i" class="animate-pulse">
        <CardHeader class="space-y-2">
          <div class="h-4 bg-muted rounded w-3/4"></div>
          <div class="h-3 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div class="h-3 bg-muted rounded"></div>
            <div class="h-8 bg-muted rounded"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div v-else-if="!specs || specs.length === 0" class="text-center py-12">
      <Database class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-medium text-muted-foreground mb-2">No pre-aggregations found</h3>
      <p class="text-sm text-muted-foreground mb-4">
        Create your first pre-aggregation to improve query performance
      </p>
      <Button @click="onCreateSpec">
        <Plus class="h-4 w-4 mr-2" />
        Create Pre-Aggregation
      </Button>
    </div>

    <div v-else-if="filteredSpecs.length === 0" class="text-center py-12">
      <Database class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-medium text-muted-foreground mb-2">No pre-aggregations match your filters</h3>
      <p class="text-sm text-muted-foreground mb-4">
        Try adjusting your search or filter criteria
      </p>
      <Button variant="outline" @click="searchQuery = ''; selectedMetric = null; selectedStatus = null; selectedType = null">
        Clear Filters
      </Button>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card 
        v-for="spec in filteredSpecs" 
        :key="spec.id" 
        class="hover:shadow-md transition-shadow cursor-pointer"
        @click="onSpecClick(spec.id)"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="space-y-1 flex-1">
              <CardTitle class="text-base font-medium flex items-center space-x-2">
                <component :is="getTypeIcon(spec.type)" class="h-4 w-4" />
                <span>{{ spec.name || `Spec ${spec.id?.slice(0, 8) || 'unknown'}` }}</span>
              </CardTitle>
              <p class="text-sm text-muted-foreground">
                {{ spec.type }} • {{ spec.dimensions?.length || 0 }} dims • {{ spec.measures?.length || 0 }} measures
              </p>
            </div>
            <div class="flex flex-col items-end space-y-1">
              <Badge 
                :variant="getStatusBadgeVariant(getStatusForSpec(spec.id)?.status || 'pending')"
                class="flex items-center space-x-1"
              >
                <component :is="getStatusIcon(getStatusForSpec(spec.id)?.status || 'pending')" class="h-3 w-3" />
                <span>{{ getStatusForSpec(spec.id)?.status || 'pending' }}</span>
              </Badge>
            </div>
          </div>
        </CardHeader>
        
        <CardContent class="pt-0">
          <div class="space-y-3">
            <!-- Spec Info -->
            <div class="flex items-center justify-between text-sm">
              <div class="flex items-center space-x-2 text-muted-foreground">
                <Target class="h-3 w-3" />
                <span>{{ availableMetrics.find(m => m.id === spec.metric_id)?.name || 'Unknown Metric' }}</span>
              </div>
            </div>
            
            <!-- Status Details -->
            <div v-if="getStatusForSpec(spec.id)" class="space-y-2">
              <div v-if="getStatusForSpec(spec.id)?.row_count" class="flex items-center justify-between text-sm">
                <span class="text-muted-foreground">Rows:</span>
                <span>{{ getStatusForSpec(spec.id)?.row_count?.toLocaleString() }}</span>
              </div>
              
              <div v-if="getStatusForSpec(spec.id)?.storage_size_bytes" class="flex items-center justify-between text-sm">
                <span class="text-muted-foreground">Size:</span>
                <span>{{ formatBytes(getStatusForSpec(spec.id)?.storage_size_bytes || 0) }}</span>
              </div>
              
              <div v-if="getStatusForSpec(spec.id)?.last_built_at" class="flex items-center justify-between text-sm">
                <span class="text-muted-foreground">Last Built:</span>
                <span>{{ formatRelativeTime(getStatusForSpec(spec.id)?.last_built_at || '') }}</span>
              </div>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-xs text-muted-foreground">
                {{ formatRelativeTime(spec.updated_at) }}
              </span>
            </div>
            
            <Separator />
            
            <!-- Actions -->
            <div class="flex items-center justify-between">
              <div class="flex space-x-1">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  @click.stop="onRefreshSpec(spec.id, true)"
                  :disabled="isRefreshing[spec.id]"
                  title="Dry Run"
                >
                  <Eye class="h-3 w-3" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  @click.stop="onRefreshSpec(spec.id, false)"
                  :disabled="isRefreshing[spec.id]"
                  title="Refresh"
                >
                  <component :is="isRefreshing[spec.id] ? Loader2 : Refresh" 
                    :class="['h-3 w-3', isRefreshing[spec.id] ? 'animate-spin' : '']" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  @click.stop="onEditSpec(spec)"
                  title="Edit"
                >
                  <Edit class="h-3 w-3" />
                </Button>
              </div>
              
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button variant="ghost" size="sm" @click.stop>
                    <MoreHorizontal class="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="onSpecClick(spec.id)" class="cursor-pointer">
                    <Eye class="h-4 w-4 mr-2" />
                    View Details
                  </DropdownMenuItem>
                  <DropdownMenuItem @click="onEditSpec(spec)" class="cursor-pointer">
                    <Edit class="h-4 w-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem @click="onDeleteSpec(spec.id)" class="cursor-pointer text-red-600">
                    <Trash2 class="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            
            <!-- Error Message -->
            <Alert v-if="getStatusForSpec(spec.id)?.status === 'failed'" variant="destructive" class="mt-2">
              <AlertCircle class="h-4 w-4" />
              <AlertDescription>
                {{ getStatusForSpec(spec.id)?.error_message || 'Build failed' }}
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Create/Edit Dialog -->
    <Dialog v-model:open="showCreateDialog" v-if="!showEditDialog">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle class="flex items-center space-x-2">
            <Database class="h-5 w-5" />
            <span>Create Pre-Aggregation</span>
          </DialogTitle>
          <DialogDescription>
            Create a new pre-aggregation to improve query performance through materialized rollups.
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4 py-4 max-h-[500px] overflow-y-auto">
          <!-- Basic Info -->
          <div class="space-y-4">
            <div class="space-y-2">
              <Label for="spec-name">Name (Optional)</Label>
              <Input
                id="spec-name"
                v-model="specForm.name"
                placeholder="Pre-aggregation name"
                :disabled="isCreating"
              />
            </div>
            
            <div class="space-y-2">
              <Label for="spec-metric">Metric *</Label>
              <Select v-model="specForm.metric_id" :disabled="isCreating">
                <SelectTrigger>
                  <SelectValue placeholder="Select a metric" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="metric in availableMetrics" :key="metric.id" :value="metric.id">
                    {{ metric.title || metric.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p v-if="specFormErrors.metric_id" class="text-sm text-red-500">{{ specFormErrors.metric_id }}</p>
            </div>

            <div class="space-y-2">
              <Label for="spec-type">Type</Label>
              <Select v-model="specForm.type" :disabled="isCreating">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="PreAggregationType.ROLLUP">Rollup</SelectItem>
                  <SelectItem :value="PreAggregationType.ORIGINAL_SQL">Original SQL</SelectItem>
                  <SelectItem :value="PreAggregationType.ROLLUP_LAMBDA">Rollup Lambda</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <!-- Dimensions -->
          <div v-if="availableDimensions.length > 0" class="space-y-2">
            <Label>Dimensions *</Label>
            <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded p-2">
              <div v-for="dimension in availableDimensions" :key="dimension.name" class="flex items-center space-x-2">
                <Checkbox 
                  :id="`dim-${dimension.name}`"
                  :model-value="specForm.dimensions.some(d => d.name === dimension.name)"
                  @update:model-value="(checked: boolean | 'indeterminate') => onDimensionToggle(dimension, checked)"
                  :disabled="isCreating"

                />
                <Label :for="`dim-${dimension.name}`" class="text-sm">{{ dimension.name }}</Label>
              </div>
            </div>
            <p v-if="specFormErrors.dimensions" class="text-sm text-red-500">{{ specFormErrors.dimensions }}</p>
          </div>

          <!-- Measures -->
          <div v-if="availableMeasures.length > 0" class="space-y-2">
            <Label>Measures *</Label>
            <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded p-2">
              <div v-for="measure in availableMeasures" :key="measure.name" class="flex items-center space-x-2">
                <Checkbox 
                  :id="`meas-${measure.name}`"
                  :model-value="specForm.measures.some(m => m.name === measure.name)"
                  @update:model-value="(checked: boolean | 'indeterminate') => onMeasureToggle(measure, checked)"
                  :disabled="isCreating"

                />
                <Label :for="`meas-${measure.name}`" class="text-sm">{{ measure.name }}</Label>
              </div>
            </div>
            <p v-if="specFormErrors.measures" class="text-sm text-red-500">{{ specFormErrors.measures }}</p>
          </div>

          <!-- Refresh Policy -->
          <div class="space-y-2">
            <Label>Refresh Policy</Label>
            <div class="flex items-center space-x-2">
              <Select v-model="specForm.refresh!.type" :disabled="isCreating">
                <SelectTrigger class="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="RefreshType.EVERY">Every</SelectItem>
                  <SelectItem :value="RefreshType.SQL">SQL</SelectItem>
                  <SelectItem :value="RefreshType.MAX">Max</SelectItem>
                </SelectContent>
              </Select>
              <Input 
                v-if="specForm.refresh!.type === RefreshType.EVERY"
                v-model="specForm.refresh!.every"
                placeholder="1h, 30m, 1d"
                class="flex-1"
                :disabled="isCreating"
              />
              <Textarea 
                v-else-if="specForm.refresh!.type === RefreshType.SQL"
                v-model="specForm.refresh!.sql"
                placeholder="SELECT MAX(updated_at) FROM table"
                class="flex-1"
                :disabled="isCreating"
              />
              <Input 
                v-else-if="specForm.refresh!.type === RefreshType.MAX"
                v-model="specForm.refresh!.max"
                placeholder="7d, 30d"
                class="flex-1"
                :disabled="isCreating"
              />
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button
            variant="outline"
            @click="showCreateDialog = false"
            :disabled="isCreating"
          >
            Cancel
          </Button>
          <Button
            @click="handleCreateSpec"
            :disabled="!isSpecFormValid || isCreating"
          >
            <Loader2 v-if="isCreating" class="h-4 w-4 mr-2 animate-spin" />
            Create Pre-Aggregation
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Edit Dialog (similar structure but calls handleUpdateSpec) -->
    <Dialog v-model:open="showEditDialog" v-if="!showCreateDialog">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle class="flex items-center space-x-2">
            <Edit class="h-5 w-5" />
            <span>Edit Pre-Aggregation</span>
          </DialogTitle>
          <DialogDescription>
            Update the pre-aggregation configuration.
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4 py-4 max-h-[500px] overflow-y-auto">
          <!-- Same form structure as create dialog -->
          <div class="space-y-4">
            <div class="space-y-2">
              <Label for="edit-spec-name">Name (Optional)</Label>
              <Input
                id="edit-spec-name"
                v-model="specForm.name"
                placeholder="Pre-aggregation name"
                :disabled="isCreating"
              />
            </div>
            
            <div class="space-y-2">
              <Label for="edit-spec-metric">Metric *</Label>
              <Select v-model="specForm.metric_id" :disabled="isCreating">
                <SelectTrigger>
                  <SelectValue placeholder="Select a metric" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="metric in availableMetrics" :key="metric.id" :value="metric.id">
                    {{ metric.title || metric.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p v-if="specFormErrors.metric_id" class="text-sm text-red-500">{{ specFormErrors.metric_id }}</p>
            </div>

            <div class="space-y-2">
              <Label for="edit-spec-type">Type</Label>
              <Select v-model="specForm.type" :disabled="isCreating">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="PreAggregationType.ROLLUP">Rollup</SelectItem>
                  <SelectItem :value="PreAggregationType.ORIGINAL_SQL">Original SQL</SelectItem>
                  <SelectItem :value="PreAggregationType.ROLLUP_LAMBDA">Rollup Lambda</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <!-- Dimensions -->
          <div v-if="availableDimensions.length > 0" class="space-y-2">
            <Label>Dimensions *</Label>
            <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded p-2">
              <div v-for="dimension in availableDimensions" :key="dimension.name" class="flex items-center space-x-2">
                <Checkbox 
                  :id="`edit-dim-${dimension.name}`"
                  :model-value="specForm.dimensions.some(d => d.name === dimension.name)"
                  @update:model-value="(checked: boolean | 'indeterminate') => onDimensionToggle(dimension, checked)"
                  :disabled="isCreating"
                />
                <Label :for="`edit-dim-${dimension.name}`" class="text-sm">{{ dimension.name }}</Label>
              </div>
            </div>
            <p v-if="specFormErrors.dimensions" class="text-sm text-red-500">{{ specFormErrors.dimensions }}</p>
          </div>

          <!-- Measures -->
          <div v-if="availableMeasures.length > 0" class="space-y-2">
            <Label>Measures *</Label>
            <div class="grid grid-cols-2 gap-2 max-h-32 overflow-y-auto border rounded p-2">
              <div v-for="measure in availableMeasures" :key="measure.name" class="flex items-center space-x-2">
                <Checkbox 
                  :id="`edit-meas-${measure.name}`"
                  :model-value="specForm.measures.some(m => m.name === measure.name)"
                  @update:model-value="(checked: boolean | 'indeterminate') => onMeasureToggle(measure, checked)"
                  :disabled="isCreating"
                />
                <Label :for="`edit-meas-${measure.name}`" class="text-sm">{{ measure.name }}</Label>
              </div>
            </div>
            <p v-if="specFormErrors.measures" class="text-sm text-red-500">{{ specFormErrors.measures }}</p>
          </div>

          <!-- Refresh Policy -->
          <div class="space-y-2">
            <Label>Refresh Policy</Label>
            <div class="flex items-center space-x-2">
              <Select v-model="specForm.refresh!.type" :disabled="isCreating">
                <SelectTrigger class="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="RefreshType.EVERY">Every</SelectItem>
                  <SelectItem :value="RefreshType.SQL">SQL</SelectItem>
                  <SelectItem :value="RefreshType.MAX">Max</SelectItem>
                </SelectContent>
              </Select>
              <Input 
                v-if="specForm.refresh!.type === RefreshType.EVERY"
                v-model="specForm.refresh!.every"
                placeholder="1h, 30m, 1d"
                class="flex-1"
                :disabled="isCreating"
              />
              <Textarea 
                v-else-if="specForm.refresh!.type === RefreshType.SQL"
                v-model="specForm.refresh!.sql"
                placeholder="SELECT MAX(updated_at) FROM table"
                class="flex-1"
                :disabled="isCreating"
              />
              <Input 
                v-else-if="specForm.refresh!.type === RefreshType.MAX"
                v-model="specForm.refresh!.max"
                placeholder="7d, 30d"
                class="flex-1"
                :disabled="isCreating"
              />
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button
            variant="outline"
            @click="showEditDialog = false"
            :disabled="isCreating"
          >
            Cancel
          </Button>
          <Button
            @click="handleUpdateSpec"
            :disabled="!isSpecFormValid || isCreating"
          >
            <Loader2 v-if="isCreating" class="h-4 w-4 mr-2 animate-spin" />
            Update Pre-Aggregation
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
