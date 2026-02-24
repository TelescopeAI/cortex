<template>
  <div class="container mx-auto py-6 px-4 space-y-6">
    <!-- Breadcrumb -->
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink href="/metrics">Metrics</BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbLink :href="`/metrics/${metricId}`">{{ sourceMetricData?.name || 'Metric' }}</BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbLink :href="`/metrics/${metricId}/variants`">Variants</BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>Create</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold flex items-center gap-2">
          <GitBranch class="h-6 w-6 text-purple-600 dark:text-purple-400" />
          {{ variantTitle }}
        </h1>
        <p class="text-sm text-muted-foreground mt-1">
          from {{ sourceMetricData?.name || 'source metric' }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="handleCancel">Cancel</Button>
        <Button @click="handleCreate" :disabled="saving || !isValid">
          <Loader2 v-if="saving" class="h-4 w-4 mr-2 animate-spin" />
          Add
        </Button>
      </div>
    </div>

    <!-- Main Layout: 60/40 split -->
    <div class="grid grid-cols-1 lg:grid-cols-6 gap-6">
      <!-- Left Panel: Config (50%) -->
      <div class="lg:col-span-3">
        <Card>
          <CardContent class="pt-4">
            <!-- Keyboard Shortcuts -->
            <div class="flex items-center gap-2 mb-4">
              <Button
                variant="outline"
                size="sm"
                :disabled="!canUndo"
                :class="{ 'ring-2 ring-primary ring-offset-1': metaZPressed && canUndo }"
                @click="undo"
              >
                <Undo2 class="h-3.5 w-3.5 mr-1.5" />
                Undo
                <kbd class="ml-1.5 pointer-events-none inline-flex h-5 select-none items-center gap-0.5 rounded border bg-muted px-1 font-mono text-[10px] font-medium text-muted-foreground">
                  <span class="text-xs">⌘</span>Z
                </kbd>
              </Button>
              <Button
                variant="outline"
                size="sm"
                :disabled="!canRedo"
                :class="{ 'ring-2 ring-primary ring-offset-1': metaShiftZPressed && canRedo }"
                @click="redo"
              >
                <Redo2 class="h-3.5 w-3.5 mr-1.5" />
                Redo
                <kbd class="ml-1.5 pointer-events-none inline-flex h-5 select-none items-center gap-0.5 rounded border bg-muted px-1 font-mono text-[10px] font-medium text-muted-foreground">
                  <span class="text-xs">⌘⇧</span>Z
                </kbd>
              </Button>
            </div>

            <Tabs v-model="activeTab" class="w-full">
              <TabsList class="grid w-full grid-cols-4">
                <TabsTrigger value="basic">
                  <Info class="h-4 w-4 mr-2" />
                  Basic
                </TabsTrigger>
                <TabsTrigger value="source" :disabled="!formData.basic.name">
                  <GitBranch class="h-4 w-4 mr-2" />
                  Source
                </TabsTrigger>
                <TabsTrigger value="inclusion" :disabled="!formData.source">
                  <Filter class="h-4 w-4 mr-2" />
                  Include
                </TabsTrigger>
                <TabsTrigger value="overrides" :disabled="!formData.source">
                  <Settings class="h-4 w-4 mr-2" />
                  Overrides
                </TabsTrigger>
              </TabsList>

              <!-- Basic Tab -->
              <TabsContent value="basic" class="mt-4">
                <MetricVariantsBuilderBasicInfoBuilder
                  v-model="formData.basic"
                  :errors="validationErrors.basic"
                />
              </TabsContent>

              <!-- Source Tab -->
              <TabsContent value="source" class="mt-4">
                <MetricVariantsBuilderSourceMetricSelector
                  v-model="formData.source"
                  :error="validationErrors.source"
                  @update:model-value="handleSourceChange"
                />
              </TabsContent>

              <!-- Inclusion Tab -->
              <TabsContent value="inclusion" class="mt-4">
                <MetricVariantsBuilderComponentInclusionBuilder
                  :inclusion="formData.inclusion"
                  :source-metric="sourceMetricData"
                  @update:inclusion="handleInclusionUpdate"
                />
              </TabsContent>

              <!-- Overrides Tab -->
              <TabsContent value="overrides" class="mt-4">
                <MetricVariantsBuilderOverrideContainer
                  v-model="formData.overrides"
                  :source-metric="sourceMetricData"
                  :table-schema="tableSchema"
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <!-- Changes (Before/After) -->
        <MetricVariantsBuilderResolutionPreviewCard
          :source-metric="sourceMetricData"
          :inclusion="formData.inclusion"
          :overrides="formData.overrides"
          class="mt-4"
        />
      </div>

      <!-- Right Panel: Preview (50%) -->
      <div class="lg:col-span-3">
        <!-- Results Viewer handles all states (loading, empty, error, success) -->
        <ExecutionResultViewer
          :execution-results="resultState"
          :compiled-query="compiledSQL || undefined"
          :is-preview="isPreviewMode"
          :on-diagnose="canAutoExecute ? handleDiagnose : undefined"
          @apply-fix="handleApplyFix"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, provide, nextTick, type Ref } from 'vue'
