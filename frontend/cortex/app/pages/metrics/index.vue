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
import { TracingBeam } from '~/components/ui/tracing-beam'
import { Search, Filter, Plus, MoreHorizontal, ChevronDown, Database, Loader2, Sparkles, Target } from 'lucide-vue-next'
import type { DataModel } from '~/composables/useDataModels'
import type { SemanticMetric } from '~/composables/useMetrics'
import CreateMetricDialog from '~/components/CreateMetricDialog.vue'
import MetricListModelCard from '~/components/metric/list/ModelCard.vue'
import MetricListMetricCard from '~/components/metric/list/MetricCard.vue'
import { toast } from 'vue-sonner'

// Page metadata
definePageMeta({
  title: 'Metrics Management',
  layout: 'default'
})

// Use composables for data management
const { models, loading: modelsLoading, fetchModels, createModel } = useDataModels()
const { metrics, loading: metricsLoading, fetchMetrics, executeMetric, createMetric } = useMetrics()
const { currentView, modelFilters, metricFilters, switchView } = useMetricsView()
const { selectedEnvironmentId } = useEnvironments()

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


// Helper functions for time categorization
const isRecentlyUpdated = (dateString: string) => {
  const updated = new Date(dateString)
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return updated > yesterday
}

const isUpdatedThisMonth = (dateString: string) => {
  const updated = new Date(dateString)
  const now = new Date()
  return updated.getMonth() === now.getMonth() && 
         updated.getFullYear() === now.getFullYear()
}

// Computed properties
const filteredModels = computed(() => {
  if (!models.value || models.value.length === 0) return []
  
  return models.value.filter(model => {
    const matchesSearch = !searchQuery.value || 
      model.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      model.description?.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesDataSource = true // Data models no longer have data_source_id
    
    const getStatus = (m: any) => {
      if (m.is_valid === true) return 'valid'
      if (m.is_valid === false) return 'invalid'
      return 'pending'
    }
    
    const matchesStatus = !selectedStatus.value || 
      getStatus(model) === selectedStatus.value
    
    return matchesSearch && matchesDataSource && matchesStatus
  })
})

const categorizedModels = computed(() => {
  const recent: any[] = []
  const thisMonth: any[] = []
  const older: any[] = []
  
  filteredModels.value.forEach(model => {
    if (isRecentlyUpdated(model.updated_at)) {
      recent.push(model)
    } else if (isUpdatedThisMonth(model.updated_at)) {
      thisMonth.push(model)
    } else {
      older.push(model)
    }
  })
  
  return { recent, thisMonth, older }
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
      'valid' === selectedStatus.value // Metrics default to 'valid' status
    
    return matchesSearch && matchesModel && matchesStatus
  })
})

const categorizedMetrics = computed(() => {
  const recent: any[] = []
  const thisMonth: any[] = []
  const older: any[] = []
  
  filteredMetrics.value.forEach(metric => {
    if (isRecentlyUpdated(metric.updated_at)) {
      recent.push(metric)
    } else if (isUpdatedThisMonth(metric.updated_at)) {
      thisMonth.push(metric)
    } else {
      older.push(metric)
    }
  })
  
  return { recent, thisMonth, older }
})

// Form validation computed
const isModelFormValid = computed(() => {
  return modelForm.value.name.trim() !== '' &&
         modelForm.value.alias !== '' &&
         validateAlias(modelForm.value.alias) &&
         !modelFormErrors.value.name &&
         !modelFormErrors.value.alias
})

// Helper functions for time categorization are now in the components

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
  if (selectedEnvironmentId.value) {
    await fetchMetrics(selectedEnvironmentId.value)
  }
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
    if (!selectedEnvironmentId.value) return
    
    const modelData = {
      environment_id: selectedEnvironmentId.value,
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
      await fetchModels(selectedEnvironmentId.value)
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
    if (!selectedEnvironmentId.value) return
    
    const metricData = {
      environment_id: selectedEnvironmentId.value,
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
      await fetchMetrics(selectedEnvironmentId.value)
    }
  } catch (error) {
    console.error('Failed to create metric:', error)
  } finally {
    isCreatingMetric.value = false
  }
}

