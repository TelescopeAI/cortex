<script setup lang="ts">
import { computed } from 'vue'
import { Plus, X } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Card } from '~/components/ui/card'
import type { ColumnField, ComparisonOperator, WhenClause, LogicalOperator } from '~/types/conditionals'
import ConditionRow from './ConditionRow.vue'

interface MainCondition {
  field: ColumnField
  operator: ComparisonOperator
  compare_values?: any
}

interface Props {
  mainCondition: MainCondition
  combineWith?: LogicalOperator
  additionalConditions?: WhenClause[]
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:main-condition': [value: MainCondition]
  'update:combine-with': [value: LogicalOperator]
  'update:additional-conditions': [value: WhenClause[]]
}>()

const updateMainCondition = (condition: MainCondition) => {
  emit('update:main-condition', condition)
}

const updateCombineWith = (operator: LogicalOperator) => {
  emit('update:combine-with', operator)
}

const updateAdditionalConditions = (conditions: WhenClause[]) => {
  emit('update:additional-conditions', conditions)
}

const addNestedCondition = (operator: LogicalOperator) => {
  const newCondition: WhenClause = {
    field: {
      column: '',
      transforms: []
    },
    operator: '=',
    compare_values: null,
    then_return: null
  }
  
  const conditions = [...(props.additionalConditions || []), newCondition]
  updateAdditionalConditions(conditions)
  
  // Set the combine_with operator
  if (!props.combineWith) {
    updateCombineWith(operator)
  }
}

const removeNestedCondition = (index: number) => {
  const conditions = [...(props.additionalConditions || [])]
  conditions.splice(index, 1)
  updateAdditionalConditions(conditions)
}

const updateNestedCondition = (index: number, condition: WhenClause) => {
  const conditions = [...(props.additionalConditions || [])]
  conditions[index] = condition
  updateAdditionalConditions(conditions)
}
</script>

<template>
  <div class="space-y-2">
    <!-- Main Condition (Primary) -->
    <Card class="p-3 bg-card">
      <ConditionRow
        :condition="mainCondition"
        :available-tables="availableTables"
        :available-columns="availableColumns"
        :is-primary="true"
        @update:condition="updateMainCondition"
      />
      
      <!-- Add AND/OR Buttons -->
      <div class="flex gap-2 mt-3 pt-3 border-t">
        <Button variant="outline" size="sm" @click="addNestedCondition('AND')">
          <Plus class="h-3 w-3 mr-1" />
          Add AND
        </Button>
        <Button variant="outline" size="sm" @click="addNestedCondition('OR')">
          <Plus class="h-3 w-3 mr-1" />
          Add OR
        </Button>
      </div>
    </Card>

    <!-- Nested Conditions (with visual connection) -->
    <div v-if="additionalConditions && additionalConditions.length > 0" class="ml-6 space-y-2">
      <div 
        v-for="(nestedCondition, index) in additionalConditions"
        :key="index"
        class="relative"
      >
        <!-- Connecting Line -->
        <div class="absolute left-[-24px] top-0 bottom-0 w-px bg-border"></div>
        <div class="absolute left-[-24px] top-[20px] w-6 h-px bg-border"></div>
        
        <!-- Logical Operator Badge -->
        <Badge 
          :variant="combineWith === 'AND' ? 'default' : 'secondary'"
          class="absolute left-[-20px] top-2 text-[10px] px-1"
        >
          {{ combineWith }}
        </Badge>

        <!-- Nested Condition Row -->
        <Card class="p-3 bg-muted/30">
          <div class="flex items-start gap-2">
            <ConditionRow
              :condition="nestedCondition"
              :available-tables="availableTables"
              :available-columns="availableColumns"
              :is-primary="false"
              @update:condition="updateNestedCondition(index, $event)"
            />
            
            <Button
              variant="ghost"
              size="sm"
              class="h-8 w-8 p-0"
              @click="removeNestedCondition(index)"
            >
              <X class="h-3 w-3" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

