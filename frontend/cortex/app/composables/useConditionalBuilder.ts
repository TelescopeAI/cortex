import { ref } from 'vue'
import type { Condition, WhenClause } from '~/types/conditionals'

export function useConditionalBuilder(initialCondition?: Condition) {
  const condition = ref<Condition>(initialCondition || {
    when_clauses: [],
    else_return: 0
  })

  const addWhenClause = () => {
    condition.value.when_clauses.push({
      field: {
        column: '',
        transforms: []
      },
      operator: '=',
      compare_values: null,
      then_return: null
    })
  }

  const removeWhenClause = (index: number) => {
    condition.value.when_clauses.splice(index, 1)
  }

  return {
    condition,
    addWhenClause,
    removeWhenClause
  }
}