import { watchDebounced, useDebouncedRefHistory, useMagicKeys } from '@vueuse/core'
import { toast } from 'vue-sonner'
import {
  GitBranch, Info, Filter, Settings, Eye, Play, Code,
  Undo2, Redo2, Loader2
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '~/components/ui/tabs'
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList,
  BreadcrumbPage, BreadcrumbSeparator
} from '~/components/ui/breadcrumb'
import ExecutionResultViewer from '~/components/ExecutionResultViewer.vue'
import type {
  MetricRef, IncludedComponents, MetricOverrides, VariantValidationErrors,
  MetricVariantBaseRequest
} from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { SemanticMetricVariant } from '~/types/metric_variants'

const route = useRoute()
const router = useRouter()
const metricId = computed(() => route.params.id as string)

const { selectedEnvironmentId } = useEnvironments()
const { getMetric } = useMetrics()
const { createVariant, executeVariant, diagnoseVariant } = useMetricVariants()
const { getDataSourceSchema } = useDataSources()

// UI State
const activeTab = ref('basic')
const saving = ref(false)
const sourceMetricData = ref<SemanticMetric | null>(null)
const tableSchema = ref<any>(null)
const validationErrors = ref<VariantValidationErrors>({})

// Preview / Execution State
const previewLoading = ref(false)
const executeLoading = ref(false)
const compiledSQL = ref<string | null>(null)
const executionData = ref<Record<string, any>[] | null>(null)
const executionMetadata = ref<Record<string, any> | null>(null)
const executionError = ref<string | null>(null)

// Provide loading states to ExecutionResultViewer
provide('executionLoading', executeLoading)
provide('previewLoading', previewLoading)

const resultState = computed(() => {
  if (!compiledSQL.value && !executionData.value && !executionError.value) return null
  return {
    success: !executionError.value,
    data: executionData.value || [],
    metadata: executionMetadata.value || {},
    errors: executionError.value ? [executionError.value] : [],
  }
})

const isPreviewMode = computed(() => !executionData.value && (!!compiledSQL.value || !!executionError.value))

// Form data
const formData = ref<{
  basic: {
    name: string
    alias: string
    description: string
    public: boolean
  }
  source: MetricRef | null
  inclusion: IncludedComponents | null
  overrides: MetricOverrides | null
  derivations: any[]
  combine: MetricRef[]
}>({
  basic: {
    name: '',
    alias: '',
    description: '',
    public: true
  },
  source: null,
  inclusion: null,
  overrides: null,
  derivations: [],
  combine: []
})

// Undo / Redo with debounced history
const { undo, redo, canUndo, canRedo } = useDebouncedRefHistory(formData, {
  deep: true,
  debounce: 500,
  capacity: 50,
})

// Keyboard shortcuts with reactive visual feedback
const keys = useMagicKeys()

const metaZPressed = computed(() => !!(keys['Meta+z'] as Ref<boolean> | undefined)?.value)
const metaShiftZPressed = computed(() => !!(keys['Meta+Shift+z'] as Ref<boolean> | undefined)?.value)

watch(metaZPressed, (pressed) => {
  if (pressed && canUndo.value) undo()
})
watch(metaShiftZPressed, (pressed) => {
  if (pressed && canRedo.value) redo()
})

// Validation
const isValid = computed(() => {
  return (
    !!formData.value.basic.name.trim() &&
    !!formData.value.source?.metric_id
  )
})

const canPreview = computed(() => {
  return isValid.value && !!selectedEnvironmentId.value
})

// Separate validation for auto-execute (doesn't require name)
const canAutoExecute = computed(() => {
  return !!formData.value.source?.metric_id && !!selectedEnvironmentId.value
})

// Dynamic title based on variant name
const variantTitle = computed(() => {
  return formData.value.basic.name.trim() || 'New Variant'
})

