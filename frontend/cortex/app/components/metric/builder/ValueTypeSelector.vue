<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, ArrowRight } from 'lucide-vue-next'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import type { ColumnField, ComparisonOperator } from '~/types/conditionals'
import ComparisonValueInput from './ComparisonValueInput.vue'
import ColumnFieldBuilder from './ColumnFieldBuilder.vue'
import { DatePickerInput, DateRangePickerInput } from '~/components/date-picker'

interface Props {
  modelValue: any | ColumnField
  operator?: ComparisonOperator
  availableTables: string[]
  availableColumns: Record<string, string[]>
  placeholder?: string
  label?: string
  context?: 'comparison' | 'return'
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any | ColumnField]
}>()

const valueType = computed(() => {
  return isColumnField(props.modelValue) ? 'column' : 'static'
})

const isColumnField = (value: any): value is ColumnField => {
  return value && typeof value === 'object' && 'column' in value
}

const updateValueType = (type: 'static' | 'column') => {
  if (type === 'static') {
    // Convert from ColumnField to static value
    if (isColumnField(props.modelValue)) {
      emit('update:modelValue', '')
    }
  } else {
    // Convert from static to ColumnField
    if (!isColumnField(props.modelValue)) {
      emit('update:modelValue', {
        column: '',
        transforms: []
      })
    }
  }
}

const updateStaticValue = (value: any) => {
  emit('update:modelValue', value)
}

const updateColumnValue = (value: ColumnField) => {
  emit('update:modelValue', value)
}

// Date operator detection
const isDateRangeOperator = computed(() => {
  return props.operator === 'BETWEEN'
})

const isDateOperator = computed(() => {
  return ['=', '!=', '>', '<', '>=', '<='].includes(props.operator || '') && 
         props.context === 'comparison'
})

const showColumnBuilder = computed(() => {
  return valueType.value === 'column'
})

const switchToColumnReference = () => {
  updateValueType('column')
}

const switchToStatic = () => {
  updateValueType('static')
}
</script>

<template>
  <div class="space-y-2">
    <Label v-if="label">{{ label }}</Label>
    
    <!-- Static Value Mode (Default) -->
    <div v-if="!showColumnBuilder" class="space-y-2">
      <!-- Date Range Picker for BETWEEN -->
      <DateRangePickerInput
        v-if="isDateRangeOperator"
        :model-value="modelValue"
        @update:model-value="updateStaticValue"
        :placeholder="placeholder"
      />
      
      <!-- Single Date Picker for date comparison -->
      <DatePickerInput
        v-else-if="isDateOperator"
        :model-value="modelValue"
        @update:model-value="updateStaticValue"
        :placeholder="placeholder"
      />
      
      <!-- Standard Comparison Input (numbers, strings, lists) -->
      <ComparisonValueInput
        v-else
        :model-value="modelValue"
        @update:model-value="updateStaticValue"
        :operator="operator || '='"
      />
      
      <!-- Link to switch to column reference -->
      <button
        type="button"
        class="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
        @click="switchToColumnReference"
      >
        <ArrowRight class="h-3 w-3" />
        {{ context === 'comparison' ? 'Compare to another column' : 'Return a column value' }}
      </button>
    </div>

    <!-- Column Reference Mode -->
    <div v-else class="space-y-2">
      <div class="flex items-center justify-between">
        <Label class="text-xs font-medium text-muted-foreground">Column Reference</Label>
        <button
          type="button"
          class="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
          @click="switchToStatic"
        >
          <ArrowLeft class="h-3 w-3" />
          Back to static value
        </button>
      </div>
      
      <ColumnFieldBuilder
        :model-value="modelValue as ColumnField"
        @update:model-value="updateColumnValue"
        :available-tables="availableTables"
        :available-columns="availableColumns"
      />
    </div>
  </div>
</template>

