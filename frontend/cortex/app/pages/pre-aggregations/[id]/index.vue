<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Separator } from '~/components/ui/separator'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { 
  ArrowLeft,
  Edit, 
  Settings, 
  Target, 
  Database, 
  Loader2, 
  RefreshCw as Refresh, 
  Clock, 
  AlertCircle, 
  CheckCircle, 
  Trash2,
  Eye,
  Zap,
  PlayCircle,
  BarChart3,
  Code,
  Info
} from 'lucide-vue-next'
import type { 
  PreAggregationSpec, 
  PreAggregationUpsertRequest,
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
  title: 'Pre-Aggregation Details',
  layout: 'default'
})

// Get route params
const route = useRoute()
const specId = route.params.id as string

// Use composables for data management
const { specs, statuses, loading, fetchSpecs, upsertSpec, deleteSpec, refreshSpec, fetchAllStatuses, getStatusForSpec } = usePreAggregations()
const { metrics, fetchMetrics } = useMetrics()

// Component state
const isEditing = ref(false)
const isRefreshing = ref(false)
const isDeleting = ref(false)
const showDeleteDialog = ref(false)

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

// Form validation
const specFormErrors = ref({
  name: '',
  metric_id: '',
  dimensions: '',
  measures: ''
})

// Computed properties
const currentSpec = computed(() => {
  return specs.value.find(s => s.id === specId)
})

const currentStatus = computed(() => {
  return getStatusForSpec(specId)
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
  return metric.dimensions.map((d: any) => d.name || d.query || d.id)
})