// Build inline variant request from form data
const buildInlineVariant = (): MetricVariantBaseRequest | null => {
  if (!formData.value.source?.metric_id) return null

  return {
    name: formData.value.basic.name.trim() || 'preview',  // Fallback name for preview
    alias: formData.value.basic.alias.trim() || undefined,
    description: formData.value.basic.description.trim() || undefined,
    source: formData.value.source,
    overrides: formData.value.overrides || undefined,
    include: formData.value.inclusion || undefined,
    derivations: formData.value.derivations.length > 0 ? formData.value.derivations : undefined,
    combine: formData.value.combine.length > 0 ? formData.value.combine : undefined,
    public: formData.value.basic.public,
  }
}

// Auto-execute with fallback to preview SQL
const autoExecuteOrPreview = async () => {
  if (!canAutoExecute.value) return
  try {
    await onExecute()
  } catch {
    await onPreviewSQL()
  }
}

// Diagnose callback for ExecutionResultError
const handleDiagnose = async () => {
  const variant = buildInlineVariant()
  if (!variant || !selectedEnvironmentId.value || !sourceMetricData.value) {
    throw new Error('Missing variant definition, environment, or source metric')
  }
  // The backend SemanticMetricVariant model requires these binding fields
  const enrichedVariant = {
    ...variant,
    environment_id: selectedEnvironmentId.value,
    data_model_id: sourceMetricData.value.data_model_id,
    data_source_id: sourceMetricData.value.data_source_id,
    source_id: sourceMetricData.value.id,
  }
  return diagnoseVariant({
    variant: enrichedVariant,
    environment_id: selectedEnvironmentId.value,
  })
}

// Helper to recursively remove null/undefined values from an object
const removeNullValues = (obj: any): any => {
  if (obj === null || obj === undefined) return undefined
  if (Array.isArray(obj)) return obj.map(removeNullValues).filter(v => v !== undefined)
  if (typeof obj === 'object') {
    const cleaned: Record<string, any> = {}
    for (const [key, value] of Object.entries(obj)) {
      const cleanedValue = removeNullValues(value)
      if (cleanedValue !== null && cleanedValue !== undefined) {
        cleaned[key] = cleanedValue
      }
    }
    return Object.keys(cleaned).length > 0 ? cleaned : undefined
  }
  return obj
}

// Apply fix from doctor suggestion
const handleApplyFix = (fixed: Record<string, any>) => {
  let applied = false

  if (fixed.source) {
    formData.value.source = fixed.source
    applied = true
  }
  if (fixed.overrides !== undefined) {
    // Remove null values to prevent empty CONFIG cards
    const cleanedOverrides = removeNullValues(fixed.overrides)
    if (cleanedOverrides) {
      formData.value.overrides = cleanedOverrides
      applied = true
    }
  }
  if (fixed.include !== undefined) {
    formData.value.inclusion = fixed.include
    applied = true
  }
  if (fixed.derivations !== undefined) {
    formData.value.derivations = fixed.derivations
    applied = true
  }
  if (fixed.combine !== undefined) {
    formData.value.combine = fixed.combine
    applied = true
  }

  if (applied) {
    toast.success('Fix applied — re-executing automatically.')
    nextTick(() => autoExecuteOrPreview())
  } else {
    toast.warning('No applicable changes found in fix suggestion.')
  }
}

// Load table schema for a data source
const loadTableSchema = async (dataSourceId?: string) => {
  if (!dataSourceId) { tableSchema.value = null; return }
  try {
    tableSchema.value = await getDataSourceSchema(dataSourceId)
  } catch (error) {
    console.error('Failed to load table schema:', error)
    tableSchema.value = null
  }
}

// Source change handler — reset inclusion/overrides (watch will trigger auto-execute)
const handleSourceChange = async (source: MetricRef | null) => {
  if (source?.metric_id && selectedEnvironmentId.value) {
    sourceMetricData.value = await getMetric(source.metric_id, selectedEnvironmentId.value)
    await loadTableSchema(sourceMetricData.value?.data_source_id)
    // Reset inclusion and overrides — old values reference the previous source metric
    formData.value.inclusion = null
    formData.value.overrides = null
    // Watch will trigger auto-execute
  } else {
    sourceMetricData.value = null
    tableSchema.value = null
    formData.value.inclusion = null
    formData.value.overrides = null
  }
}

