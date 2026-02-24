<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <GitBranch class="h-5 w-5 text-purple-600 dark:text-purple-400" />
          {{ isEdit ? 'Edit' : 'Create' }} Variant
        </DialogTitle>
        <DialogDescription>
          {{ isEdit ? 'Modify variant configuration' : 'Create a new variant from a base metric' }}
        </DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto">
        <Tabs v-model="activeTab" class="w-full">
          <TabsList class="grid w-full grid-cols-5">
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
            <TabsTrigger value="preview" :disabled="!formData.source">
              <Eye class="h-4 w-4 mr-2" />
              Preview
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

          <!-- Preview Tab -->
          <TabsContent value="preview" class="mt-4 space-y-4">
            <MetricVariantsBuilderResolutionPreviewCard
              :source-metric="sourceMetricData"
              :inclusion="formData.inclusion"
              :overrides="formData.overrides"
            />

            <Alert>
              <AlertCircle class="h-4 w-4" />
              <AlertTitle>Advanced Features</AlertTitle>
              <AlertDescription>
                Derivations and multi-source composition will be available in a future update.
              </AlertDescription>
            </Alert>
          </TabsContent>
        </Tabs>
      </div>

      <DialogFooter class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Button
            v-if="activeTab !== 'basic'"
            variant="outline"
            @click="previousTab"
          >
            <ChevronLeft class="h-4 w-4 mr-2" />
            Previous
          </Button>
        </div>
        <div class="flex items-center gap-2">
          <Button
            variant="outline"
            @click="handleCancel"
          >
            Cancel
          </Button>
          <Button
            v-if="activeTab !== 'preview'"
            @click="nextTab"
            :disabled="!canProceed"
          >
            Next
            <ChevronRight class="h-4 w-4 ml-2" />
          </Button>
          <Button
            v-else
            @click="handleSubmit"
            :disabled="saving || !isValid"
          >
            <Loader2 v-if="saving" class="h-4 w-4 mr-2 animate-spin" />
            {{ isEdit ? 'Update' : 'Create' }} Variant
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { GitBranch, Info, Filter, Settings, Eye, AlertCircle, ChevronLeft, ChevronRight, Loader2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '~/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '~/components/ui/tabs'
import { Button } from '~/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '~/components/ui/alert'
import type { SemanticMetricVariant, MetricRef, IncludedComponents, MetricOverrides, VariantValidationErrors } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  open: boolean
  variant?: SemanticMetricVariant | null
  defaultSourceMetricId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'success': [variant: SemanticMetricVariant]
}>()

const { selectedEnvironmentId } = useEnvironments()
const { getMetric } = useMetrics()
const { createVariant, updateVariant } = useMetricVariants()
const { getDataSourceSchema } = useDataSources()

const activeTab = ref('basic')
const saving = ref(false)
const sourceMetricData = ref<SemanticMetric | null>(null)
const tableSchema = ref<any>(null)

const loadTableSchema = async (dataSourceId?: string) => {
  if (!dataSourceId) { tableSchema.value = null; return }
  try {
    tableSchema.value = await getDataSourceSchema(dataSourceId)
  } catch (error) {
    console.error('Failed to load table schema:', error)
    tableSchema.value = null
  }
}

const isEdit = computed(() => !!props.variant)

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

// Validation
const validationErrors = ref<VariantValidationErrors>({})

const canProceed = computed(() => {
  switch (activeTab.value) {
    case 'basic':
      return !!formData.value.basic.name.trim()
    case 'source':
      return !!formData.value.source?.metric_id
    default:
      return true
  }
})

const isValid = computed(() => {
  return (
    !!formData.value.basic.name.trim() &&
    !!formData.value.source?.metric_id
  )
})

// Tab navigation
const tabs = ['basic', 'source', 'inclusion', 'overrides', 'preview']

const nextTab = () => {
  const currentIndex = tabs.indexOf(activeTab.value)
  if (currentIndex < tabs.length - 1) {
    activeTab.value = tabs[currentIndex + 1]
  }
}

const previousTab = () => {
  const currentIndex = tabs.indexOf(activeTab.value)
  if (currentIndex > 0) {
    activeTab.value = tabs[currentIndex - 1]
  }
}

// Source change handler
const handleSourceChange = async (source: MetricRef | null) => {
  if (source?.metric_id && selectedEnvironmentId.value) {
    sourceMetricData.value = await getMetric(source.metric_id, selectedEnvironmentId.value)
    await loadTableSchema(sourceMetricData.value?.data_source_id)
  } else {
    sourceMetricData.value = null
    tableSchema.value = null
  }
}

// Inclusion change handler
const handleInclusionUpdate = (inclusion: IncludedComponents | null) => {
  console.log('Inclusion updated:', inclusion)
  formData.value.inclusion = inclusion
}

// Dialog handlers
const handleOpenChange = (open: boolean) => {
  emit('update:open', open)
  if (!open) {
    resetForm()
  }
}

const handleCancel = () => {
  emit('update:open', false)
  resetForm()
}

const handleSubmit = async () => {
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
      combine: formData.value.combine.length > 0 ? formData.value.combine : undefined
    }

    let result: SemanticMetricVariant | null

    if (isEdit.value && props.variant) {
      result = await updateVariant(
        props.variant.id,
        selectedEnvironmentId.value,
        variantData
      )
    } else {
      result = await createVariant(selectedEnvironmentId.value, variantData)
    }

    if (result) {
      toast.success(`Variant ${isEdit.value ? 'updated' : 'created'} successfully`)
      emit('success', result)
      emit('update:open', false)
      resetForm()
    } else {
      toast.error(`Failed to ${isEdit.value ? 'update' : 'create'} variant`)
    }
  } catch (error) {
    console.error('Failed to save variant:', error)
    toast.error(`Failed to ${isEdit.value ? 'update' : 'create'} variant`)
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  formData.value = {
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
  }
  activeTab.value = 'basic'
  sourceMetricData.value = null
  tableSchema.value = null
  validationErrors.value = {}
}

// Initialize form when editing or when default source is provided
watch(() => props.open, async (open) => {
  if (open) {
    if (props.variant) {
      // Editing existing variant
      formData.value = {
        basic: {
          name: props.variant.name,
          alias: props.variant.alias || '',
          description: props.variant.description || '',
          public: props.variant.public
        },
        source: props.variant.source,
        inclusion: props.variant.include || null,
        overrides: props.variant.overrides || null,
        derivations: props.variant.derivations || [],
        combine: props.variant.combine || []
      }

      if (props.variant.source.metric_id && selectedEnvironmentId.value) {
        sourceMetricData.value = await getMetric(
          props.variant.source.metric_id,
          selectedEnvironmentId.value
        )
        await loadTableSchema(sourceMetricData.value?.data_source_id)
      }
    } else if (props.defaultSourceMetricId && selectedEnvironmentId.value) {
      // Creating new variant with default source
      formData.value.source = {
        metric_id: props.defaultSourceMetricId
      }
      sourceMetricData.value = await getMetric(
        props.defaultSourceMetricId,
        selectedEnvironmentId.value
      )
      await loadTableSchema(sourceMetricData.value?.data_source_id)
    }
  }
})
</script>
