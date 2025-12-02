<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import type { ColumnField, ComparisonOperator } from '~/types/conditionals'
import ColumnFieldBuilder from './ColumnFieldBuilder.vue'
import ValueTypeSelector from './ValueTypeSelector.vue'

interface Condition {
  field: ColumnField
  operator: ComparisonOperator
  compare_values?: any
}

interface Props {
  condition: Condition
  isPrimary: boolean
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:condition': [value: Condition]
}>()

const updateField = (field: ColumnField) => {
  emit('update:condition', { ...props.condition, field })
}

const updateOperator = (value: any) => {
  const operator = String(value) as ComparisonOperator
  emit('update:condition', { ...props.condition, operator })
}

const updateCompareValues = (compare_values: any) => {
  emit('update:condition', { ...props.condition, compare_values })
}

const getAllColumns = (): string[] => {
  return Object.values(props.availableColumns).flat()
}

const updateColumn = (value: any) => {
  const column = String(value)
  const field = { ...props.condition.field, column }
  emit('update:condition', { ...props.condition, field })
}
</script>

<template>
  <div class="flex items-center gap-2 flex-wrap">
    <!-- Column Field (with transforms) -->
    <div class="flex-1 min-w-[200px]">
      <ColumnFieldBuilder
        v-if="isPrimary"
        :model-value="condition.field"
        @update:model-value="updateField"
        :available-tables="availableTables"
        :available-columns="availableColumns"
      />
      <!-- Simplified display for nested -->
      <Select 
        v-else
        :model-value="condition.field.column"
        @update:model-value="updateColumn"
      >
        <SelectTrigger class="h-8 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem 
            v-for="col in getAllColumns()"
            :key="col"
            :value="col"
          >
            {{ col }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Operator -->
    <Select 
      :model-value="condition.operator"
      @update:model-value="updateOperator"
    >
      <SelectTrigger class="w-32 h-8">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="=">equals</SelectItem>
        <SelectItem value="!=">not equals</SelectItem>
        <SelectItem value=">">greater than</SelectItem>
        <SelectItem value="<">less than</SelectItem>
        <SelectItem value=">=">greater or equal</SelectItem>
        <SelectItem value="<=">less or equal</SelectItem>
        <SelectItem value="IN">in list</SelectItem>
        <SelectItem value="NOT IN">not in list</SelectItem>
        <SelectItem value="LIKE">matches pattern</SelectItem>
        <SelectItem value="BETWEEN">between</SelectItem>
        <SelectItem value="IS NULL">is null</SelectItem>
        <SelectItem value="IS NOT NULL">is not null</SelectItem>
      </SelectContent>
    </Select>

    <!-- Compare Value (Static or Column) -->
    <ValueTypeSelector
      :model-value="condition.compare_values"
      @update:model-value="updateCompareValues"
      :operator="condition.operator"
      :available-tables="availableTables"
      :available-columns="availableColumns"
      :context="'comparison'"
      placeholder="Value to compare"
    />
  </div>
</template>

