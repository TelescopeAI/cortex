import { ref, computed } from 'vue'
import type { WhenClause, ColumnField, ComparisonOperator, TransformFunction } from '~/types/conditionals'

export interface ConditionBuilderState {
  type: 'column' | 'function'
  field: ColumnField
  operator: ComparisonOperator
  compare_values: any
  wrap_function?: TransformFunction
  wrap_function_params?: Record<string, any>
}

export function useConditionBuilder(initialCondition?: Partial<WhenClause>) {
  const condition = ref<ConditionBuilderState>({
    type: 'column',
    field: { column: '', transforms: [] },
    operator: '=',
    compare_values: null,
    wrap_function: undefined,
    wrap_function_params: undefined,
    ...initialCondition
  })

  // Smart column type detection
  const columnType = computed(() => {
    const column = condition.value.field.column.toLowerCase()
    
    // Date/timestamp detection
    if (column.includes('date') || column.includes('time') || column.includes('created') || column.includes('updated')) {
      return 'date'
    }
    
    // Numeric detection
    if (column.includes('count') || column.includes('total') || column.includes('amount') || column.includes('price') || column.includes('percent')) {
      return 'number'
    }
    
    // Default to string
    return 'string'
  })

  // Smart input detection
  const shouldShowDatePicker = computed(() => {
    return columnType.value === 'date' && 
           !['BETWEEN', 'IN', 'NOT IN'].includes(condition.value.operator)
  })

  const shouldShowDateRangePicker = computed(() => {
    return columnType.value === 'date' && condition.value.operator === 'BETWEEN'
  })

  const shouldShowNumberInput = computed(() => {
    return columnType.value === 'number' && 
           !['IN', 'NOT IN', 'LIKE'].includes(condition.value.operator)
  })

  // Actions
  const updateType = (type: 'column' | 'function') => {
    condition.value.type = type
    if (type === 'column') {
      condition.value.wrap_function = undefined
      condition.value.wrap_function_params = undefined
    }
  }

  const updateField = (field: ColumnField) => {
    condition.value.field = field
  }

  const updateOperator = (operator: ComparisonOperator) => {
    condition.value.operator = operator
    
    // Auto-reset compare_values based on operator
    if (operator === 'BETWEEN') {
      condition.value.compare_values = [null, null]
    } else if (['IN', 'NOT IN'].includes(operator)) {
      condition.value.compare_values = []
    } else if (['IS NULL', 'IS NOT NULL'].includes(operator)) {
      condition.value.compare_values = null
    } else {
      condition.value.compare_values = null
    }
  }

  const updateCompareValues = (values: any) => {
    condition.value.compare_values = values
  }

  const wrapInFunction = (func: TransformFunction, params?: Record<string, any>) => {
    condition.value.wrap_function = func
    condition.value.wrap_function_params = params
  }

  const removeFunction = () => {
    condition.value.wrap_function = undefined
    condition.value.wrap_function_params = undefined
  }

  // Convert to WhenClause format
  const toWhenClause = (): WhenClause => {
    return {
      field: condition.value.field,
      operator: condition.value.operator,
      compare_values: condition.value.compare_values,
      then_return: null, // Will be set by parent
      wrap_function: condition.value.wrap_function,
      wrap_function_params: condition.value.wrap_function_params
    }
  }

  return {
    // State
    condition,
    columnType,
    
    // Computed
    shouldShowDatePicker,
    shouldShowDateRangePicker,
    shouldShowNumberInput,
    
    // Actions
    updateType,
    updateField,
    updateOperator,
    updateCompareValues,
    wrapInFunction,
    removeFunction,
    toWhenClause
  }
}
