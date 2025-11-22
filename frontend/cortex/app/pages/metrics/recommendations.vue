<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Checkbox } from '~/components/ui/checkbox'
import { Separator } from '~/components/ui/separator'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { Sparkles, Database, Target, Loader2, CheckCircle2, XCircle, ArrowLeft, ChevronRight } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'
import { toast } from 'vue-sonner'

// Page metadata
definePageMeta({
  title: 'Generate Metric Recommendations',
  layout: 'default'
})

// Composables
const { dataSources, getDataSourceSchema } = useDataSources()
const { models, fetchModels } = useDataModels()
const { recommendMetrics, createMetric } = useMetrics()
const { selectedEnvironmentId } = useEnvironments()

// State
const step = ref<'select' | 'review' | 'creating'>('select')
const selectedDataSource = ref<string>('')
const selectedDataModel = ref<string>('')
const recommendedMetrics = ref<SemanticMetric[]>([])
const selectedMetricIds = ref<Set<string>>(new Set())
const isGenerating = ref(false)
const isCreating = ref(false)
const creationProgress = ref({ current: 0, total: 0, errors: [] as string[] })

// Computed
const canGenerate = computed(() => {
  return selectedDataSource.value && selectedDataModel.value && !isGenerating.value
})

const selectedMetrics = computed(() => {
  return recommendedMetrics.value.filter(m => selectedMetricIds.value.has(m.name))
})

const allSelected = computed(() => {
  return recommendedMetrics.value.length > 0 && 
         selectedMetricIds.value.size === recommendedMetrics.value.length
})

const selectedDataSourceName = computed(() => {
  return dataSources.value?.find(ds => ds.id === selectedDataSource.value)?.name || 'Unknown'
})

const selectedDataModelName = computed(() => {
  return models.value?.find(m => m.id === selectedDataModel.value)?.name || 'Unknown'
})

// Helper function to determine if metric is comparison type
const isComparisonMetric = (metric: SemanticMetric) => {
  return metric.dimensions && metric.dimensions.length > 0
}

// Helper function to get metric type badge
const getMetricTypeBadge = (metric: SemanticMetric) => {
  return isComparisonMetric(metric) ? 'Comparison' : 'Single Value'
}

// Helper function to count measures, dimensions, filters
const getMetricStats = (metric: SemanticMetric) => {
  const measures = metric.measures?.length || 0
  const dimensions = metric.dimensions?.length || 0
  const filters = metric.filters?.length || 0
  return { measures, dimensions, filters }
}

// Event handlers
const handleGenerate = async () => {
  if (!canGenerate.value || !selectedEnvironmentId.value) return

  isGenerating.value = true
  try {
    const metrics = await recommendMetrics(
      selectedEnvironmentId.value,
      selectedDataSource.value,
      selectedDataModel.value
    )
    
    recommendedMetrics.value = metrics
    
    // Start with none selected (user must select which ones they want)
    selectedMetricIds.value = new Set()
    
    if (metrics.length === 0) {
      toast.info('No recommendations generated', {
        description: 'The selected data source schema did not produce any metric recommendations.'
      })
    } else {
      step.value = 'review'
      toast.success(`Generated ${metrics.length} metric recommendations`)
    }
  } catch (error: any) {
    console.error('Failed to generate recommendations:', error)
    toast.error('Failed to generate recommendations', {
      description: error?.data?.detail || error.message || 'An unexpected error occurred'
    })
  } finally {
    isGenerating.value = false
  }
}

const toggleMetric = (metricName: string, checked: boolean | 'indeterminate') => {
  const newSet = new Set(selectedMetricIds.value)
  if (checked === true) {
    newSet.add(metricName)
  } else {
    newSet.delete(metricName)
  }
  selectedMetricIds.value = newSet
}

const selectAll = () => {
  selectedMetricIds.value = new Set(recommendedMetrics.value.map(m => m.name))
}

const deselectAll = () => {
  selectedMetricIds.value = new Set()
}

const handleCreateSelected = async () => {
  if (selectedMetrics.value.length === 0) {
    toast.error('No metrics selected')
    return
  }

  step.value = 'creating'
  isCreating.value = true
  creationProgress.value = {
    current: 0,
    total: selectedMetrics.value.length,
    errors: []
  }

  const metricsToCreate = selectedMetrics.value

  for (let i = 0; i < metricsToCreate.length; i++) {
    const metric = metricsToCreate[i] as SemanticMetric
    try {
      await createMetric({
        environment_id: selectedEnvironmentId.value!,
        data_model_id: selectedDataModel.value,
        data_source_id: selectedDataSource.value,
        name: metric.name,
        title: metric.title || undefined,
        description: metric.description || undefined,
        table_name: metric.table_name || undefined,
        measures: metric.measures || undefined,
        dimensions: metric.dimensions || undefined,
        filters: metric.filters || undefined,
        grouped: metric.grouped,
        public: true
      })
      creationProgress.value.current++
    } catch (error: any) {
      console.error(`Failed to create metric ${metric.name}:`, error)
      creationProgress.value.errors.push(`${metric.title || metric.name}: ${error?.data?.detail || error.message}`)
      creationProgress.value.current++
    }
  }

  isCreating.value = false

  // Show results
  const successCount = creationProgress.value.current - creationProgress.value.errors.length
  if (creationProgress.value.errors.length === 0) {
    toast.success(`Successfully created ${successCount} metrics!`)
    setTimeout(() => {
      navigateTo('/metrics')
    }, 1500)
  } else {
    toast.warning(`Created ${successCount} of ${creationProgress.value.total} metrics`, {
      description: `${creationProgress.value.errors.length} metrics failed to create`
    })
  }
}

