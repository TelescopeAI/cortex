// TypeScript interfaces for semantic ordering

export type SemanticOrderType = 'asc' | 'desc'

export type SemanticNullsPosition = 'first' | 'last'

export type SemanticOrderReferenceType = 'measure' | 'dimension' | 'column' | 'position'

export interface SemanticOrderSequence {
  name: string
  description?: string
  
  // Semantic ordering (recommended approach)
  semantic_type?: SemanticOrderReferenceType
  semantic_name?: string // Name of the measure/dimension to order by
  
  // Position-based ordering
  position?: number // 1-based position in SELECT clause
  
  // Legacy direct column ordering (backward compatibility)
  query?: string // Column name or expression to order by
  table?: string
  
  // Common properties
  order_type: SemanticOrderType
  nulls?: SemanticNullsPosition
}

// Form interfaces for UI components
export interface OrderSequenceFormData {
  name: string
  description?: string
  query: string
  table?: string
  order_type: SemanticOrderType
  nulls?: SemanticNullsPosition
}

export interface OrderSequenceOption {
  label: string
  value: SemanticOrderType | SemanticNullsPosition
}

// Constants for UI dropdowns
export const ORDER_TYPE_OPTIONS: OrderSequenceOption[] = [
  { label: 'Ascending', value: 'asc' },
  { label: 'Descending', value: 'desc' }
]

export const NULLS_POSITION_OPTIONS: OrderSequenceOption[] = [
  { label: 'Nulls First', value: 'first' },
  { label: 'Nulls Last', value: 'last' }
]

export const SEMANTIC_ORDER_REFERENCE_TYPE_OPTIONS: Array<{ label: string; value: SemanticOrderReferenceType }> = [
  { label: 'Measure', value: 'measure' },
  { label: 'Dimension', value: 'dimension' },
  { label: 'Column', value: 'column' },
  { label: 'Position', value: 'position' }
]

// Helper functions for semantic ordering
export function createSemanticOrderSequence(
  type: SemanticOrderReferenceType,
  name: string,
  reference: string | number,
  orderType: SemanticOrderType = 'asc'
): SemanticOrderSequence {
  const base: SemanticOrderSequence = {
    name: `order_${name}`,
    semantic_type: type,
    order_type: orderType
  }

  switch (type) {
    case 'measure':
    case 'dimension':
      return { ...base, semantic_name: String(reference) }
    case 'position':
      return { ...base, position: Number(reference) }
    case 'column':
      return { ...base, query: String(reference) }
    default:
      return base
  }
}

export function getOrderSequenceDisplayName(sequence: SemanticOrderSequence): string {
  if (sequence.semantic_name) {
    return `${sequence.semantic_name} (${sequence.semantic_type})`
  }
  if (sequence.position) {
    return `Position ${sequence.position}`
  }
  if (sequence.query) {
    return sequence.query
  }
  return sequence.name
}
