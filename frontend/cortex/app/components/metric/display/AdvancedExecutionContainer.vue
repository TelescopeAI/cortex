<template>
  <Collapsible v-model:open="isOpen" class="border rounded-lg">
    <div class="flex items-center justify-between p-4">
      <div>
        <h3 class="font-semibold text-sm text-gray-900 dark:text-gray-100">Advanced</h3>
        <p class="text-xs text-muted-foreground mt-1">Configure context, cache, parameters, limits, grouping, and modifiers</p>
      </div>
      <CollapsibleTrigger as-child>
        <Button variant="ghost" size="sm" class="w-9 p-0">
          <ChevronDown :class="['h-4 w-4 transition-transform', isOpen && 'rotate-180']" />
          <span class="sr-only">Toggle advanced options</span>
        </Button>
      </CollapsibleTrigger>
    </div>

    <CollapsibleContent class="CollapsibleContent p-4 border-t">
      <MetricDisplayExecutionContextCard
        :model-value="contextId"
        @update:model-value="$emit('update:contextId', $event)"
      />

      <MetricDisplayCachePreferenceCard
        :enabled="cacheEnabled"
        :ttl="cacheTtl"
        @update:enabled="$emit('update:cacheEnabled', $event)"
        @update:ttl="$emit('update:cacheTtl', $event)"
      />

      <MetricDisplayParametersCard
        v-if="hasParameters"
        :model-value="executionParams"
        :parameters="parameters"
        :available-cortex-parameters="availableCortexParameters"
        :is-loading="executing"
        @update:model-value="$emit('update:executionParams', $event)"
      />

      <MetricDisplayQueryLimitsCard
        :use-limit="useLimit"
        :limit-value="limitValue"
        :offset-value="offsetValue"
        @update:use-limit="$emit('update:useLimit', $event)"
        @update:limit-value="$emit('update:limitValue', $event)"
        @update:offset-value="$emit('update:offsetValue', $event)"
      />

      <MetricDisplayQueryGroupingCard
        :use-grouped="useGrouped"
        :grouped-value="groupedValue"
        :metric-grouped="metricGrouped"
        @update:use-grouped="$emit('update:useGrouped', $event)"
        @update:grouped-value="$emit('update:groupedValue', $event)"
      />

      <MetricDisplayMetricModifiersCard
        :modifiers-enabled="modifiersEnabled"
        :modifiers="modifiers"
        :table-schema="tableSchema"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        :metric="metric"
        :schema-loading="schemaLoading"
        :schema-error="schemaError"
        @update:modifiers-enabled="$emit('update:modifiersEnabled', $event)"
        @update:modifiers="$emit('update:modifiers', $event)"
        @reload-schema="$emit('reload-schema')"
      />
    </CollapsibleContent>
  </Collapsible>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '~/components/ui/collapsible'
import { Button } from '~/components/ui/button'
import { ChevronDown } from 'lucide-vue-next'
import MetricDisplayExecutionContextCard from './ExecutionContextCard.vue'
import MetricDisplayCachePreferenceCard from './CachePreferenceCard.vue'
import MetricDisplayParametersCard from './ParametersCard.vue'
import MetricDisplayQueryLimitsCard from './QueryLimitsCard.vue'
import MetricDisplayQueryGroupingCard from './QueryGroupingCard.vue'
import MetricDisplayMetricModifiersCard from './MetricModifiersCard.vue'
import type { MetricModifiers } from '~/types/metric-modifiers'

interface Props {
  contextId: string
  cacheEnabled: boolean
  cacheTtl?: number
  hasParameters: boolean
  executionParams: Record<string, any>
  parameters: any[]
  availableCortexParameters: string[]
  executing: boolean
  useLimit: boolean
  limitValue: number
  offsetValue: number
  useGrouped: boolean
  groupedValue: boolean
  metricGrouped: boolean
  modifiersEnabled: boolean
  modifiers: MetricModifiers
  tableSchema: any
  availableTables: any[]
  availableColumns: any[]
  metric: any
  schemaLoading: boolean
  schemaError: string | null
}

defineProps<Props>()

const emit = defineEmits<{
  'update:contextId': [value: string]
  'update:cacheEnabled': [value: boolean]
  'update:cacheTtl': [value: number]
  'update:executionParams': [value: Record<string, any>]
  'update:useLimit': [value: boolean]
  'update:limitValue': [value: number]
  'update:offsetValue': [value: number]
  'update:useGrouped': [value: boolean]
  'update:groupedValue': [value: boolean]
  'update:modifiersEnabled': [value: boolean]
  'update:modifiers': [value: MetricModifiers]
  'reload-schema': []
}>()

const isOpen = ref(false)
</script>

<style scoped>
/* styles.css */
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