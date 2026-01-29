<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '~/components/ui/card'
import { Checkbox } from '~/components/ui/checkbox'
import MetricStatsBadges from './MetricStatsBadges.vue'
import MetricPreviewChart from './MetricPreviewChart.vue'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  metric: SemanticMetric
  selected?: boolean
  loading?: boolean
}

interface Emits {
  (e: 'toggle-select', checked: boolean): void
}

const props = defineProps<Props>()
defineEmits<Emits>()

const metricDescription = computed(() => {
  return props.metric.description || 'No description'
})

const metricTitle = computed(() => {
  return props.metric.title || props.metric.name
})
</script>

<template>
  <Card 
    class="relative hover:shadow-xl hover:dark:shadow-md hover:shadow-indigo-100 dark:hover:shadow-indigo-500 transition-shadow"
    :class="{ 'ring-2 ring-primary': selected }"
  >
    <CardContent class="p-4">
      <!-- 2-column grid: Left = info, Right = chart -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left Column: Metric Info -->
        <div class="flex flex-col justify-center space-y-6">
          <!-- Header with checkbox and title -->
          <div class="flex items-start space-x-4">
            <Checkbox 
              :id="`metric-${metric.name}`"
              :checked="selected"
              @click.stop="$emit('toggle-select', !selected)"
              class="mt-2 h-5 w-5 cursor-pointer"
            />
            
            <div class="flex-1 space-y-2">
              <h3 class="text-2xl font-semibold text-indigo-900 dark:text-indigo-100 leading-tight">{{ metricTitle }}</h3>
              <p class="text-sm text-muted-foreground line-clamp-3">
                {{ metricDescription }}
              </p>
            </div>
          </div>

          <!-- Metric Details -->
          <div class="flex flex-wrap gap-x-8 gap-y-4 pl-9">
            <!-- Measures -->
            <div v-if="metric.measures && metric.measures.length > 0" class="space-y-2">
              <p class="text-sm font-semibold text-foreground">Numbers:</p>
              <div class="space-y-1.5">
                <div 
                  v-for="(measure, idx) in metric.measures" 
                  :key="idx"
                  class="text-sm text-muted-foreground"
                >
                  • {{ measure.type?.toUpperCase() }}({{ measure.query || measure.name }})
                </div>
              </div>
            </div>

            <!-- Dimensions -->
            <div v-if="metric.dimensions && metric.dimensions.length > 0" class="space-y-2">
              <p class="text-sm font-semibold text-foreground">Categories:</p>
              <div class="space-y-1.5">
                <div 
                  v-for="(dim, idx) in metric.dimensions" 
                  :key="idx"
                  class="text-sm text-muted-foreground"
                >
                  • {{ dim.name }}
                </div>
              </div>
            </div>

            <!-- Filters -->
            <div v-if="metric.filters && metric.filters.length > 0" class="space-y-2">
              <p class="text-sm font-semibold text-foreground">Filters:</p>
              <div class="space-y-1.5">
                <div 
                  v-for="(filter, idx) in metric.filters" 
                  :key="idx"
                  class="text-sm text-muted-foreground"
                >
                  • {{ filter.name || filter.query }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Chart Preview (always visible) -->
        <div class="min-h-[200px]">
          <MetricPreviewChart :metric="metric" :expanded="true" />
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
