<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Separator } from '~/components/ui/separator'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from '~/components/ui/sheet'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import { ArrowLeft, Edit, PlayCircle, Plus, Settings, Target, MoreHorizontal, Loader2, Trash2 } from 'lucide-vue-next'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '~/components/ui/alert-dialog'
import { toast } from 'vue-sonner'
import CreateMetricDialog from '~/components/CreateMetricDialog.vue'

// Page metadata
definePageMeta({
  title: 'Model Details',
  layout: 'default'
})

// Get model ID from route
const route = useRoute()
const modelId = route.params.id as string

// Use composables
const { getModel, executeModel, validateModel, updateModel } = useDataModels()
const { getMetricsForModel, deleteMetric } = useMetrics()
const { selectedEnvironmentId } = useEnvironments()

// Component state
const model = ref<any>(null)
const modelMetrics = ref<any[]>([])
const loading = ref(true)
const executing = ref(false)
const validating = ref(false)
const isEditSheetOpen = ref(false)
const isUpdating = ref(false)

// Delete dialog state
const deleteDialogOpen = ref(false)
const metricToDelete = ref<any>(null)
const isDeleting = ref(false)

// Edit form state
const editForm = ref({
  name: '',
  alias: '',
  description: '',
  config: '{}'
})

// Create metric dialog ref
const createMetricDialogRef = ref<InstanceType<typeof CreateMetricDialog> | null>(null)

