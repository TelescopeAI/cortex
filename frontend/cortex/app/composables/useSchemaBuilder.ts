import { ref, readonly } from 'vue'

export function useSchemaBuilder(initialSchema: any) {
  const schema = ref({
    name: '',
    alias: '',
    title: '',
    description: '',
    table_name: '',
    query: '',
    data_source_id: undefined as string | undefined,
    limit: undefined as number | undefined,
    grouped: true,
    ordered: true,
    measures: [] as any[],
    dimensions: [] as any[],
    joins: [] as any[],
    filters: [] as any[],
    order: [] as any[],
    parameters: {} as any,
    refresh: undefined as any,
    cache: undefined as any,
    ...initialSchema
  })

  const updateMeasures = (measures: any[]) => {
    console.log('[useSchemaBuilder] updateMeasures called with:', measures)
    // Always create a new array to ensure reactivity
    schema.value.measures = [...measures]
    console.log('[useSchemaBuilder] Schema measures after update:', schema.value.measures)
  }

  const updateDimensions = (dimensions: any[]) => {
    // Always create a new array to ensure reactivity
    schema.value.dimensions = [...dimensions]
  }

  const updateJoins = (joins: any[]) => {
    // Always create a new array to ensure reactivity
    schema.value.joins = [...joins]
  }

  const updateFilters = (filters: any[]) => {
    // Always create a new array to ensure reactivity
    schema.value.filters = [...filters]
  }

  const updateOrder = (order: any[]) => {
    // Always create a new array to ensure reactivity
    schema.value.order = [...order]
  }

  const updateField = (field: string, value: any) => {
    (schema.value as any)[field] = value
  }

  return {
    schema,
    updateMeasures,
    updateDimensions,
    updateJoins,
    updateFilters,
    updateOrder,
    updateField
  }
}

