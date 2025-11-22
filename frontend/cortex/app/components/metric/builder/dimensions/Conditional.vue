<script setup lang="ts">
import ConditionalBuilder from '../ConditionalBuilder.vue'
import type { Condition } from '~/types/conditionals'

interface Dimension {
  name: string
  description?: string
  query: string
  table?: string
  formatting?: any[]
  conditional?: boolean
  conditions?: Condition | null
}

interface Props {
  dimension: Dimension
  availableTables: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:dimension': [value: Dimension]
}>()

const updateDimension = (updates: Partial<Dimension>) => {
  emit('update:dimension', { ...props.dimension, ...updates })
}

const getAvailableColumnsMap = (): Record<string, string[]> => {
  const columnsMap: Record<string, string[]> = {}
  
  props.availableTables.forEach((table: any) => {
    columnsMap[table.name] = table.columns.map((col: any) => col.name)
  })
  
  return columnsMap
}

const updateConditions = (conditions: Condition | null) => {
  updateDimension({ conditions })
}
</script>

<template>
  <div class="space-y-3">
    <!-- Conditional Builder -->
    <ConditionalBuilder
      :model-value="dimension.conditions || null"
      @update:model-value="updateConditions"
      :available-tables="availableTables.map((t: any) => t.name)"
      :available-columns="getAvailableColumnsMap()"
    />
  </div>
</template>

