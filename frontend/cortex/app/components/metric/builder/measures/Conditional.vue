<script setup lang="ts">
import { computed } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import ConditionalBuilder from '../ConditionalBuilder.vue'
import type { Condition } from '~/types/conditionals'

interface Measure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
  conditional?: boolean
  conditions?: Condition | null
}

interface Props {
  measure: Measure
  availableTables: any[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:measure': [value: Measure]
}>()

const updateMeasure = (updates: Partial<Measure>) => {
  emit('update:measure', { ...props.measure, ...updates })
}

const getAvailableColumnsMap = (): Record<string, string[]> => {
  const columnsMap: Record<string, string[]> = {}
  
  props.availableTables.forEach((table: any) => {
    columnsMap[table.name] = table.columns.map((col: any) => col.name)
  })
  
  return columnsMap
}

const updateConditions = (conditions: Condition | null) => {
  updateMeasure({ conditions })
}
</script>

<template>
  <div class="space-y-3">
    <!-- Aggregation Type -->
    <div class="flex items-center gap-2">
      <span class="text-sm text-muted-foreground">Aggregate using</span>
      <Select :model-value="measure.type" @update:model-value="(val) => updateMeasure({ type: val })">
        <SelectTrigger class="w-auto min-w-[130px] h-9">
          <SelectValue placeholder="Select type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="count">COUNT</SelectItem>
          <SelectItem value="sum">SUM</SelectItem>
          <SelectItem value="avg">AVG</SelectItem>
          <SelectItem value="min">MIN</SelectItem>
          <SelectItem value="max">MAX</SelectItem>
          <SelectItem value="count_distinct">COUNT DISTINCT</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Conditional Builder -->
    <div class="pt-4 border-t">
      <ConditionalBuilder
        :model-value="measure.conditions || null"
        @update:model-value="updateConditions"
        :available-tables="availableTables.map((t: any) => t.name)"
        :available-columns="getAvailableColumnsMap()"
      />
    </div>
  </div>
</template>

