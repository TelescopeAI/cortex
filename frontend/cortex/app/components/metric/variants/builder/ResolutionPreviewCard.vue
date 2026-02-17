<template>
  <Card class="border-purple-200 dark:border-purple-800">
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <Eye class="h-5 w-5 text-purple-600 dark:text-purple-400" />
        Resolution Preview
      </CardTitle>
      <CardDescription>
        Preview how this variant will be resolved by the compiler
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="!sourceMetric" class="text-center py-8 text-muted-foreground">
        <AlertCircle class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">Select a source metric to see preview</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Summary Stats -->
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center p-4 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ estimatedMeasures }}</div>
            <div class="text-xs text-muted-foreground">Measures</div>
          </div>
          <div class="text-center p-4 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ estimatedDimensions }}</div>
            <div class="text-xs text-muted-foreground">Dimensions</div>
          </div>
        </div>

        <!-- Changes Summary -->
        <div class="space-y-2">
          <Label class="text-sm">Changes</Label>
          <div class="space-y-1 text-sm">
            <div v-if="hasInclusion" class="flex items-center gap-2 text-blue-600 dark:text-blue-400">
              <Filter class="h-4 w-4" />
              <span>Inclusion whitelist active</span>
            </div>
            <div v-if="excludeCount > 0" class="flex items-center gap-2 text-red-600 dark:text-red-400">
              <Minus class="h-4 w-4" />
              <span>{{ excludeCount }} components excluded</span>
            </div>
            <div v-if="scalarOverrides > 0" class="flex items-center gap-2 text-orange-600 dark:text-orange-400">
              <Settings class="h-4 w-4" />
              <span>{{ scalarOverrides }} scalar overrides</span>
            </div>
            <div v-if="!hasInclusion && excludeCount === 0 && scalarOverrides === 0" class="flex items-center gap-2 text-muted-foreground">
              <CheckCircle2 class="h-4 w-4" />
              <span>No modifications</span>
            </div>
          </div>
        </div>

        <!-- Fetch Resolved Button -->
        <Button
          @click="fetchResolved"
          :disabled="loading || !canResolve"
          class="w-full"
          variant="outline"
        >
          <Loader2 v-if="loading" class="h-4 w-4 mr-2 animate-spin" />
          <Eye v-else class="h-4 w-4 mr-2" />
          {{ loading ? 'Resolving...' : 'Fetch Resolved Metric' }}
        </Button>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import { Eye, AlertCircle, Filter, Minus, Settings, CheckCircle2, Loader2 } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { IncludedComponents, MetricOverrides } from '~/types/metric_variants'

interface Props {
  sourceMetric: SemanticMetric | null
  inclusion: IncludedComponents | null
  overrides: MetricOverrides | null
}

const props = defineProps<Props>()

const loading = ref(false)

// Estimate counts based on source and overrides
const estimatedMeasures = computed(() => {
  if (!props.sourceMetric) return 0

  let count = props.sourceMetric.measures?.length || 0

  // Apply inclusion whitelist
  if (props.inclusion?.measures) {
    count = props.inclusion.measures.length
  }

  // Apply exclusions
  const excluded = props.overrides?.exclude?.measures?.length || 0
  count = Math.max(0, count - excluded)

  // Add new measures
  const added = props.overrides?.add?.measures?.length || 0
  count += added

  return count
})

const estimatedDimensions = computed(() => {
  if (!props.sourceMetric) return 0

  let count = props.sourceMetric.dimensions?.length || 0

  // Apply inclusion whitelist
  if (props.inclusion?.dimensions) {
    count = props.inclusion.dimensions.length
  }

  // Apply exclusions
  const excluded = props.overrides?.exclude?.dimensions?.length || 0
  count = Math.max(0, count - excluded)

  // Add new dimensions
  const added = props.overrides?.add?.dimensions?.length || 0
  count += added

  return count
})

const hasInclusion = computed(() => {
  return props.inclusion !== null
})

const excludeCount = computed(() => {
  if (!props.overrides?.exclude) return 0

  return (
    (props.overrides.exclude.measures?.length || 0) +
    (props.overrides.exclude.dimensions?.length || 0) +
    (props.overrides.exclude.filters?.length || 0) +
    (props.overrides.exclude.joins?.length || 0)
  )
})

const scalarOverrides = computed(() => {
  if (!props.overrides) return 0

  let count = 0
  if (props.overrides.table_name) count++
  if (props.overrides.limit !== undefined) count++
  if (props.overrides.grouped !== undefined) count++
  if (props.overrides.ordered !== undefined) count++

  return count
})

const canResolve = computed(() => {
  return props.sourceMetric !== null
})

const fetchResolved = async () => {
  loading.value = true
  // TODO: Call compiler API to get resolved metric
  setTimeout(() => {
    loading.value = false
  }, 1000)
}
</script>
