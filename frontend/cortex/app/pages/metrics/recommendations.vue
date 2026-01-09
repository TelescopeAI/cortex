<script setup lang="ts">
import { ref, computed, watch, shallowRef } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Separator } from '~/components/ui/separator'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { Sparkles, Database, Target, Loader2, CheckCircle2, XCircle, ArrowLeft, ChevronRight } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'
import { toast } from 'vue-sonner'
import MetricPreviewCard from '~/components/recommend/MetricPreviewCard.vue'

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

// Filters / options
const includeTablesInput = ref<string>('')
const excludeTablesInput = ref<string>('')
const includeColumnsInput = ref<string>('')
const excludeColumnsInput = ref<string>('')
const metricTypesSelected = ref<Set<string>>(new Set(['count', 'sum', 'avg', 'min', 'max', 'count_distinct', 'boolean']))
const timeWindowsInput = ref<string>('30')
const grainsInput = ref<string>('day,week,month,quarter,year')

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

const includeTables = computed(() => parseCsv(includeTablesInput.value))
const excludeTables = computed(() => parseCsv(excludeTablesInput.value))
const includeColumns = computed(() => parseCsv(includeColumnsInput.value))
const excludeColumns = computed(() => parseCsv(excludeColumnsInput.value))
const timeWindows = computed(() => parseNumberCsv(timeWindowsInput.value))
const grains = computed(() => parseCsv(grainsInput.value))
const metricTypes = computed(() => Array.from(metricTypesSelected.value))

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
        includeTables: includeTables.value,
        excludeTables: excludeTables.value,
        includeColumns: includeColumns.value,
        excludeColumns: excludeColumns.value,
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

// Helpers
function parseCsv(value: string): string[] | undefined {
  if (!value) return undefined
  const parts = value.split(',').map(v => v.trim()).filter(Boolean)
  return parts.length ? parts : undefined
}

function parseNumberCsv(value: string): number[] | undefined {
  if (!value) return undefined
  const parts = value
    .split(',')
    .map(v => v.trim())
    .filter(Boolean)
    .map(v => Number(v))
    .filter(v => !Number.isNaN(v) && v > 0)
  return parts.length ? parts : undefined
}

function toggleMetricType(type: string, checked: boolean | 'indeterminate') {
  const next = new Set(metricTypesSelected.value)
  if (checked === true) {
    next.add(type)
  } else {
    next.delete(type)
  }
  metricTypesSelected.value = next
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

        <Separator />

        <!-- Filters -->
        <div class="grid gap-4 md:grid-cols-2">
          <div class="space-y-2">
            <label class="text-sm font-medium">Include Tables (comma-separated)</label>
            <input v-model="includeTablesInput" class="input" placeholder="orders, customers" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Exclude Tables (comma-separated)</label>
            <input v-model="excludeTablesInput" class="input" placeholder="tmp_logs" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Include Columns (comma-separated)</label>
            <input v-model="includeColumnsInput" class="input" placeholder="orders.amount, status" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Exclude Columns (comma-separated)</label>
            <input v-model="excludeColumnsInput" class="input" placeholder="orders.debug_flag" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Metric Types</label>
            <div class="flex flex-wrap gap-2">
              <label v-for="type in ['count','sum','avg','min','max','count_distinct','boolean']" :key="type" class="flex items-center space-x-1 text-sm">
                <input
                  type="checkbox"
                  :checked="metricTypesSelected.has(type)"
                  @change="(e: any) => toggleMetricType(type, e.target.checked)"
                />
                <span>{{ type }}</span>
              </label>
            </div>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Time Windows (days, comma-separated)</label>
            <input v-model="timeWindowsInput" class="input" placeholder="30,90" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Time Grains (comma-separated)</label>
            <input v-model="grainsInput" class="input" placeholder="day,week,month,quarter,year" />
          </div>
        </div>

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
</style>