const handleBack = () => {
  if (step.value === 'review') {
    step.value = 'select'
    recommendedMetrics.value = []
    selectedMetricIds.value = new Set()
  }
}

const handleBackToMetrics = () => {
  navigateTo('/metrics')
}

// Initialize data
onMounted(() => {
  if (selectedEnvironmentId.value) {
    fetchModels(selectedEnvironmentId.value)
  }
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <Button variant="ghost" size="sm" @click="handleBackToMetrics">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Metrics
        </Button>
      </div>
    </div>

    <div class="space-y-1">
      <h2 class="text-2xl font-semibold tracking-tight flex items-center space-x-2">
        <Sparkles class="h-6 w-6 text-primary" />
        <span>Generate Metric Recommendations</span>
      </h2>
      <p class="text-sm text-muted-foreground">
        Automatically generate metrics from your data source schema using intelligent rules
      </p>
    </div>

    <!-- Step 1: Selection -->
    <Card v-if="step === 'select'">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Database class="h-5 w-5" />
          <span>Select Data Source and Model</span>
        </CardTitle>
        <CardDescription>
          Choose a data source to analyze and a data model to associate the generated metrics with
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-6">
        <!-- Data Source Selection -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Data Source *</label>
          <Select v-model="selectedDataSource">
            <SelectTrigger>
              <SelectValue placeholder="Select a data source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem 
                v-for="source in dataSources" 
                :key="source.id" 
                :value="source.id"
              >
                {{ source.name }} ({{ source.source_type }})
              </SelectItem>
            </SelectContent>
          </Select>
          <p class="text-xs text-muted-foreground">
            The data source schema will be analyzed to generate metric recommendations
          </p>
        </div>

        <!-- Data Model Selection -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Data Model *</label>
          <Select v-model="selectedDataModel">
            <SelectTrigger>
              <SelectValue placeholder="Select a data model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem 
                v-for="model in models" 
                :key="model.id" 
                :value="model.id"
              >
                {{ model.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          <p class="text-xs text-muted-foreground">
            Generated metrics will be associated with this data model
          </p>
        </div>

        <Separator />

        <!-- Generate Button -->
        <div class="flex justify-end">
          <Button 
            @click="handleGenerate" 
            :disabled="!canGenerate"
            size="lg"
          >
            <Loader2 v-if="isGenerating" class="h-4 w-4 mr-2 animate-spin" />
            <Sparkles v-else class="h-4 w-4 mr-2" />
            {{ isGenerating ? 'Generating...' : 'Generate Recommendations' }}
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Step 2: Review -->
    <div v-if="step === 'review'" class="space-y-6">
      <!-- Summary Card -->
      <Card>
        <CardContent class="pt-6">
          <div class="flex items-center justify-between">
            <div class="space-y-1">
              <div class="flex items-center space-x-2">
                <Database class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm font-medium">{{ selectedDataSourceName }}</span>
                <ChevronRight class="h-4 w-4 text-muted-foreground" />
                <Target class="h-4 w-4 text-muted-foreground" />
                <span class="text-sm font-medium">{{ selectedDataModelName }}</span>
              </div>
              <p class="text-sm text-muted-foreground">
                {{ recommendedMetrics.length }} metrics recommended • {{ selectedMetricIds.size }} selected
              </p>
            </div>

            <div class="flex items-center space-x-2">
              <Button variant="outline" size="sm" @click="handleBack">
                <ArrowLeft class="h-4 w-4 mr-2" />
                Back
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                @click="allSelected ? deselectAll() : selectAll()"
              >
                {{ allSelected ? 'Deselect All' : 'Select All' }}
              </Button>
              <Button 
                @click="handleCreateSelected" 
                :disabled="selectedMetricIds.size === 0"
                size="sm"
              >
                Create {{ selectedMetricIds.size }} Selected
                <ChevronRight class="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Metrics List -->
      <div class="space-y-4">
        <Card 
          v-for="metric in recommendedMetrics" 
          :key="metric.name"
          class="relative hover:shadow-md transition-shadow"
          :class="{ 'ring-2 ring-primary': selectedMetricIds.has(metric.name) }"
        >
          <CardHeader class="pb-3">
            <div class="flex items-start space-x-3">
              <Checkbox 
                :id="`metric-${metric.name}`"
                :checked="selectedMetricIds.has(metric.name)"
                @click="(e: Event) => {
                  e.stopPropagation();
                  toggleMetric(metric.name, !(selectedMetricIds.has(metric.name)));
                }"
                class="mt-1"
              />
              <label :for="`metric-${metric.name}`" class="flex-1 space-y-1 cursor-pointer">
                <CardTitle class="text-base font-medium">
                  {{ metric.title || metric.name }}
                </CardTitle>
                <p class="text-xs text-muted-foreground line-clamp-2">
                  {{ metric.description || 'No description' }}
                </p>
              </label>
            </div>
          </CardHeader>

          <CardContent class="pt-0">
            <div class="grid gap-4 md:grid-cols-3">
              <!-- Left Column: Basic Info -->
              <div class="space-y-3">
                <!-- Metric Type Badge -->
                <div class="flex items-center space-x-2">
                  <Badge :variant="isComparisonMetric(metric) ? 'default' : 'secondary'">
                    {{ getMetricTypeBadge(metric) }}
                  </Badge>
                  <Badge variant="outline" class="text-xs">
                    {{ metric.table_name }}
                  </Badge>
                </div>

                <!-- Metric Stats -->
                <div class="flex flex-col space-y-1 text-xs text-muted-foreground">
                  <span v-if="getMetricStats(metric).measures > 0">
                    📊 {{ getMetricStats(metric).measures }} measure{{ getMetricStats(metric).measures !== 1 ? 's' : '' }}
                  </span>
                  <span v-if="getMetricStats(metric).dimensions > 0">
                    🔷 {{ getMetricStats(metric).dimensions }} dim{{ getMetricStats(metric).dimensions !== 1 ? 's' : '' }}
                  </span>
                  <span v-if="getMetricStats(metric).filters > 0">
                    🔍 {{ getMetricStats(metric).filters }} filter{{ getMetricStats(metric).filters !== 1 ? 's' : '' }}
                  </span>
                </div>
              </div>

              <!-- Middle Column: Measures -->
              <div v-if="metric.measures && metric.measures.length > 0" class="space-y-2">
                <p class="text-xs font-medium">Measures:</p>
                <div class="space-y-1">
                  <div 
                    v-for="(measure, idx) in metric.measures" 
                    :key="idx"
                    class="text-xs text-muted-foreground pl-2"
                  >
                    • {{ measure.type?.toUpperCase() }}({{ measure.query || measure.name }})
                  </div>
                </div>
              </div>

              <!-- Right Column: Dimensions and Filters -->
              <div class="space-y-3">
                <!-- Dimension Details -->
                <div v-if="metric.dimensions && metric.dimensions.length > 0" class="space-y-2">
                  <p class="text-xs font-medium">Dimensions:</p>
                  <div class="space-y-1">
                    <div 
                      v-for="(dim, idx) in metric.dimensions" 
                      :key="idx"
                      class="text-xs text-muted-foreground pl-2"
                    >
                      • {{ dim.name }}
                    </div>
                  </div>
                </div>

                <!-- Filter Details -->
                <div v-if="metric.filters && metric.filters.length > 0" class="space-y-2">
                  <p class="text-xs font-medium">Filters:</p>
                  <div class="space-y-1">
                    <div 
                      v-for="(filter, idx) in metric.filters" 
                      :key="idx"
                      class="text-xs text-muted-foreground pl-2"
                    >
                      • {{ filter.name || filter.query }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Step 3: Creating -->
    <Card v-if="step === 'creating'">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Loader2 v-if="isCreating" class="h-5 w-5 animate-spin" />
          <CheckCircle2 v-else class="h-5 w-5 text-green-500" />
          <span>{{ isCreating ? 'Creating Metrics...' : 'Creation Complete' }}</span>
        </CardTitle>
        <CardDescription>
          {{ creationProgress.current }} of {{ creationProgress.total }} metrics processed
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <!-- Progress Bar -->
        <div class="space-y-2">
          <div class="w-full bg-secondary rounded-full h-2">
            <div 
              class="bg-primary h-2 rounded-full transition-all duration-300"
              :style="{ width: `${(creationProgress.current / creationProgress.total) * 100}%` }"
            ></div>
          </div>
          <p class="text-sm text-muted-foreground text-center">
            {{ Math.round((creationProgress.current / creationProgress.total) * 100) }}%
          </p>
        </div>

        <!-- Errors -->
        <div v-if="creationProgress.errors.length > 0" class="space-y-2">
          <Alert variant="destructive">
            <XCircle class="h-4 w-4" />
            <AlertDescription>
              <p class="font-medium">{{ creationProgress.errors.length }} metric(s) failed to create:</p>
              <ul class="mt-2 space-y-1 text-sm">
                <li v-for="(error, idx) in creationProgress.errors" :key="idx">
                  • {{ error }}
                </li>
              </ul>
            </AlertDescription>
          </Alert>
        </div>

        <!-- Success Message -->
        <div v-if="!isCreating" class="text-center space-y-4 pt-4">
          <p class="text-sm text-muted-foreground">
            Successfully created {{ creationProgress.current - creationProgress.errors.length }} metrics
          </p>
          <Button @click="handleBackToMetrics">
            View Metrics
            <ChevronRight class="h-4 w-4 ml-2" />
          </Button>
        </div>
      </CardContent>
    </Card>
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