const availableMeasures = computed(() => {
  const metric = selectedMetricObj.value
  if (!metric?.measures) return []
  return metric.measures.map((m: any) => m.name || m.query || m.id)
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
const onEdit = () => {
  if (currentSpec.value) {
    populateFormFromSpec(currentSpec.value)
    isEditing.value = true
  }
}

const onCancelEdit = () => {
  isEditing.value = false
  resetSpecForm()
}

const onSave = async () => {
  if (!isSpecFormValid.value) {
    validateForm()
    return
  }

  try {
    const updatedSpec = await upsertSpec(specForm.value)
    if (updatedSpec) {
      isEditing.value = false
      toast.success('Pre-aggregation updated successfully')
      await fetchAllStatuses()
    }
  } catch (error) {
    console.error('Failed to update spec:', error)
    toast.error('Failed to update pre-aggregation')
  }
}

const onDelete = async () => {
  isDeleting.value = true
  try {
    const success = await deleteSpec(specId)
    if (success) {
      toast.success('Pre-aggregation deleted successfully')
      navigateTo('/pre-aggregations')
    } else {
      toast.error('Failed to delete pre-aggregation')
    }
  } catch (error) {
    console.error('Failed to delete spec:', error)
    toast.error('Failed to delete pre-aggregation')
  } finally {
    isDeleting.value = false
    showDeleteDialog.value = false
  }
}

const onRefresh = async (dryRun: boolean = false) => {
  isRefreshing.value = true
  try {
    const result = await refreshSpec(specId, dryRun)
    if (dryRun) {
      toast.success(`Dry run completed: ${result.preview || 'Ready to build'}`)
    } else {
      toast.success('Pre-aggregation refresh started')
      setTimeout(fetchAllStatuses, 1000)
    }
  } catch (error) {
    toast.error(`Failed to ${dryRun ? 'preview' : 'refresh'} pre-aggregation`)
  } finally {
    isRefreshing.value = false
  }
}

// Form handlers
const resetSpecForm = () => {
  if (currentSpec.value) {
    populateFormFromSpec(currentSpec.value)
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

const onDimensionToggle = (dimension: string, checked: boolean | undefined) => {
  if (checked) {
    if (!specForm.value.dimensions.includes(dimension)) {
      specForm.value.dimensions.push(dimension)
    }
  } else {
    specForm.value.dimensions = specForm.value.dimensions.filter(d => d !== dimension)
  }
  specFormErrors.value.dimensions = ''
}

const onMeasureToggle = (measure: string, checked: boolean | undefined) => {
  if (checked) {
    if (!specForm.value.measures.includes(measure)) {
      specForm.value.measures.push(measure)
    }
  } else {
    specForm.value.measures = specForm.value.measures.filter(m => m !== measure)
  }
  specFormErrors.value.measures = ''
}

// Watch for form changes
watch(() => specForm.value.metric_id, () => {
  specFormErrors.value.metric_id = ''
  // Reset dimensions and measures when metric changes
  specForm.value.dimensions = []
  specForm.value.measures = []
})

// Initialize data
onMounted(async () => {
  await Promise.all([
    fetchSpecs(),
    fetchMetrics()
  ])
  await fetchAllStatuses()
  
  // Populate form with current spec data
  if (currentSpec.value) {
    populateFormFromSpec(currentSpec.value)
  }
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
      <div class="flex items-center space-x-4">
        <Button variant="ghost" size="sm" @click="navigateTo('/pre-aggregations')">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Pre-Aggregations
        </Button>
        
        <div class="space-y-1">
          <h2 class="text-2xl font-semibold tracking-tight flex items-center space-x-2">
            <component :is="getTypeIcon(currentSpec?.type || PreAggregationType.ROLLUP)" class="h-6 w-6" />
            <span>{{ currentSpec?.name || `Pre-Aggregation ${specId?.slice(0, 8) || 'unknown'}` }}</span>
          </h2>
          <p class="text-sm text-muted-foreground">
            {{ currentSpec?.type || 'rollup' }} • {{ currentSpec?.dimensions?.length || 0 }} dimensions • {{ currentSpec?.measures?.length || 0 }} measures
          </p>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <Button 
          variant="outline" 
          size="sm" 
          @click="onRefresh(true)"
          :disabled="isRefreshing"
        >
          <Eye class="h-4 w-4 mr-2" />
          Dry Run
        </Button>
        
        <Button 
          variant="outline" 
          size="sm" 
          @click="onRefresh(false)"
          :disabled="isRefreshing"
        >
          <component :is="isRefreshing ? Loader2 : Refresh" 
            :class="['h-4 w-4 mr-2', isRefreshing ? 'animate-spin' : '']" />
          Refresh
        </Button>
        
        <Button 
          v-if="!isEditing" 
          size="sm" 
          @click="onEdit"
        >
          <Edit class="h-4 w-4 mr-2" />
          Edit
        </Button>
        
        <Button 
          v-if="isEditing" 
          variant="outline" 
          size="sm" 
          @click="onCancelEdit"
        >
          Cancel
        </Button>
        
        <Button 
          v-if="isEditing" 
          size="sm" 
          @click="onSave"
          :disabled="!isSpecFormValid"
        >
          Save Changes
        </Button>
        
        <Button 
          variant="destructive" 
          size="sm" 
          @click="showDeleteDialog = true"
        >
          <Trash2 class="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <Card class="animate-pulse">
        <CardHeader>
          <div class="h-6 bg-muted rounded w-1/3"></div>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div class="h-4 bg-muted rounded w-1/2"></div>
            <div class="h-4 bg-muted rounded w-3/4"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Not Found State -->
    <div v-else-if="!currentSpec" class="text-center py-12">
      <AlertCircle class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-medium text-muted-foreground mb-2">Pre-aggregation not found</h3>
      <p class="text-sm text-muted-foreground mb-4">
        The pre-aggregation you're looking for doesn't exist or has been deleted.
      </p>
      <Button @click="navigateTo('/pre-aggregations')">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Pre-Aggregations
      </Button>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-6">
      <!-- Status Card -->
      <Card>
        <CardHeader>
          <CardTitle class="flex items-center space-x-2">
            <component :is="getStatusIcon(currentStatus?.status || 'pending')" class="h-5 w-5" />
            <span>Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="space-y-2">
              <Label class="text-sm font-medium">Current Status</Label>
              <Badge :variant="getStatusBadgeVariant(currentStatus?.status || 'pending')" class="flex items-center space-x-1 w-fit">
                <component :is="getStatusIcon(currentStatus?.status || 'pending')" class="h-3 w-3" />
                <span>{{ currentStatus?.status || 'pending' }}</span>
              </Badge>
            </div>
            
            <div v-if="currentStatus?.row_count" class="space-y-2">
              <Label class="text-sm font-medium">Row Count</Label>
              <p class="text-sm">{{ currentStatus.row_count.toLocaleString() }}</p>
            </div>
            
            <div v-if="currentStatus?.storage_size_bytes" class="space-y-2">
              <Label class="text-sm font-medium">Storage Size</Label>
              <p class="text-sm">{{ formatBytes(currentStatus.storage_size_bytes) }}</p>
            </div>
            
            <div v-if="currentStatus?.last_built_at" class="space-y-2">
              <Label class="text-sm font-medium">Last Built</Label>
              <p class="text-sm">{{ formatRelativeTime(currentStatus.last_built_at) }}</p>
            </div>
          </div>
          
          <!-- Error Message -->
          <Alert v-if="currentStatus?.status === 'failed'" variant="destructive" class="mt-4">
            <AlertCircle class="h-4 w-4" />
            <AlertDescription>
              {{ currentStatus?.error_message || 'Build failed' }}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <!-- Tabs for different views -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-4">
          <div class="grid gap-4 md:grid-cols-2">
            <!-- Basic Info -->
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center space-x-2">
                  <Info class="h-5 w-5" />
                  <span>Basic Information</span>
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Name</Label>
                  <p class="text-sm">{{ currentSpec.name || 'Unnamed' }}</p>
                </div>
                
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Type</Label>
                  <div class="flex items-center space-x-2">
                    <component :is="getTypeIcon(currentSpec.type)" class="h-4 w-4" />
                    <span class="text-sm">{{ currentSpec.type }}</span>
                  </div>
                </div>
                
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Metric</Label>
                  <p class="text-sm">{{ availableMetrics.find(m => m.id === currentSpec?.metric_id)?.name || 'Unknown' }}</p>
                </div>
                
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Created</Label>
                  <p class="text-sm">{{ formatAbsoluteDate(currentSpec.created_at) }}</p>
                </div>
                
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Last Updated</Label>
                  <p class="text-sm">{{ formatAbsoluteDate(currentSpec.updated_at) }}</p>
                </div>
              </CardContent>
            </Card>

            <!-- Dimensions & Measures -->
            <Card>
              <CardHeader>
                <CardTitle class="flex items-center space-x-2">
                  <BarChart3 class="h-5 w-5" />
                  <span>Dimensions & Measures</span>
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Dimensions ({{ currentSpec.dimensions.length }})</Label>
                  <div class="flex flex-wrap gap-1">
                    <Badge v-for="dimension in currentSpec.dimensions" :key="dimension" variant="secondary" class="text-xs">
                      {{ dimension }}
                    </Badge>
                  </div>
                </div>
                
                <div class="space-y-2">
                  <Label class="text-sm font-medium">Measures ({{ currentSpec.measures.length }})</Label>
                  <div class="flex flex-wrap gap-1">
                    <Badge v-for="measure in currentSpec.measures" :key="measure" variant="outline" class="text-xs">
                      {{ measure }}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <!-- Configuration Tab -->
        <TabsContent value="configuration" class="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <Settings class="h-5 w-5" />
                <span>Configuration</span>
              </CardTitle>
            </CardHeader>
            <CardContent class="space-y-6">
              <!-- Refresh Policy -->
              <div class="space-y-2">
                <Label class="text-sm font-medium">Refresh Policy</Label>
                <div class="p-3 bg-muted rounded-md">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm font-medium">{{ currentSpec.refresh?.type || 'every' }}</span>
                    <span v-if="currentSpec.refresh?.every" class="text-sm">{{ currentSpec.refresh.every }}</span>
                    <span v-if="currentSpec.refresh?.sql" class="text-sm font-mono">{{ currentSpec.refresh.sql }}</span>
                    <span v-if="currentSpec.refresh?.max" class="text-sm">{{ currentSpec.refresh.max }}</span>
                  </div>
                </div>
              </div>

              <!-- Storage Configuration -->
              <div class="space-y-2">
                <Label class="text-sm font-medium">Storage</Label>
                <div class="p-3 bg-muted rounded-md">
                  <div class="flex items-center space-x-2">
                    <Database class="h-4 w-4" />
                    <span class="text-sm">{{ currentSpec.storage?.mode || 'source' }}</span>
                  </div>
                </div>
              </div>

              <!-- Build Strategy -->
              <div class="space-y-2">
                <Label class="text-sm font-medium">Build Strategy</Label>
                <div class="p-3 bg-muted rounded-md">
                  <div class="flex items-center space-x-2">
                    <Code class="h-4 w-4" />
                    <span class="text-sm">{{ currentSpec.build?.strategy || 'mv' }}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Details Tab -->
        <TabsContent value="details" class="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle class="flex items-center space-x-2">
                <Code class="h-5 w-5" />
                <span>Raw Configuration</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre class="text-xs bg-muted p-4 rounded-md overflow-auto">{{ JSON.stringify(currentSpec, null, 2) }}</pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:open="showDeleteDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Pre-Aggregation</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this pre-aggregation? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            @click="showDeleteDialog = false"
            :disabled="isDeleting"
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            @click="onDelete"
            :disabled="isDeleting"
          >
            <Loader2 v-if="isDeleting" class="h-4 w-4 mr-2 animate-spin" />
            Delete
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