// Computed properties
const modelStatus = computed(() => {
  if (!model.value) return 'unknown'
  if (model.value.is_valid === true) return 'valid'
  if (model.value.is_valid === false) return 'invalid'
  return 'pending'
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

// Localized time formatting - uses browser's locale
const formatLocalizedTime = (date: string | Date) => {
  const target = new Date(date)
  
  // Use Intl.RelativeTimeFormat for relative time in user's locale
  const now = new Date()
  const diffMs = now.getTime() - target.getTime()
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  const rtf = new Intl.RelativeTimeFormat(navigator.language, { numeric: 'auto' })
  
  if (diffMinutes < 1) return 'just now'
  if (diffMinutes < 60) return rtf.format(-diffMinutes, 'minute')
  if (diffHours < 24) return rtf.format(-diffHours, 'hour')
  if (diffDays < 7) return rtf.format(-diffDays, 'day')
  
  // For older dates, use localized date format
  return target.toLocaleDateString(navigator.language, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Event handlers
const onBack = () => {
  navigateTo('/metrics')
}

const onEdit = () => {
  // Populate edit form with current model data
  editForm.value = {
    name: model.value?.name || '',
    alias: model.value?.alias || '',
    description: model.value?.description || '',
    config: JSON.stringify(model.value?.config || {}, null, 2)
  }
  isEditSheetOpen.value = true
}

const onSaveEdit = async () => {
  if (!model.value || !selectedEnvironmentId.value) return

  isUpdating.value = true
  try {
    let config = {}
    try {
      config = JSON.parse(editForm.value.config)
    } catch (error) {
      toast.error('Invalid JSON configuration')
      return
    }

    // Prepare update data, only include fields that have actual values
    const updateData: any = {}
    
    if (editForm.value.name.trim()) {
      updateData.name = editForm.value.name.trim()
    }
    
    if (editForm.value.alias.trim()) {
      updateData.alias = editForm.value.alias.trim()
    }
    
    if (editForm.value.description.trim()) {
      updateData.description = editForm.value.description.trim()
    }
    
    if (Object.keys(config).length > 0) {
      updateData.config = config
    }

    const updatedModel = await updateModel(model.value.id, selectedEnvironmentId.value, updateData)

    if (updatedModel) {
      model.value = updatedModel
      isEditSheetOpen.value = false
      toast.success('Model updated successfully')
    }
  } catch (error) {
    console.error('Failed to update model:', error)
    toast.error('Failed to update model')
  } finally {
    isUpdating.value = false
  }
}

const onValidate = async () => {
  if (!model.value || !selectedEnvironmentId.value) return
  
  validating.value = true
  try {
    await validateModel(modelId)
    // Refresh model data
    await loadModel()
    toast.success('Model validation completed')
  } catch (error) {
    console.error('Failed to validate model:', error)
    toast.error('Failed to validate model')
  } finally {
    validating.value = false
  }
}

const onExecute = async () => {
  if (!model.value || !selectedEnvironmentId.value) return
  
  executing.value = true
  try {
    await executeModel(modelId, {})
    toast.success('Model execution completed')
  } catch (error) {
    console.error('Failed to execute model:', error)
    toast.error('Failed to execute model')
  } finally {
    executing.value = false
  }
}

const onMetricClick = (metricId: string) => {
  navigateTo(`/metrics/${metricId}`)
}

const onDeleteMetricClick = (metric: any, event: Event) => {
  event.stopPropagation()
  metricToDelete.value = metric
  deleteDialogOpen.value = true
}

const onDeleteMetric = async () => {
  if (!metricToDelete.value || !selectedEnvironmentId.value) return
  
  isDeleting.value = true
  try {
    const success = await deleteMetric(metricToDelete.value.id, selectedEnvironmentId.value)
    if (success) {
      toast.success('Metric deleted successfully')
      // Refresh the metrics list
      await loadModelMetrics()
      deleteDialogOpen.value = false
      metricToDelete.value = null
    } else {
      toast.error('Failed to delete metric')
    }
  } catch (error) {
    console.error('Failed to delete metric:', error)
    toast.error('Failed to delete metric')
  } finally {
    isDeleting.value = false
  }
}

const onAddMetric = () => {
  // Open the create metric dialog instead of navigating
  createMetricDialogRef.value?.openDialog()
}

const onMetricCreated = async (metric: any) => {
  // Refresh the metrics list when a new metric is created
  if (selectedEnvironmentId.value) {
    await loadModelMetrics()
  }
  toast.success('Metric added to model successfully')
}

// Data loading
const loadModel = async () => {
  try {
    if (!selectedEnvironmentId.value) {
      throw createError({
        statusCode: 400,
        statusMessage: 'Environment not selected'
      })
    }
    
    model.value = await getModel(modelId, selectedEnvironmentId.value)
    if (!model.value) {
      throw createError({
        statusCode: 404,
        statusMessage: 'Model not found'
      })
    }
  } catch (error) {
    console.error('Failed to load model:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to load model'
    })
  }
}

const loadModelMetrics = async () => {
  try {
    if (!selectedEnvironmentId.value) return
    
    modelMetrics.value = await getMetricsForModel(modelId, selectedEnvironmentId.value)
  } catch (error) {
    console.error('Failed to load model metrics:', error)
    modelMetrics.value = []
  }
}


const loadData = async () => {
  loading.value = true
  try {
    await loadModel()
    await loadModelMetrics()
  } finally {
    loading.value = false
  }
}

// Initialize
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Back Button (Always at top) -->
    <div>
      <Button variant="ghost" size="sm" @click="onBack" class="mb-4">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Metrics
      </Button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="space-y-6">
      <div class="space-y-1">
        <div class="h-8 w-64 bg-muted rounded animate-pulse"></div>
        <div class="h-4 w-32 bg-muted rounded animate-pulse"></div>
      </div>
      <Card>
        <CardContent class="pt-6">
          <div class="space-y-4">
            <div class="h-6 bg-muted rounded w-1/4 animate-pulse"></div>
            <div class="grid grid-cols-3 gap-4">
              <div class="h-20 bg-muted rounded animate-pulse"></div>
              <div class="h-20 bg-muted rounded animate-pulse"></div>
              <div class="h-20 bg-muted rounded animate-pulse"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Content -->
    <div v-else-if="model" class="space-y-6">
      <!-- Header -->
      <div class="space-y-1">
        <h1 class="text-2xl font-semibold tracking-tight">
          📁 {{ model.name }}
        </h1>
        <p class="text-sm text-muted-foreground">
          Data Model Details
        </p>
      </div>

      <!-- Model Information -->
      <Card>
        <CardHeader>
          <CardTitle>Model Information</CardTitle>
        </CardHeader>
        <CardContent class="space-y-6">
          <!-- Status and Basic Info -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="space-y-2">
              <div class="text-sm font-medium text-muted-foreground">Status</div>
              <Badge :variant="getStatusBadgeVariant(modelStatus)">
                {{ getStatusIcon(modelStatus) }} {{ modelStatus }}
              </Badge>
            </div>
            <div class="space-y-2">
              <div class="text-sm font-medium text-muted-foreground">Version</div>
              <div class="text-sm">{{ model.version }}</div>
            </div>
          </div>

          <!-- Additional Info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <div class="text-sm font-medium text-muted-foreground">Associated Metrics</div>
              <div class="flex items-center space-x-2 text-sm">
                <Target class="h-4 w-4" />
                <span>{{ modelMetrics.length }} metrics</span>
              </div>
            </div>
            <div class="space-y-2">
              <div class="text-sm font-medium text-muted-foreground">Last Updated</div>
              <div class="text-sm">{{ formatLocalizedTime(model.updated_at) }}</div>
            </div>
          </div>

          <!-- Description -->
          <div v-if="model.description" class="space-y-2">
            <div class="text-sm font-medium text-muted-foreground">Description</div>
            <p class="text-sm">{{ model.description }}</p>
          </div>

          <!-- Action Buttons at bottom of card -->
          <Separator />
          <div class="flex items-center justify-end space-x-2 pt-4">
            <Button variant="outline" size="sm" @click="onValidate" :disabled="validating">
              <Settings class="h-4 w-4 mr-2" />
              {{ validating ? 'Validating...' : 'Validate' }}
            </Button>
            <Button variant="outline" size="sm" @click="onExecute" :disabled="executing">
              <PlayCircle class="h-4 w-4 mr-2" />
              {{ executing ? 'Executing...' : 'Execute' }}
            </Button>
            <Button size="sm" @click="onEdit">
              <Edit class="h-4 w-4 mr-2" />
              Edit Model
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Associated Metrics -->
      <Card>
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle>Associated Metrics</CardTitle>
            <Button size="sm" @click="onAddMetric">
              <Plus class="h-4 w-4 mr-2" />
              Add Metric
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div v-if="modelMetrics.length === 0" class="text-center py-8">
            <Target class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 class="text-lg font-medium text-foreground mb-2">No metrics found</h3>
            <p class="text-muted-foreground mb-4">
              This model doesn't have any metrics yet. Create your first metric to get started.
            </p>
            <Button @click="onAddMetric">
              <Plus class="h-4 w-4 mr-2" />
              Add Metric
            </Button>
          </div>
          
          <div v-else class="space-y-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead class="text-right">Delete</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="metric in modelMetrics" :key="metric.id" class="cursor-pointer" @click="onMetricClick(metric.id)">
                  <TableCell class="font-medium">{{ metric.name }}</TableCell>
                  <TableCell class="text-muted-foreground">{{ metric.description || 'No description' }}</TableCell>
                  <TableCell>
                    <Badge variant="outline">Active</Badge>
                  </TableCell>
                  <TableCell>{{ formatLocalizedTime(metric.updated_at) }}</TableCell>
                  <TableCell class="text-right">
                    <Button variant="ghost" size="sm" @click="(e: Event) => onDeleteMetricClick(metric, e)">
                      <Trash2 class="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Edit Model Sheet -->
    <Sheet v-model:open="isEditSheetOpen">
      <SheetContent side="right" class="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Edit Data Model</SheetTitle>
          <SheetDescription>
            Update the model configuration and settings.
          </SheetDescription>
        </SheetHeader>
        
        <div class="grid gap-6 p-4">
          <div class="space-y-2">
            <Label for="edit-name">Name *</Label>
            <Input
              id="edit-name"
              v-model="editForm.name"
              placeholder="Enter model name"
              :disabled="isUpdating"
            />
          </div>
          
          <div class="space-y-2">
            <Label for="edit-alias">Alias</Label>
            <Input
              id="edit-alias"
              v-model="editForm.alias"
              placeholder="Enter model alias"
              :disabled="isUpdating"
            />
          </div>
          
          <div class="space-y-2">
            <Label for="edit-description">Description</Label>
            <Textarea
              id="edit-description"
              v-model="editForm.description"
              placeholder="Enter model description"
              rows="3"
              :disabled="isUpdating"
            />
          </div>
          
          
          <div class="space-y-2">
            <Label for="edit-config">Configuration (JSON)</Label>
            <Textarea
              id="edit-config"
              v-model="editForm.config"
              placeholder='{"key": "value"}'
              rows="6"
              class="font-mono text-sm"
              :disabled="isUpdating"
            />
          </div>
        </div>
        
        <SheetFooter class="flex gap-3">
          <Button 
            variant="outline" 
            @click="isEditSheetOpen = false" 
            :disabled="isUpdating"
          >
            Cancel
          </Button>
          <Button @click="onSaveEdit" :disabled="isUpdating">
            <Loader2 v-if="isUpdating" class="w-4 h-4 mr-2 animate-spin" />
            {{ isUpdating ? 'Saving...' : 'Save Changes' }}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>

         <!-- Create Metric Dialog -->
     <CreateMetricDialog
       ref="createMetricDialogRef"
       :prefilled-data-model-id="modelId"
       :prefilled-data-model-name="model?.name"
       :hide-initial-trigger="true"
       @created="onMetricCreated"
     />

    <!-- Delete Metric Alert Dialog -->
    <AlertDialog v-model:open="deleteDialogOpen">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Metric</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the metric "{{ metricToDelete?.name }}"? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel :disabled="isDeleting">Cancel</AlertDialogCancel>
          <AlertDialogAction 
            @click="onDeleteMetric" 
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
</template> 