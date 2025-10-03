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
import { Search, Filter, Plus, MoreHorizontal, PlayCircle, Edit, Settings, Target, FolderOpen, ChevronDown, Database, Loader2 } from 'lucide-vue-next'
import type { DataModel } from '~/composables/useDataModels'
import type { SemanticMetric } from '~/composables/useMetrics'
import CreateMetricDialog from '~/components/CreateMetricDialog.vue'
import { toast } from 'vue-sonner'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Metrics Management',
  layout: 'default'
})

// Use composables for data management
const { models, loading: modelsLoading, fetchModels, createModel } = useDataModels()
const { metrics, loading: metricsLoading, fetchMetrics, executeMetric, validateMetric, createMetric } = useMetrics()
const { currentView, modelFilters, metricFilters, switchView } = useMetricsView()

// Component state
const searchQuery = ref('')
const selectedStatus = ref<string | null>(null)
const selectedModel = ref<string | null>(null)

// Dialog states
const showCreateModelDialog = ref(false)
const showCreateMetricDialog = ref(false)
const isCreatingModel = ref(false)
const isCreatingMetric = ref(false)

// Component refs
const createMetricDialogRef = ref<InstanceType<typeof CreateMetricDialog> | null>(null)

// Model form state
const modelForm = ref({
  name: '',
  alias: '',
  description: '',
  config: {}
})

// Metric form state
const metricForm = ref({
  data_model_id: '',
  name: '',
  alias: '',
  title: '',
  description: '',
  public: true
})

// Form validation
const modelFormErrors = ref({
  name: '',
  alias: ''
})

const { 
  generateAlias, 
  validateAlias, 
  getAliasError, 
  aliasManuallyEdited, 
  markAsManuallyEdited
} = useAliasGenerator()

// Watch for name changes to auto-generate alias
watch(() => modelForm.value.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    modelForm.value.alias = generateAlias(newName)
  }
  // Clear name error when user starts typing
  modelFormErrors.value.name = ''
})

// Track manual alias edits
const onAliasInput = () => {
  markAsManuallyEdited()
}

// Watch for alias changes to validate
watch(() => modelForm.value.alias, (newAlias) => {
  modelFormErrors.value.alias = getAliasError(newAlias)
})


// Computed properties
const filteredModels = computed(() => {
  if (!models.value || models.value.length === 0) return []
  
  return models.value.filter(model => {
    const matchesSearch = !searchQuery.value || 
      model.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      model.description?.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesDataSource = true // Data models no longer have data_source_id
    
    const matchesStatus = !selectedStatus.value || 
      getModelStatus(model) === selectedStatus.value
    
    return matchesSearch && matchesDataSource && matchesStatus
  })
})

const filteredMetrics = computed(() => {
  if (!metrics.value || metrics.value.length === 0) return []
  
  return metrics.value.filter(metric => {
    const matchesSearch = !searchQuery.value ||
      metric.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      metric.alias?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      metric.title?.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesModel = !selectedModel.value ||
      metric.data_model_id === selectedModel.value
    
    const matchesStatus = !selectedStatus.value ||
      getMetricStatus(metric) === selectedStatus.value
    
    return matchesSearch && matchesModel && matchesStatus
  })
})

// Form validation computed
const isModelFormValid = computed(() => {
  return modelForm.value.name.trim() !== '' &&
         modelForm.value.alias !== '' &&
         validateAlias(modelForm.value.alias) &&
         !modelFormErrors.value.name &&
         !modelFormErrors.value.alias
})

// Utility functions
const getModelStatus = (model: any) => {
  if (model.is_valid === true) return 'valid'
  if (model.is_valid === false) return 'invalid'
  return 'pending'
}