// Initialize data
onMounted(() => {
  if (selectedEnvironmentId.value) {
    fetchModels(selectedEnvironmentId.value)
    fetchMetrics(selectedEnvironmentId.value)
  }
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row flex-wrap items-start md:items-center space-y-4 md:space-y-0 md:space-x-4 justify-between mb-10">
      <div class="space-y-1">
        <h2 class="text-2xl font-semibold tracking-tight">Metrics</h2>
      </div>
      
      <div class="flex flex-col md:flex-row flex-wrap items-start md:items-center space-y-4 md:space-y-2  xl:space-y-0 md:space-x-4 justify-between">
        <div class="flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4">
          <!-- Search -->
          <div class="min-w-[25vw]">
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
        <div class="flex flex-row space-x-4">
          <!-- Generate Recommendations Button -->
        <Button variant="outline" size="lg" class="cursor-pointer hover:bg-fuchsia-600 hover:dark:bg-fuchsia-600 hover:text-white"
         @click="navigateTo('/metrics/recommendations')">
          <Sparkles class="h-4 w-4 mr-2" />
          Auto Generate
        </Button>
        
        <!-- Create New Dropdown -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button size="lg">
              <Plus class="h-4 w-4 mr-2" />
              Add
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

        <div v-else class="space-y-8">
          <!-- Recently Updated -->
          <div v-if="categorizedModels.recent.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Recently Updated</h3>
              <Badge variant="secondary">{{ categorizedModels.recent.length }}</Badge>
            </div>
            <div class="space-y-4 px-6">
              <MetricListModelCard
                v-for="model in categorizedModels.recent"
                :key="model.id"
                :model="model"
                @click="onModelClick(model.id)"
              />
            </div>
          </div>

          <!-- Updated This Month -->
          <div v-if="categorizedModels.thisMonth.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Updated This Month</h3>
              <Badge variant="secondary">{{ categorizedModels.thisMonth.length }}</Badge>
            </div>
            <div class="space-y-4 px-6">
              <MetricListModelCard
                v-for="model in categorizedModels.thisMonth"
                :key="model.id"
                :model="model"
                @click="onModelClick(model.id)"
              />
            </div>
          </div>

          <!-- Older -->
          <div v-if="categorizedModels.older.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Older</h3>
              <Badge variant="secondary">{{ categorizedModels.older.length }}</Badge>
            </div>
            <div class="space-y-4 px-6">
              <MetricListModelCard
                v-for="model in categorizedModels.older"
                :key="model.id"
                :model="model"
                @click="onModelClick(model.id)"
              />
            </div>
          </div>
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

        <div v-else class="space-y-8">
          <!-- Recently Updated -->
          <div v-if="categorizedMetrics.recent.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Recently Updated</h3>
              <Badge variant="secondary">{{ categorizedMetrics.recent.length }}</Badge>
            </div>
            <div class="pl-6 space-y-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <MetricListMetricCard
                v-for="metric in categorizedMetrics.recent"
                :key="metric.id"
                :metric="metric"
                @click="onMetricClick(metric.id)"
              />
            </div>
          </div>

          <!-- Updated This Month -->
          <div v-if="categorizedMetrics.thisMonth.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Updated This Month</h3>
              <Badge variant="secondary">{{ categorizedMetrics.thisMonth.length }}</Badge>
            </div>
            <div class="space-y-4 pl-6 grid grid-cols-3 gap-4">
              <MetricListMetricCard
                v-for="metric in categorizedMetrics.thisMonth"
                :key="metric.id"
                :metric="metric"
                @click="onMetricClick(metric.id)"
              />
            </div>
          </div>

          <!-- Older -->
          <div v-if="categorizedMetrics.older.length > 0">
            <div class="flex items-center gap-2 mb-4">
              <h3 class="text-sm font-medium text-muted-foreground">Older</h3>
              <Badge variant="secondary">{{ categorizedMetrics.older.length }}</Badge>
            </div>
            <div class="space-y-4 pl-6 grid grid-cols-3 gap-4">
              <MetricListMetricCard
                v-for="metric in categorizedMetrics.older"
                :key="metric.id"
                :metric="metric"
                @click="onMetricClick(metric.id)"
              />
            </div>
          </div>
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