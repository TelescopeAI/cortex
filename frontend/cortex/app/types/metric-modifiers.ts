import type {
  SemanticMeasure,
  SemanticDimension,
  SemanticFilter,
  SemanticJoin,
} from '~/types/output-formats'
import type { SemanticOrderSequence } from '~/types/order'

export interface MetricModifier {
  measures?: SemanticMeasure[]
  dimensions?: SemanticDimension[]
  joins?: SemanticJoin[]
  filters?: SemanticFilter[]
  order?: SemanticOrderSequence[]
  limit?: number | null
}

export type MetricModifiers = MetricModifier[]

export function createMetricModifier(): MetricModifier {
  return {
    measures: [],
    dimensions: [],
    joins: [],
    filters: [],
    order: [],
    limit: null,
  }
}