const getMetricStatus = (metric: any) => {
  // You'll need to implement this based on your metric validation logic
  return 'valid' // placeholder
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

// Event handlers
const onViewChange = (view: string) => {
  switchView(view as 'models' | 'metrics')
}

const onModelClick = (modelId: string) => {
  navigateTo(`/metrics/models/${modelId}`)
}

const onMetricClick = (metricId: string) => {
  navigateTo(`/metrics/${metricId}`)
}

const onModelMetricsClick = (modelId: string) => {
  selectedModel.value = modelId
  switchView('metrics')
}

const onExecuteModel = async (modelId: string) => {
  // Implementation for model execution
  console.log('Execute model:', modelId)
}

const onExecuteMetric = async (metricId: string) => {
  try {
    await executeMetric(metricId, {})
  } catch (error) {
    console.error('Failed to execute metric:', error)
  }
}

const onValidateMetric = async (metricId: string) => {
  try {
    await validateMetric(metricId)
  } catch (error) {
    console.error('Failed to validate metric:', error)
  }
}

// Create handlers
const onCreateModel = () => {
  showCreateModelDialog.value = true
  resetModelForm()
}

const onCreateMetric = () => {
  createMetricDialogRef.value?.openDialog()
}

const onMetricCreated = async (metric: any) => {
  // Refresh the metrics list when a new metric is created
  await fetchMetrics()
  toast.success('Metric created successfully')
}

// Form handlers
  const resetModelForm = () => {
    modelForm.value = {
      name: '',
      alias: '',
      description: '',
      config: {}
    }
    modelFormErrors.value = {
      name: '',
      alias: ''
    }
    aliasManuallyEdited.value = false
  }

const resetMetricForm = () => {
  metricForm.value = {
    data_model_id: '',
    name: '',
    alias: '',
    title: '',
    description: '',
    public: true
  }
}

const handleCreateModel = async () => {
  // Validate form before submission
  if (!isModelFormValid.value) {
    if (!modelForm.value.name.trim()) {
      modelFormErrors.value.name = 'Name is required'
    }
    if (!modelForm.value.alias || !validateAlias(modelForm.value.alias)) {
      modelFormErrors.value.alias = 'Valid alias is required'
    }
    return
  }

  isCreatingModel.value = true
  try {
    const modelData = {
      name: modelForm.value.name.trim(),
      alias: modelForm.value.alias,
      description: modelForm.value.description.trim() || undefined,
      config: modelForm.value.config || {}
    }

    const createdModel = await createModel(modelData)
    if (createdModel) {
      showCreateModelDialog.value = false
      resetModelForm()
      // Refresh the models list
      await fetchModels()
    }
  } catch (error) {
    console.error('Failed to create model:', error)
  } finally {
    isCreatingModel.value = false
  }
}

const handleCreateMetric = async () => {
  if (!metricForm.value.name || !metricForm.value.data_model_id) {
    return
  }

  isCreatingMetric.value = true
  try {
    const metricData = {
      data_model_id: metricForm.value.data_model_id,
      name: metricForm.value.name,
      alias: metricForm.value.alias || undefined,
      title: metricForm.value.title || undefined,
      description: metricForm.value.description || undefined,
      public: metricForm.value.public
    }

    const createdMetric = await createMetric(metricData)
    if (createdMetric) {
      showCreateMetricDialog.value = false
      resetMetricForm()
      // Refresh the metrics list
      await fetchMetrics()
    }
  } catch (error) {
    console.error('Failed to create metric:', error)
  } finally {
    isCreatingMetric.value = false
  }
}

// Initialize data
onMounted(() => {
  fetchModels()
  fetchMetrics()
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div class="space-y-1">
        <h2 class="text-2xl font-semibold tracking-tight">📊 Metrics Management</h2>
        <p class="text-sm text-muted-foreground">
          Manage your data models and metrics in one unified interface
        </p>
      </div>
      
      <div class="flex items-center space-x-2">
        <Button variant="outline" size="sm">
          <Filter class="h-4 w-4 mr-2" />
          Export
        </Button>
        
        <!-- Create New Dropdown -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button size="sm">
              <Plus class="h-4 w-4 mr-2" />
              Create New
              <ChevronDown class="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem @click="onCreateModel" class="cursor-pointer">
              <Database class="h-4 w-4 mr-2" />
              Data Model
            </DropdownMenuItem>
            <DropdownMenuItem @click="onCreateMetric" class="cursor-pointer">
              <Target class="h-4 w-4 mr-2" />
              Metric
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- Create Model Dialog -->
    <Dialog v-model:open="showCreateModelDialog">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle class="flex items-center space-x-2">
            <Database class="h-5 w-5" />
            <span>Create Data Model</span>
          </DialogTitle>
          <DialogDescription>
            Create a new data model to organize your semantic definitions and metrics.
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4 py-4">
          <div class="space-y-2">
            <Label for="model-name">Name *</Label>
            <Input
              id="model-name"
              v-model="modelForm.name"
              placeholder="Enter model name"
              :disabled="isCreatingModel"
            />
            <p v-if="modelFormErrors.name" class="text-sm text-red-500">{{ modelFormErrors.name }}</p>
          </div>
          
          <div class="space-y-2">
            <Label for="model-alias">Alias</Label>
            <Input
              id="model-alias"
              v-model="modelForm.alias"
              placeholder="Auto-generated from name"
              :disabled="isCreatingModel"
              @input="onAliasInput"
            />
            <p v-if="modelFormErrors.alias" class="text-sm text-red-500">{{ modelFormErrors.alias }}</p>
            <p class="text-xs text-muted-foreground">Only lowercase letters, numbers, and underscores allowed</p>
          </div>
          
          <div class="space-y-2">
            <Label for="model-description">Description</Label>
            <Textarea
              id="model-description"
              v-model="modelForm.description"
              placeholder="Describe your data model"
              rows="3"
              :disabled="isCreatingModel"
            />
          </div>
          
        </div>
        
        <DialogFooter>
          <Button
            variant="outline"
            @click="showCreateModelDialog = false"
            :disabled="isCreatingModel"
          >
            Cancel
          </Button>
          <Button
            @click="handleCreateModel"
            :disabled="!isModelFormValid || isCreatingModel"
          >
            <Loader2 v-if="isCreatingModel" class="h-4 w-4 mr-2 animate-spin" />
            Create Model
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Create Metric Dialog -->
    <CreateMetricDialog
      ref="createMetricDialogRef"
      :hide-initial-trigger="true"
      @created="onMetricCreated"
    />

    <!-- Filters and Search -->
    <Card>
      <CardContent class="pt-6">
        <div class="flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4">
          <!-- Search -->
          <div class="flex-1">
            <div class="relative">
              <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                v-model="searchQuery"
                placeholder="Search models and metrics..."
                class="pl-8"
              />
            </div>
          </div>
          
          
          <!-- Status Filter -->
          <Select v-model="selectedStatus">
            <SelectTrigger class="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">All Status</SelectItem>
              <SelectItem value="valid">Valid</SelectItem>
              <SelectItem value="invalid">Invalid</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>

          <!-- Model Filter (for metrics view) -->
          <Select v-if="currentView === 'metrics'" v-model="selectedModel">
            <SelectTrigger class="w-[180px]">
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="null">All Models</SelectItem>
              <SelectItem v-for="model in models || []" :key="model.id" :value="model.id">
                {{ model.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- View Toggle -->
    <Tabs :value="currentView" @update:value="onViewChange" default-value="metrics" class="w-full">
      <TabsList class="grid w-full grid-cols-2">
        <TabsTrigger value="metrics" class="flex items-center space-x-2">
          <Target class="h-4 w-4" />
          <span>Metrics</span>
          <Badge variant="secondary" class="ml-2">{{ metrics?.length || 0 }}</Badge>
        </TabsTrigger>
        <TabsTrigger value="models" class="flex items-center space-x-2">
          <FolderOpen class="h-4 w-4" />
          <span>Models</span>
          <Badge variant="secondary" class="ml-2">{{ models?.length || 0 }}</Badge>
        </TabsTrigger>
      </TabsList>

      <!-- Models View -->
      <TabsContent value="models" class="space-y-4">
        <div v-if="modelsLoading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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

        <div v-else-if="!models || models.length === 0" class="text-center py-12">
          <FolderOpen class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No models found</h3>
          <p class="text-sm text-muted-foreground mb-4">
            Create your first data model to get started
          </p>
          <Button @click="onCreateModel">
            <Plus class="h-4 w-4 mr-2" />
            Create Model
          </Button>
        </div>

        <div v-else-if="filteredModels.length === 0" class="text-center py-12">
          <FolderOpen class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No models match your filters</h3>
          <p class="text-sm text-muted-foreground mb-4">
            Try adjusting your search or filter criteria
          </p>
          <Button variant="outline" @click="searchQuery = ''; selectedStatus = null">
            Clear Filters
          </Button>
        </div>

        <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card 
            v-for="model in filteredModels" 
            :key="model.id" 
            class="hover:shadow-md transition-shadow cursor-pointer"
            @click="onModelClick(model.id)"
          >
            <CardHeader class="pb-3">
              <div class="flex items-start justify-between">
                <div class="space-y-1 flex-1">
                  <CardTitle class="text-base font-medium">{{ model.name }}</CardTitle>
                  <p class="text-sm text-muted-foreground line-clamp-2">
                    {{ model.description || 'No description available' }}
                  </p>
                </div>
                <Badge :variant="getStatusBadgeVariant(getModelStatus(model))" class="ml-2">
                  {{ getStatusIcon(getModelStatus(model)) }} {{ getModelStatus(model) }}
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent class="pt-0">
              <div class="space-y-3">
                <!-- Model Info -->
                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center space-x-2 text-muted-foreground">
                    <span>📊</span>
                    <span>Data Model</span>
                  </div>
                  <span class="text-muted-foreground">v{{ model.version }}</span>
                </div>
                
                <!-- Metrics Count -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-1 text-sm text-muted-foreground">
                    <Target class="h-3 w-3" />
                    <span>{{ model.metrics_count || 0 }} metrics</span>
                  </div>
                  <span class="text-xs text-muted-foreground">
                    {{ formatRelativeTime(model.updated_at) }}
                  </span>
                </div>
                
                <Separator />
                
                <!-- Actions -->
                <div class="flex items-center justify-between">
                  <div class="flex space-x-1">
                    <Button variant="ghost" size="sm" @click.stop="onExecuteModel(model.id)">
                      <PlayCircle class="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" @click.stop="onModelClick(model.id)">
                      <Edit class="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Settings class="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <Button 
                    variant="outline" 
                    size="sm" 
                    @click.stop="onModelMetricsClick(model.id)"
                    v-if="model.metrics_count && model.metrics_count > 0"
                  >
                    View Metrics
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Metrics View -->
      <TabsContent value="metrics" class="space-y-4">
        <div v-if="metricsLoading" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
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

        <div v-else-if="!models || models.length === 0" class="text-center py-12">
          <FolderOpen class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No data models found</h3>
          <p class="text-sm text-muted-foreground mb-4">
            Create your first data model to get started with metrics
          </p>
          <Button @click="onCreateModel">
            <Plus class="h-4 w-4 mr-2" />
            Create Model
          </Button>
        </div>

        <div v-else-if="!metrics || metrics.length === 0" class="text-center py-12">
          <Target class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No metrics found</h3>
          <p class="text-sm text-muted-foreground mb-4">
            Create your first metric to get started
          </p>
          <Button @click="onCreateMetric">
            <Plus class="h-4 w-4 mr-2" />
            Create Metric
          </Button>
        </div>

        <div v-else-if="filteredMetrics.length === 0" class="text-center py-12">
          <Target class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No metrics match your filters</h3>
          <p class="text-sm text-muted-foreground mb-4">
            Try adjusting your search or filter criteria
          </p>
          <Button variant="outline" @click="searchQuery = ''; selectedModel = null; selectedStatus = null">
            Clear Filters
          </Button>
        </div>

        <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card 
            v-for="metric in filteredMetrics" 
            :key="metric.id" 
            class="hover:shadow-md transition-shadow cursor-pointer"
            @click="onMetricClick(metric.id)"
          >
            <CardHeader class="pb-3">
              <div class="flex items-start justify-between">
                <div class="space-y-1 flex-1">
                  <CardTitle class="text-base font-medium">{{ metric.title || metric.name }}</CardTitle>
                  <p class="text-sm text-muted-foreground line-clamp-2">
                    {{ metric.description || 'No description available' }}
                  </p>
                </div>
                <div class="flex flex-col items-end space-y-1">
                  <Badge :variant="getStatusBadgeVariant(getMetricStatus(metric))">
                    {{ getStatusIcon(getMetricStatus(metric)) }} {{ getMetricStatus(metric) }}
                  </Badge>
                  <Badge v-if="metric.public" variant="secondary" class="text-xs">Public</Badge>
                </div>
              </div>
            </CardHeader>
            
            <CardContent class="pt-0">
              <div class="space-y-3">
                <!-- Metric Info -->
                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center space-x-2 text-muted-foreground">
                    <FolderOpen class="h-3 w-3" />
                    <span>{{ metric.data_model_name || 'Unknown Model' }}</span>
                  </div>
                  <span class="text-muted-foreground">{{ metric.alias || metric.name }}</span>
                </div>
                
                <!-- Parameters -->
                <div v-if="metric.parameters && metric.parameters.length > 0" class="flex items-center space-x-1 text-sm text-muted-foreground">
                  <Settings class="h-3 w-3" />
                  <span>{{ metric.parameters.length }} parameters</span>
                </div>
                
                <div class="flex items-center justify-between">
                  <span class="text-xs text-muted-foreground">
                    {{ formatRelativeTime(metric.updated_at) }}
                  </span>
                </div>
                
                <Separator />
                
                <!-- Actions -->
                <div class="flex items-center justify-between">
                  <div class="flex space-x-1">
                    <Button variant="ghost" size="sm" @click.stop="onExecuteMetric(metric.id)">
                      <PlayCircle class="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" @click.stop="onMetricClick(metric.id)">
                      <Edit class="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" @click.stop="onValidateMetric(metric.id)">
                      <Settings class="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal class="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>
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