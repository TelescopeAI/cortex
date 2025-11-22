<script setup lang="ts">
import { provide, watch } from 'vue'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Input } from '~/components/ui/input'
import { DatePickerInput, DateRangePickerInput } from '~/components/date-picker'
import { useConditionBuilder } from '~/composables/useConditionBuilder'
import { useSchemaMetadata } from '~/composables/useSchemaMetadata'
import type { WhenClause } from '~/types/conditionals'

interface Props {
  modelValue: WhenClause
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: WhenClause]
}>()

// Initialize condition builder
const {
  condition,
  columnType,
  shouldShowDatePicker,
  shouldShowDateRangePicker,
  shouldShowNumberInput,
  updateType,
  updateField,
  updateOperator,
  updateCompareValues,
  wrapInFunction,
  removeFunction,
  toWhenClause
} = useConditionBuilder(props.modelValue)

// Initialize schema metadata
const { getColumnType, getOperatorsForType } = useSchemaMetadata(
  props.availableTables, 
  props.availableColumns
)

// Provide context to all child components
provide('conditionContext', {
  // State
  condition,
  columnType,
  
  // Computed
  shouldShowDatePicker,
  shouldShowDateRangePicker,
  shouldShowNumberInput,
  
  // Schema helpers
  getColumnType,
  getOperatorsForType,
  
  // Actions
  updateType,
  updateField,
  updateOperator,
  updateCompareValues,
  wrapInFunction,
  removeFunction,
  
  // Data
  availableTables: props.availableTables,
  availableColumns: props.availableColumns
})

// Watch for changes and emit updates
watch(condition, (newCondition) => {
  emit('update:modelValue', toWhenClause())
}, { deep: true })
</script>

<template>
  <div class="space-y-3">
    <!-- Type Selector Slot -->
    <slot 
      name="type-selector"
      :condition="condition"
      :update-type="updateType"
    >
      <div class="flex items-center gap-2">
        <Label class="text-xs font-semibold">Type</Label>
        <Select :model-value="condition.type" @update:model-value="updateType">
          <SelectTrigger class="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="column">Column Condition</SelectItem>
            <SelectItem value="function">Function</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </slot>

    <!-- Function Selector Slot (conditional) -->
    <slot 
      v-if="condition.type === 'function'"
      name="function-selector"
      :condition="condition"
      :wrap-function="wrapInFunction"
      :remove-function="removeFunction"
    >
      <div class="space-y-2">
        <Label class="text-xs font-semibold">Function</Label>
        <Select :model-value="condition.wrap_function" @update:model-value="(func) => wrapInFunction(func)">
          <SelectTrigger>
            <SelectValue placeholder="Select function" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>String Functions</SelectLabel>
              <SelectItem value="COALESCE">COALESCE (handle nulls)</SelectItem>
              <SelectItem value="LOWER">LOWER (to lowercase)</SelectItem>
              <SelectItem value="UPPER">UPPER (to uppercase)</SelectItem>
              <SelectItem value="CONCAT">CONCAT (join strings)</SelectItem>
              <SelectItem value="TRIM">TRIM (remove spaces)</SelectItem>
              <SelectItem value="SUBSTRING">SUBSTRING (extract text)</SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Math Functions</SelectLabel>
              <SelectItem value="ROUND">ROUND (round number)</SelectItem>
              <SelectItem value="ABS">ABS (absolute value)</SelectItem>
              <SelectItem value="CEIL">CEIL (round up)</SelectItem>
              <SelectItem value="FLOOR">FLOOR (round down)</SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Date Functions</SelectLabel>
              <SelectItem value="EXTRACT">EXTRACT (get date part)</SelectItem>
              <SelectItem value="DATE_TRUNC">DATE_TRUNC (truncate date)</SelectItem>
              <SelectItem value="DATE_PART">DATE_PART (get date part)</SelectItem>
            </SelectGroup>
            <SelectGroup>
              <SelectLabel>Type Conversion</SelectLabel>
              <SelectItem value="CAST">CAST (convert type)</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>
    </slot>

    <!-- Column Selection Slot -->
    <slot 
      name="column-selector"
      :condition="condition"
      :update-field="updateField"
      :available-tables="availableTables"
      :available-columns="availableColumns"
    >
      <div class="space-y-2">
        <Label class="text-xs font-semibold">Column</Label>
        <div class="flex gap-2">
          <Select :model-value="condition.field.table" @update:model-value="(table) => updateField({ ...condition.field, table })">
            <SelectTrigger>
              <SelectValue placeholder="Table" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="table in availableTables" :key="table" :value="table">
                {{ table }}
              </SelectItem>
            </SelectContent>
          </Select>
          <Select :model-value="condition.field.column" @update:model-value="(column) => updateField({ ...condition.field, column })">
            <SelectTrigger>
              <SelectValue placeholder="Column" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="col in availableColumns[condition.field.table || '']" :key="col" :value="col">
                {{ col }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </slot>

    <!-- Operator Selection Slot -->
    <slot 
      name="operator-selector"
      :condition="condition"
      :update-operator="updateOperator"
      :operators="getOperatorsForType(columnType)"
    >
      <div class="space-y-2">
        <Label class="text-xs font-semibold">Operator</Label>
        <Select :model-value="condition.operator" @update:model-value="updateOperator">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="op in getOperatorsForType(columnType)" :key="op" :value="op">
              {{ op }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </slot>

    <!-- Value Input Slot (smart detection) -->
    <slot 
      name="value-input"
      :condition="condition"
      :update-compare-values="updateCompareValues"
      :should-show-date-picker="shouldShowDatePicker"
      :should-show-date-range-picker="shouldShowDateRangePicker"
      :should-show-number-input="shouldShowNumberInput"
      :column-type="columnType"
    >
      <div class="space-y-2">
        <Label class="text-xs font-semibold">Value</Label>
        
        <!-- Date Range Picker for BETWEEN -->
        <DateRangePickerInput
          v-if="shouldShowDateRangePicker"
          :model-value="condition.compare_values"
          @update:model-value="updateCompareValues"
          placeholder="Select date range"
        />
        
        <!-- Single Date Picker for date comparison -->
        <DatePickerInput
          v-else-if="shouldShowDatePicker"
          :model-value="condition.compare_values"
          @update:model-value="updateCompareValues"
          placeholder="Select date"
        />
        
        <!-- Number Input for numeric columns -->
        <Input
          v-else-if="shouldShowNumberInput"
          :model-value="condition.compare_values"
          @update:model-value="updateCompareValues"
          type="number"
          placeholder="Enter value"
        />
        
        <!-- Text Input for other cases -->
        <Input
          v-else
          :model-value="condition.compare_values"
          @update:model-value="updateCompareValues"
          placeholder="Enter value"
        />
      </div>
    </slot>
  </div>
</template>