// Inclusion change handler (watch will trigger auto-execute)
const handleInclusionUpdate = (inclusion: IncludedComponents | null) => {
  formData.value.inclusion = inclusion
  // Watch will trigger auto-execute after debounce
}

// Preview SQL (preview mode — generates query without executing)
const onPreviewSQL = async () => {
  const variant = buildInlineVariant()
  if (!variant || !selectedEnvironmentId.value) return

  previewLoading.value = true
  executionError.value = null

  try {
    const result = await executeVariant({
      environment_id: selectedEnvironmentId.value,
      variant,
      preview: true,
    })

    if (result) {
      if (result.success === false) {
        executionError.value = result.errors?.join('\n') || 'Preview failed'
      } else {
        compiledSQL.value = result.sql || null
        if (result.metadata) {
          executionMetadata.value = result.metadata
        }
      }
    }
  } catch (err) {
    executionError.value = err instanceof Error ? err.message : 'Failed to preview SQL'
  } finally {
    previewLoading.value = false
  }
}

// Execute variant (full execution — returns data)
const onExecute = async () => {
  const variant = buildInlineVariant()
  if (!variant || !selectedEnvironmentId.value) return

  executeLoading.value = true
  executionError.value = null
  executionData.value = null

  try {
    const result = await executeVariant({
      environment_id: selectedEnvironmentId.value,
      variant,
      preview: false,
    })

    if (result) {
      if (result.success === false) {
        executionError.value = result.errors?.join('\n') || 'Execution failed'
        toast.error('Execution failed')
      } else {
        executionData.value = result.data || null
        executionMetadata.value = result.metadata || null
        compiledSQL.value = result.sql || compiledSQL.value
        toast.success(`Executed successfully — ${result.metadata?.row_count ?? 0} rows returned`)
      }
    }
  } catch (err) {
    executionError.value = err instanceof Error ? err.message : 'Failed to execute variant'
    toast.error(executionError.value)
  } finally {
    executeLoading.value = false
  }
}

// Track only execution-relevant fields (exclude basic info like name, alias, description)
const executionRelevantData = computed(() => ({
  source: formData.value.source,
  inclusion: formData.value.inclusion,
  overrides: formData.value.overrides,
  derivations: formData.value.derivations,
  combine: formData.value.combine,
}))

// Debounced watcher: only trigger on changes that affect query execution
watchDebounced(
  executionRelevantData,
  async () => {
    // Always trigger preview if source is selected (removed gate to fix stuck preview)
    if (formData.value.source?.metric_id) {
      await autoExecuteOrPreview()
    }
  },
  { debounce: 500, deep: true }
)

// Create variant handler
const handleCreate = async () => {
  if (!isValid.value || !selectedEnvironmentId.value) return

  saving.value = true
  validationErrors.value = {}

  try {
    const variantData: Partial<SemanticMetricVariant> = {
      name: formData.value.basic.name.trim(),
      alias: formData.value.basic.alias.trim() || undefined,
      description: formData.value.basic.description.trim() || undefined,
      public: formData.value.basic.public,
      source: formData.value.source!,
      include: formData.value.inclusion || undefined,
      overrides: formData.value.overrides || undefined,
      derivations: formData.value.derivations.length > 0 ? formData.value.derivations : undefined,
      combine: formData.value.combine.length > 0 ? formData.value.combine : undefined,
    }

    const result = await createVariant(selectedEnvironmentId.value, variantData)

    if (result) {
      toast.success('Variant created successfully')
      router.push(`/metrics/${metricId.value}/variants/${result.id}`)
    } else {
      toast.error('Failed to create variant')
    }
  } catch (err) {
    console.error('Failed to create variant:', err)
    toast.error('Failed to create variant')
  } finally {
    saving.value = false
  }
}

// Cancel handler
const handleCancel = () => {
  router.push(`/metrics/${metricId.value}/variants`)
}

// Pre-populate source metric from URL param and auto-execute
onMounted(async () => {
  if (metricId.value && selectedEnvironmentId.value) {
    formData.value.source = { metric_id: metricId.value }
    sourceMetricData.value = await getMetric(metricId.value, selectedEnvironmentId.value)
    await loadTableSchema(sourceMetricData.value?.data_source_id)
    await autoExecuteOrPreview()
  }
})

// Watch for environment changes
watch(selectedEnvironmentId, async (newEnvId) => {
  if (newEnvId && metricId.value) {
    sourceMetricData.value = await getMetric(metricId.value, newEnvId)
  }
})
</script>
