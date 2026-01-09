<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Separator } from '~/components/ui/separator'
import { ScrollArea } from '~/components/ui/scroll-area'
import { Sparkles, Database, Target, Loader2, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  dashboardId?: string
  initialDataSourceId?: string
  initialDataModelId?: string
  compact?: boolean
}

interface Emits {
  (e: 'select', metric: SemanticMetric, dataSourceId: string, dataModelId: string): void
}

const props = withDefaults(defineProps<Props>(), {
  dashboardId: undefined,
  initialDataSourceId: '',
  initialDataModelId: '',
  compact: false
})
const emit = defineEmits<Emits>()

// Composables
const { dataSources } = useDataSources()
const { models, fetchModels } = useDataModels()
const { recommendMetrics } = useMetrics()
const { selectedEnvironmentId } = useEnvironments()

// State - initialize from props if provided
const selectedDataSource = ref<string>(props.initialDataSourceId || '')
const selectedDataModel = ref<string>(props.initialDataModelId || '')
const recommendedMetrics = ref<SemanticMetric[]>([])
const isGenerating = ref(false)
const error = ref<string | null>(null)
const hasGenerated = ref(false)

// Watch for prop changes to update selections
watch(() => props.initialDataSourceId, (newVal) => {
  if (newVal && newVal !== selectedDataSource.value) {
    selectedDataSource.value = newVal
  }
})

watch(() => props.initialDataModelId, (newVal) => {
  if (newVal && newVal !== selectedDataModel.value) {
    selectedDataModel.value = newVal
  }
})

// Computed
const canGenerate = computed(() => {
  return selectedDataSource.value && selectedDataModel.value && !isGenerating.value
})

const selectedDataSourceName = computed(() => {
  return dataSources.value?.find(ds => ds.id === selectedDataSource.value)?.name || 'Unknown'
})

const selectedDataModelName = computed(() => {
  return models.value?.find(m => m.id === selectedDataModel.value)?.name || 'Unknown'
})

// Methods
async function handleGenerate() {
  if (!canGenerate.value || !selectedEnvironmentId.value) return

  isGenerating.value = true
  error.value = null
  
  try {
    const { metrics } = await recommendMetrics(
      selectedEnvironmentId.value,
      selectedDataSource.value,
      selectedDataModel.value
    )
    
    recommendedMetrics.value = metrics
    hasGenerated.value = true
    
    if (metrics.length === 0) {
      error.value = 'No recommendations generated for the selected data source schema.'
    }
  } catch (err: any) {
    console.error('Failed to generate recommendations:', err)
    error.value = err?.data?.detail || err.message || 'An unexpected error occurred'
  } finally {
    isGenerating.value = false
  }
}

function handleSelectMetric(metric: SemanticMetric) {
  emit('select', metric, selectedDataSource.value, selectedDataModel.value)
}

function getMetricTitle(metric: SemanticMetric): string {
  return metric.title || metric.name
}

function getMetricDescription(metric: SemanticMetric): string {
  return metric.description || 'No description'
}

// Initialize data
onMounted(() => {
  if (selectedEnvironmentId.value) {
    fetchModels(selectedEnvironmentId.value)
  }
})

// Watch for environment changes
watch(selectedEnvironmentId, (newEnvId) => {
  if (newEnvId) {
    fetchModels(newEnvId)
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Selection Controls -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="flex flex-col gap-2"
       :class="compact ? 'flex-row gap-x-6' : ''">
            <!-- Data Source Selection -->
            <div class="space-y-2">
              <label class="text-sm font-medium">Data Source</label>
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
            </div>

            <!-- Data Model Selection -->
            <div class="space-y-2">
              <label class="text-sm font-medium">Data Model</label>
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
            </div>
            </div>

            <!-- Generate Button -->
            <div class="flex items-center justify-end">
              <Button 
                @click="handleGenerate" 
                :disabled="!canGenerate"
                size="sm"
                class="flex-shrink-0"
              >
                <Loader2 v-if="isGenerating" class="h-4 w-4 mr-2 animate-spin" />
                <Sparkles v-else class="h-4 w-4 mr-2" />
                {{ isGenerating ? 'Generating...' : 'Generate' }}
              </Button>
            </div>
      </div>
    

    <Separator v-if="hasGenerated" />

    <!-- Error State -->
    <div v-if="error && !isGenerating" class="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/30">
      <AlertCircle class="h-4 w-4 text-destructive flex-shrink-0" />
      <p class="text-sm text-destructive">{{ error }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="isGenerating" class="flex items-center justify-center py-8">
      <div class="text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-3"></div>
        <p class="text-sm text-muted-foreground">Analyzing schema and generating recommendations...</p>
      </div>
    </div>

    <!-- Recommendations List -->
    <ScrollArea v-if="recommendedMetrics.length > 0 && !isGenerating" class="h-[300px]">
      <div class="space-y-3 pr-4">
        <Card 
          v-for="metric in recommendedMetrics" 
          :key="metric.name"
          class="cursor-pointer hover:bg-muted/50 hover:border-primary/50 transition-colors"
          @click="handleSelectMetric(metric)"
        >
          <CardContent class="p-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <h4 class="font-medium text-sm truncate">{{ getMetricTitle(metric) }}</h4>
                <p class="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {{ getMetricDescription(metric) }}
                </p>
                
                <!-- Metric Details -->
                <div class="flex flex-wrap gap-2 mt-2">
                  <Badge v-if="metric.measures?.length" variant="outline" class="text-xs">
                    {{ metric.measures.length }} measure{{ metric.measures.length > 1 ? 's' : '' }}
                  </Badge>
                  <Badge v-if="metric.dimensions?.length" variant="outline" class="text-xs">
                    {{ metric.dimensions.length }} dimension{{ metric.dimensions.length > 1 ? 's' : '' }}
                  </Badge>
                  <Badge v-if="metric.filters?.length" variant="secondary" class="text-xs">
                    {{ metric.filters.length }} filter{{ metric.filters.length > 1 ? 's' : '' }}
                  </Badge>
                </div>
              </div>
              
              <Button size="sm" variant="ghost" class="flex-shrink-0">
                <CheckCircle2 class="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>

    <!-- Empty State (after generation) -->
    <div v-if="hasGenerated && recommendedMetrics.length === 0 && !isGenerating && !error" class="text-center py-8">
      <div class="w-12 h-12 mx-auto bg-muted rounded-full flex items-center justify-center mb-3">
        <Sparkles class="w-6 h-6 text-muted-foreground" />
      </div>
      <h4 class="font-medium mb-1">No recommendations found</h4>
      <p class="text-sm text-muted-foreground">
        Try selecting a different data source or data model.
      </p>
    </div>

    <!-- Initial State (before generation) -->
    <div v-if="!hasGenerated && !isGenerating" class="text-center py-8">
      <div class="w-12 h-12 mx-auto bg-muted rounded-full flex items-center justify-center mb-3">
        <Sparkles class="w-6 h-6 text-muted-foreground" />
      </div>
      <h4 class="font-medium mb-1">Generate Metrics</h4>
      <p class="text-sm text-muted-foreground max-w-sm mx-auto">
        Select a data source and data model above, then click generate to recommendations.
      </p>
    </div>
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

