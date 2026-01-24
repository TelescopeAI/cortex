<script setup lang="ts">
import { ref, computed, watch, shallowRef } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Separator } from '~/components/ui/separator'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '~/components/ui/collapsible'
import { Sparkles, Database, Target, Loader2, CheckCircle2, XCircle, ArrowLeft, ChevronRight, ChevronDown } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'
import { toast } from 'vue-sonner'
import MetricPreviewCard from '~/components/recommend/MetricPreviewCard.vue'
import MetricRecommendFilterSection from '~/components/recommend/MetricRecommendFilterSection.vue'

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
const recommendationsMeta = ref<any>(null)
const selectedMetricIds = ref<Set<string>>(new Set())
const isGenerating = ref(false)
const isCreating = ref(false)
const creationProgress = ref({ current: 0, total: 0, errors: [] as string[] })

// Schema and filter state
interface TableSelectionState {
  excluded: boolean
  selectedColumns: string[]
}

const schema = ref<{ tables: any[] } | null>(null)
const isLoadingSchema = ref(false)
const tableSelections = ref<Record<string, TableSelectionState>>({})
const selectedMetricTypes = ref<string[]>(['count'])
const selectedTimeGrains = ref<string[]>(['month'])
const timeWindowDays = ref<number>(30)
const advancedFiltersOpen = ref(false)

// Scroll detection for sticky header
const scrollSentinel = ref<HTMLElement | null>(null)
const isScrolled = shallowRef(false)

useIntersectionObserver(
  scrollSentinel,
  ([entry]) => {
    isScrolled.value = !entry?.isIntersecting
  },
  { threshold: 0 }
)

// Computed
const canGenerate = computed(() => {
  return selectedDataSource.value && selectedDataModel.value && !isGenerating.value
})

const selectedMetrics = computed(() => {
  return recommendedMetrics.value.filter(m => selectedMetricIds.value.has(m.name))
})

// Transform state to backend API format
const selectConfig = computed(() => {
  if (!schema.value) return {}

  const include: Record<string, string[]> = {}
  const exclude: Record<string, string[]> = {}

  Object.entries(tableSelections.value).forEach(([tableName, state]) => {
    const table = schema.value?.tables.find(t => t.name === tableName)
    if (!table) return

    // Handle excluded tables
    if (state.excluded) {
      exclude[tableName] = []  // Empty array = exclude entire table
      return
    }

    // Determine if all columns selected or specific columns
    const allColumnCount = table.columns.length
    const selectedCount = state.selectedColumns.length

    if (selectedCount === allColumnCount) {
      // All columns selected - send empty array to backend as optimization
      include[tableName] = []  // Empty array = all columns (backend convention)
    } else {
      // Specific columns selected
      include[tableName] = state.selectedColumns
    }
  })

  // If no specific filters, return empty object (select all)
  if (Object.keys(include).length === 0 && Object.keys(exclude).length === 0) {
    return {}
  }

  // Return config with only populated fields
  const config: any = {}
  if (Object.keys(include).length > 0) config.include = include
  if (Object.keys(exclude).length > 0) config.exclude = exclude
  return config
})

const timeWindows = computed(() => {
  return timeWindowDays.value ? [timeWindowDays.value] : undefined
})

const grains = computed(() => {
  return selectedTimeGrains.value.length > 0 ? selectedTimeGrains.value : undefined
})

