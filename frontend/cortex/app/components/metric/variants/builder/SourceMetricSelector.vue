<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <Label for="source-metric">
        Source Metric
        <span class="text-destructive">*</span>
      </Label>
      <Select
        :model-value="modelValue?.metric_id"
        @update:model-value="handleMetricSelect"
      >
        <SelectTrigger id="source-metric" :class="{ 'border-destructive': error }">
          <SelectValue placeholder="Select a metric to derive from">
            <span v-if="selectedMetric">{{ selectedMetric.title || selectedMetric.name }}</span>
          </SelectValue>
        </SelectTrigger>
        <SelectContent>
          <div v-if="loading" class="p-4 text-center">
            <Loader2 class="h-4 w-4 animate-spin mx-auto" />
            <p class="text-sm text-muted-foreground mt-2">Loading metrics...</p>
          </div>
          <div v-else-if="metrics.length === 0" class="p-4 text-center">
            <p class="text-sm text-muted-foreground">No metrics available</p>
          </div>
          <SelectItem
            v-for="metric in metrics"
            :key="metric.id"
            :value="metric.id"
          >
            <div class="flex flex-col">
              <span class="font-medium">{{ metric.title || metric.name }}</span>
              <span class="text-xs text-muted-foreground">
                {{ metric.description || 'No description' }}
              </span>
            </div>
          </SelectItem>
        </SelectContent>
      </Select>
      <p v-if="error" class="text-sm text-destructive">
        {{ error }}
      </p>
      <p v-else class="text-xs text-muted-foreground">
        The base metric to create a variant from
      </p>
    </div>

    <!-- Source Alias (optional) -->
    <div v-if="modelValue?.metric_id" class="space-y-2">
      <Label for="source-alias">
        Source Alias (optional)
      </Label>
      <Input
        id="source-alias"
        :model-value="modelValue?.alias"
        @update:model-value="handleAliasUpdate"
        placeholder="e.g., 'base', 'main'"
      />
      <p class="text-xs text-muted-foreground">
        Alias for the source metric in multi-source compositions
      </p>
    </div>

    <!-- Selected Metric Preview -->
    <Card v-if="selectedMetric" class="border-purple-200 dark:border-purple-800">
      <CardHeader class="pb-3">
        <CardTitle class="text-sm flex items-center gap-2">
          <CheckCircle2 class="h-4 w-4 text-green-600" />
          Selected Source
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Name:</span>
            <span class="font-medium">{{ selectedMetric.title || selectedMetric.name }}</span>
          </div>
          <div v-if="selectedMetric.measures" class="flex justify-between">
            <span class="text-muted-foreground">Measures:</span>
            <span>{{ selectedMetric.measures.length }}</span>
          </div>
          <div v-if="selectedMetric.dimensions" class="flex justify-between">
            <span class="text-muted-foreground">Dimensions:</span>
            <span>{{ selectedMetric.dimensions.length }}</span>
          </div>
          <div v-if="selectedMetric.filters" class="flex justify-between">
            <span class="text-muted-foreground">Filters:</span>
            <span>{{ selectedMetric.filters.length }}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Loader2, CheckCircle2 } from 'lucide-vue-next'
import { useMetrics } from '~/composables/useMetrics'
import { useEnvironments } from '~/composables/useEnvironments'
import type { MetricRef } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  modelValue: MetricRef | null
  error?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: MetricRef | null]
}>()

const { selectedEnvironmentId } = useEnvironments()
const { fetchMetrics, metrics: metricsRef, loading } = useMetrics()

const metrics = computed(() => metricsRef.value || [])
const selectedMetric = ref<SemanticMetric | null>(null)

const handleMetricSelect = (metricId: string) => {
  const metric = metrics.value.find(m => m.id === metricId)
  if (metric) {
    selectedMetric.value = metric
    emit('update:modelValue', {
      metric_id: metricId,
      alias: props.modelValue?.alias || undefined
    })
  }
}

const handleAliasUpdate = (alias: string) => {
  if (props.modelValue) {
    emit('update:modelValue', {
      ...props.modelValue,
      alias: alias || undefined
    })
  }
}

onMounted(async () => {
  if (selectedEnvironmentId.value) {
    await fetchMetrics(selectedEnvironmentId.value)
  }

  // If modelValue already has a metric_id, find and set the selected metric
  if (props.modelValue?.metric_id) {
    selectedMetric.value = metrics.value.find(m => m.id === props.modelValue?.metric_id) || null
  }
})

watch(() => props.modelValue?.metric_id, (newId) => {
  if (newId) {
    selectedMetric.value = metrics.value.find(m => m.id === newId) || null
  } else {
    selectedMetric.value = null
  }
})
</script>
