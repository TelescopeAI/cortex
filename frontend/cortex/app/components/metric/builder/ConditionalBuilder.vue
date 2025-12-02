<script setup lang="ts">
import { computed } from 'vue'
import { Plus } from 'lucide-vue-next'
import type { Condition, WhenClause } from '~/types/conditionals'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import WhenClauseBuilder from './WhenClauseBuilder.vue'
import ValueTypeSelector from './ValueTypeSelector.vue'

interface Props {
  modelValue: Condition | null
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: Condition | null]
}>()

const condition = computed({
  get: () => props.modelValue || { when_clauses: [], else_return: 0 },
  set: (val) => emit('update:modelValue', val)
})

const addWhenClause = () => {
  const newClause: WhenClause = {
    field: {
      column: '',
      transforms: []
    },
    operator: '=',
    compare_values: null,
    then_return: null
  }
  
  emit('update:modelValue', {
    ...condition.value,
    when_clauses: [...condition.value.when_clauses, newClause]
  })
}

const removeWhenClause = (index: number) => {
  const clauses = [...condition.value.when_clauses]
  clauses.splice(index, 1)
  emit('update:modelValue', {
    ...condition.value,
    when_clauses: clauses
  })
}

const updateWhenClause = (index: number, clause: WhenClause) => {
  const clauses = [...condition.value.when_clauses]
  clauses[index] = clause
  emit('update:modelValue', {
    ...condition.value,
    when_clauses: clauses
  })
}

const updateElseReturn = (value: any) => {
  emit('update:modelValue', {
    ...condition.value,
    else_return: value
  })
}
</script>

<template>
  <div class="conditional-builder">
    <!-- Header -->
    <div class="mb-4">
      <Label class="text-sm font-medium">Build Conditional Logic</Label>
      <p class="text-xs text-muted-foreground mt-1">
        Define multiple conditions that return different values
      </p>
    </div>

    <!-- WHEN Clauses -->
    <div class="space-y-4">
      <WhenClauseBuilder
        v-for="(whenClause, index) in condition.when_clauses"
        :key="index"
        :model-value="whenClause"
        @update:model-value="updateWhenClause(index, $event)"
        :index="index"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        @remove="removeWhenClause(index)"
      />
    </div>

    <!-- Add WHEN Button -->
    <Button variant="outline" class="mt-4 w-full" @click="addWhenClause">
      <Plus class="h-4 w-4 mr-2" />
      Add WHEN Clause
    </Button>

    <!-- ELSE Clause -->
    <div class="mt-6 p-4 border rounded-lg bg-muted/30">
      <ValueTypeSelector
        :model-value="condition.else_return"
        @update:model-value="updateElseReturn"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        :context="'return'"
        label="Otherwise Return"
        placeholder="Default value when no conditions match"
      />
    </div>
  </div>
</template>

