<template>
  <div class="space-y-6 min-w-0">
    <!-- Query & Execution Actions -->
    <MetricDisplayQueryExecutionCard
      :previewing="validating"
      :executing="executing"
      @preview="$emit('validate')"
      @execute="$emit('execute')"
    />

     <!-- Advanced Execution Options -->
     <MetricDisplayAdvancedExecutionContainer
      :context-id="contextId"
      :cache-enabled="cacheEnabled"
      :cache-ttl="cacheTtl"
      :has-parameters="hasParameters"
      :execution-params="executionParams"
      :parameters="parameters"
      :available-cortex-parameters="availableCortexParameters"
      :executing="executing"
      :use-limit="useLimit"
      :limit-value="limitValue"
      :offset-value="offsetValue"
      :use-grouped="useGrouped"
      :grouped-value="groupedValue"
      :metric-grouped="metricGrouped"
      :modifiers-enabled="modifiersEnabled"
      :modifiers="modifiers"
      :table-schema="tableSchema"
      :available-tables="availableTables"
      :available-columns="availableColumns"
      :metric="metric"
      :schema-loading="schemaLoading"
      :schema-error="schemaError"
      @update:context-id="$emit('update:contextId', $event)"
      @update:cache-enabled="$emit('update:cacheEnabled', $event)"
      @update:cache-ttl="$emit('update:cacheTtl', $event)"
      @update:execution-params="$emit('update:executionParams', $event)"
      @update:use-limit="$emit('update:useLimit', $event)"
      @update:limit-value="$emit('update:limitValue', $event)"
      @update:offset-value="$emit('update:offsetValue', $event)"
      @update:use-grouped="$emit('update:useGrouped', $event)"
      @update:grouped-value="$emit('update:groupedValue', $event)"
      @update:modifiers-enabled="$emit('update:modifiersEnabled', $event)"
      @update:modifiers="$emit('update:modifiers', $event)"
      @reload-schema="$emit('reload-schema')"
    />

    <!-- Unified Results Viewer -->
    <ExecutionResultViewer
      v-if="executionResults || validationResult"
      :execution-results="executionResults || validationResult"
      :compiled-query="compiledQuery"
      :original-query="originalQuery"
      :is-preview="!executionResults && !!validationResult"
      @copy-query="$emit('copy-query')"
    />
  </div>
</template>

<script setup lang="ts">
import MetricDisplayQueryExecutionCard from './QueryExecutionCard.vue'
import MetricDisplayAdvancedExecutionContainer from './AdvancedExecutionContainer.vue'
import ExecutionResultViewer from '~/components/ExecutionResultViewer.vue'
import type { MetricModifiers } from '~/types/metric-modifiers'

interface Props {
  validating: boolean
  validationResult: any
  compiledQuery: string
  originalQuery: string
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
  executionResults: any
}

defineProps<Props>()

defineEmits<{
  'validate': []
  'copy-query': []
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
  'execute': []
}>()
</script>
