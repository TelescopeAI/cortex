<script setup lang="ts">
import { inject } from 'vue'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { DatePickerInput, DateRangePickerInput } from '~/components/date-picker'
import ValueTypeSelector from '../ValueTypeSelector.vue'

interface Props {
  modelValue: any
  placeholder?: string
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Enter value'
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

// Get context from parent ConditionBuilder
const context = inject('conditionContext', {
  shouldShowDatePicker: false,
  shouldShowDateRangePicker: false,
  shouldShowNumberInput: false,
  columnType: 'string'
})

const updateValue = (value: any) => {
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="space-y-2">
    <Label v-if="label" class="text-xs font-semibold">{{ label }}</Label>
    
    <!-- Date Range Picker for BETWEEN operator -->
    <DateRangePickerInput
      v-if="context.shouldShowDateRangePicker"
      :model-value="modelValue"
      @update:model-value="updateValue"
      :placeholder="placeholder"
    />
    
    <!-- Single Date Picker for date comparison -->
    <DatePickerInput
      v-else-if="context.shouldShowDatePicker"
      :model-value="modelValue"
      @update:model-value="updateValue"
      :placeholder="placeholder"
    />
    
    <!-- Number Input for numeric columns -->
    <Input
      v-else-if="context.shouldShowNumberInput"
      :model-value="modelValue"
      @update:model-value="updateValue"
      type="number"
      :placeholder="placeholder"
    />
    
    <!-- ValueTypeSelector for complex cases (static vs column reference) -->
    <ValueTypeSelector
      v-else
      :model-value="modelValue"
      @update:model-value="updateValue"
      :operator="context.condition?.operator"
      :available-tables="context.availableTables || []"
      :available-columns="context.availableColumns || {}"
      :context="'comparison'"
      :placeholder="placeholder"
    />
  </div>
</template>
