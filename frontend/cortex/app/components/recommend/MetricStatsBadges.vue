<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '~/components/ui/badge'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  metric: SemanticMetric
}

const props = defineProps<Props>()

// Computed properties for metric stats
const metricStats = computed(() => {
  return {
    measures: (props.metric.measures?.length ?? 0),
    dimensions: (props.metric.dimensions?.length ?? 0),
    filters: (props.metric.filters?.length ?? 0)
  }
})

// Determine if this is a comparison metric (has dimensions) or single value
const isComparisonMetric = computed(() => {
  return metricStats.value.dimensions > 0
})

const metricTypeBadge = computed(() => {
  return isComparisonMetric.value ? 'Comparison' : 'Single Value'
})

const metricTypeVariant = computed(() => {
  return isComparisonMetric.value ? 'default' : 'secondary'
})
</script>

<template>
  <div class="space-y-3">
    <!-- Metric Type Badge -->
    <div class="flex items-center space-x-2 flex-wrap gap-2">
      <Badge :variant="metricTypeVariant">
        {{ metricTypeBadge }}
      </Badge>
      <Badge v-if="metric.table_name" variant="outline" class="text-xs">
        {{ metric.table_name }}
      </Badge>
    </div>

    <!-- Metric Stats -->
    <div class="flex flex-col space-y-1 text-xs text-muted-foreground">
      <span v-if="metricStats.measures > 0">
        📊 {{ metricStats.measures }} measure{{ metricStats.measures !== 1 ? 's' : '' }}
      </span>
      <span v-if="metricStats.dimensions > 0">
        🔷 {{ metricStats.dimensions }} dimension{{ metricStats.dimensions !== 1 ? 's' : '' }}
      </span>
      <span v-if="metricStats.filters > 0">
        🔍 {{ metricStats.filters }} filter{{ metricStats.filters !== 1 ? 's' : '' }}
      </span>
    </div>
  </div>
</template>