const metricTypes = computed(() => {
  return selectedMetricTypes.value.length > 0 ? selectedMetricTypes.value : undefined
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

// Event handlers
const handleGenerate = async () => {
  if (!canGenerate.value || !selectedEnvironmentId.value) return

  isGenerating.value = true
  try {
    const { metrics, metadata } = await recommendMetrics(
      selectedEnvironmentId.value,
      selectedDataSource.value,
      selectedDataModel.value,
      {
        select: selectConfig.value,
        metricTypes: metricTypes.value,
        timeWindows: timeWindows.value,
        grains: grains.value
      }
    )
    recommendedMetrics.value = metrics
    recommendationsMeta.value = metadata || null
    
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

// Watch for data source changes to fetch schema
watch(selectedDataSource, async (dataSourceId) => {
  if (!dataSourceId) {
    schema.value = null
    tableSelections.value = {}
    return
  }

  isLoadingSchema.value = true
  try {
    schema.value = await getDataSourceSchema(dataSourceId)

    // Initialize with all tables and columns selected
    const selections: Record<string, TableSelectionState> = {}
    schema.value.tables.forEach(table => {
      const allColumnNames = table.columns.map(col => col.name)
      selections[table.name] = {
        excluded: false,
        selectedColumns: allColumnNames  // All column names
      }
    })
    tableSelections.value = selections
  } catch (error) {
    console.error('Failed to fetch schema:', error)
    toast.error('Failed to load data source schema')
  } finally {
    isLoadingSchema.value = false
  }
})

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
        <Sparkles class="h-6 w-6 text-primary hover:text-fuchsia-600 hover:animate-bounce hover:cursor-none" />
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

        <!-- Advanced Filters (Collapsible) -->
        <Collapsible v-model:open="advancedFiltersOpen" class="border rounded-lg">
          <div class="flex items-center justify-between p-4">
            <div>
              <h3 class="font-semibold text-sm text-gray-900 dark:text-gray-100">Advanced</h3>
              <p class="text-xs text-muted-foreground mt-1">Configure tables, columns, metric types, time grains, and frequency</p>
            </div>
            <CollapsibleTrigger as-child>
              <Button variant="ghost" size="sm" class="w-9 p-0">
                <ChevronDown :class="['h-4 w-4 transition-transform', advancedFiltersOpen && 'rotate-180']" />
                <span class="sr-only">Toggle advanced filters</span>
              </Button>
            </CollapsibleTrigger>
          </div>

          <CollapsibleContent class="CollapsibleContent p-4 border-t">
            <MetricRecommendFilterSection
              v-model:table-selections="tableSelections"
              v-model:metric-types="selectedMetricTypes"
              v-model:time-grains="selectedTimeGrains"
              v-model:time-window-days="timeWindowDays"
              :schema="schema"
              :is-loading-schema="isLoadingSchema"
            />
          </CollapsibleContent>
        </Collapsible>

        <Separator />

        <!-- Generate Button -->
        <div class="flex justify-end">
          <Button 
            @click="handleGenerate" 
            :disabled="!canGenerate"
            size="lg"
            class="hover:bg-fuchsia-600 hover:dark:bg-fuchsia-600 hover:text-white cursor-pointer"
          >
            <Loader2 v-if="isGenerating" class="h-4 w-4 mr-2 animate-spin" />
            <Sparkles v-else class="h-4 w-4 mr-2" />
            {{ isGenerating ? 'Generating...' : 'Generate' }}
          </Button>
        </div>
      </CardContent>
    </Card>

    <!-- Step 2: Review -->
    <div v-if="step === 'review'" class="space-y-6 flex flex-col">
      <!-- Scroll sentinel for detecting when header becomes sticky -->
      <div ref="scrollSentinel" class="h-0" aria-hidden="true"></div>
      
      <!-- Summary Card -->
      <Card 
        class="sticky top-0 z-1000 transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
        :class="isScrolled ? 'w-fit justify-center self-center bg-background/20 backdrop-blur-xl shadow-lg scale-[0.98]' : 'scale-100'"
      >
        <CardContent 
          class="transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
          :class="isScrolled ? 'w-fit' : 'w-full'"
        >
          <div class="flex items-center justify-between gap-x-10">
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
                <span v-if="recommendationsMeta?.table_preview"> • {{ Object.keys(recommendationsMeta.table_preview).length }} tables</span>
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
                Add {{ selectedMetricIds.size }} Metrics
                <ChevronRight class="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Metrics List -->
      <div class="space-y-4">
        <MetricPreviewCard 
          v-for="metric in recommendedMetrics" 
          :key="metric.name"
          :metric="metric"
          :selected="selectedMetricIds.has(metric.name)"
          @toggle-select="(checked) => toggleMetric(metric.name, checked)"
        />
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

/* Collapsible animation styles */
.CollapsibleContent {
  overflow: hidden;
}
.CollapsibleContent[data-state="open"] {
  animation: slideDown 400ms cubic-bezier(0.0, 0.0, 0.2, 1);
}
.CollapsibleContent[data-state="closed"] {
  animation: slideUp 300ms cubic-bezier(0.4, 0.0, 1, 1);
}

@keyframes slideDown {
  from {
    height: 0;
  }
  to {
    height: var(--reka-collapsible-content-height);
  }
}

@keyframes slideUp {
  from {
    height: var(--reka-collapsible-content-height);
  }
  to {
    height: 0;
  }
}
</style>

