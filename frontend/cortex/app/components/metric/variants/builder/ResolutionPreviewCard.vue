<template>
  <Card class="gap-y-0">
    <CardHeader class="pb-3">
      <CardTitle class="text-sm font-medium flex items-center gap-2">
        <GitCompareArrows class="h-4 w-4 text-purple-600 dark:text-purple-400" />
        Changes
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div v-if="!sourceMetric" class="text-center py-6 text-muted-foreground">
        <AlertCircle class="h-6 w-6 mx-auto mb-2 opacity-50" />
        <p class="text-sm">Select a source metric to see changes</p>
      </div>

      <div v-else-if="!hasAnyChanges" class="text-center py-6 text-muted-foreground">
        <CheckCircle2 class="h-6 w-6 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No modifications — variant inherits everything from source</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Measures diff -->
        <DiffSection
          v-if="measuresDiff.hasChanges"
          label="Measures"
          :added="measuresDiff.added"
          :removed="measuresDiff.removed"
          :replaced="measuresDiff.replaced"
          :included="measuresDiff.included"
          :source-names="measuresDiff.sourceNames"
        />

        <!-- Dimensions diff -->
        <DiffSection
          v-if="dimensionsDiff.hasChanges"
          label="Dimensions"
          :added="dimensionsDiff.added"
          :removed="dimensionsDiff.removed"
          :replaced="dimensionsDiff.replaced"
          :included="dimensionsDiff.included"
          :source-names="dimensionsDiff.sourceNames"
        />

        <!-- Filters diff -->
        <DiffSection
          v-if="filtersDiff.hasChanges"
          label="Filters"
          :added="filtersDiff.added"
          :removed="filtersDiff.removed"
          :replaced="filtersDiff.replaced"
          :included="filtersDiff.included"
          :source-names="filtersDiff.sourceNames"
        />

        <!-- Joins diff -->
        <DiffSection
          v-if="joinsDiff.hasChanges"
          label="Joins"
          :added="joinsDiff.added"
          :removed="joinsDiff.removed"
          :replaced="joinsDiff.replaced"
          :included="joinsDiff.included"
          :source-names="joinsDiff.sourceNames"
        />

        <!-- Scalar overrides -->
        <div v-if="scalarChanges.length > 0" class="space-y-1.5">
          <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide">Settings</p>
          <div v-for="change in scalarChanges" :key="change.field" class="flex items-center gap-2 text-sm">
            <span class="inline-flex items-center gap-1 text-orange-600 dark:text-orange-400">
              <ArrowRight class="h-3 w-3" />
              <span class="font-medium">{{ change.field }}</span>
            </span>
            <span class="text-muted-foreground">{{ change.from }}</span>
            <ArrowRight class="h-3 w-3 text-muted-foreground" />
            <span class="font-medium">{{ change.to }}</span>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { GitCompareArrows, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-vue-next'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { IncludedComponents, MetricOverrides } from '~/types/metric_variants'
import DiffSection from './DiffSection.vue'

interface Props {
  sourceMetric: SemanticMetric | null
  inclusion: IncludedComponents | null
  overrides: MetricOverrides | null
}

const props = defineProps<Props>()

interface ComponentDiff {
  hasChanges: boolean
  sourceNames: string[]
  added: string[]
  removed: string[]
  replaced: string[]
  included: string[] | null // null = no inclusion filter (all inherited)
}

function buildDiff(
  sourceItems: any[] | undefined,
  inclusionList: string[] | undefined,
  excludeList: string[] | undefined,
  addItems: any[] | undefined,
  replaceItems: any[] | undefined
): ComponentDiff {
  const sourceNames = (sourceItems || []).map((item: any) => item.name || item.toString())
  const added = (addItems || []).map((item: any) => item.name || item.toString())
  const replaced = (replaceItems || []).map((item: any) => item.name || item.toString())
  const removed = excludeList || []
  const included = inclusionList || null

  const hasChanges =
    added.length > 0 ||
    removed.length > 0 ||
    replaced.length > 0 ||
    included !== null

  return { hasChanges, sourceNames, added, removed, replaced, included }
}

const measuresDiff = computed(() =>
  buildDiff(
    props.sourceMetric?.measures,
    props.inclusion?.measures,
    props.overrides?.exclude?.measures,
    props.overrides?.add?.measures,
    props.overrides?.replace?.measures
  )
)

const dimensionsDiff = computed(() =>
  buildDiff(
    props.sourceMetric?.dimensions,
    props.inclusion?.dimensions,
    props.overrides?.exclude?.dimensions,
    props.overrides?.add?.dimensions,
    props.overrides?.replace?.dimensions
  )
)

const filtersDiff = computed(() =>
  buildDiff(
    props.sourceMetric?.filters,
    props.inclusion?.filters,
    props.overrides?.exclude?.filters,
    props.overrides?.add?.filters,
    props.overrides?.replace?.filters
  )
)

const joinsDiff = computed(() =>
  buildDiff(
    props.sourceMetric?.joins,
    props.inclusion?.joins,
    props.overrides?.exclude?.joins,
    props.overrides?.add?.joins,
    props.overrides?.replace?.joins
  )
)

const scalarChanges = computed(() => {
  if (!props.overrides || !props.sourceMetric) return []

  const changes: { field: string; from: string; to: string }[] = []

  if (props.overrides.table_name) {
    changes.push({
      field: 'table_name',
      from: props.sourceMetric.table_name || '(none)',
      to: props.overrides.table_name
    })
  }
  if (props.overrides.limit !== undefined) {
    changes.push({
      field: 'limit',
      from: String(props.sourceMetric.limit ?? '(none)'),
      to: String(props.overrides.limit)
    })
  }
  if (props.overrides.grouped !== undefined) {
    changes.push({
      field: 'grouped',
      from: String(props.sourceMetric.grouped ?? true),
      to: String(props.overrides.grouped)
    })
  }
  if (props.overrides.ordered !== undefined) {
    changes.push({
      field: 'ordered',
      from: String(props.sourceMetric.ordered ?? true),
      to: String(props.overrides.ordered)
    })
  }

  return changes
})

const hasAnyChanges = computed(() =>
  measuresDiff.value.hasChanges ||
  dimensionsDiff.value.hasChanges ||
  filtersDiff.value.hasChanges ||
  joinsDiff.value.hasChanges ||
  scalarChanges.value.length > 0
)
</script>
