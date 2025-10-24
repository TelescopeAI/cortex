<script setup lang="ts">
import { computed } from 'vue'
import { Trash2 } from 'lucide-vue-next'
import type { WhenClause, ComparisonOperator, LogicalOperator } from '~/types/conditionals'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card } from '~/components/ui/card'
import ConditionBuilder from './condition-builder/ConditionBuilder.vue'
import ValueTypeSelector from './ValueTypeSelector.vue'

interface Props {
  modelValue: WhenClause
  index: number
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: WhenClause]
  'remove': []
}>()

const whenClause = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const updateMainCondition = (condition: any) => {
  emit('update:modelValue', { 
    ...whenClause.value, 
    field: condition.field,
    operator: condition.operator,
    compare_values: condition.compare_values
  })
}

const updateCombineWith = (operator: LogicalOperator) => {
  emit('update:modelValue', { ...whenClause.value, combine_with: operator })
}

const updateAdditionalConditions = (conditions: WhenClause[]) => {
  emit('update:modelValue', { ...whenClause.value, additional_conditions: conditions })
}

const updateThenReturn = (value: any) => {
  emit('update:modelValue', { ...whenClause.value, then_return: value })
}

const updateWhenClause = (updatedClause: WhenClause) => {
  emit('update:modelValue', updatedClause)
}
</script>

<template>
  <Card class="p-4">
    <!-- Header with index and remove button -->
    <div class="flex items-center justify-between mb-4">
      <Badge variant="secondary">WHEN {{ index + 1 }}</Badge>
      <Button variant="ghost" size="sm" @click="emit('remove')">
        <Trash2 class="h-4 w-4" />
      </Button>
    </div>

    <!-- IF Section: New Condition Builder -->
    <div class="space-y-3">
      <div class="flex items-center justify-between">
        <Label class="text-sm font-medium">If</Label>
      </div>
      
      <ConditionBuilder
        :model-value="whenClause"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        @update:model-value="updateWhenClause"
      />
    </div>

    <!-- THEN Section: Return Value (Static or Column) -->
    <div class="mt-4 pt-4 border-t">
      <ValueTypeSelector
        :model-value="whenClause.then_return"
        @update:model-value="updateThenReturn"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        :context="'return'"
        label="Then Return"
        placeholder="Enter return value or select column"
      />
    </div>
  </Card>
</template>

