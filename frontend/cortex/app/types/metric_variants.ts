/**
 * Type definitions for Metric Variants
 *
 * Naming Convention: All variant-related types use the "Metric" prefix to indicate
 * they belong to the metrics domain (e.g., SemanticMetricVariant, MetricRef, MetricOverrides).
 */

import type { SemanticMetric } from './metrics'

// ============================================================================
// Core Variant Types
// ============================================================================

export interface SemanticMetricVariant {
  // Identity
  id: string
  name: string
  alias?: string
  description?: string

  // Variant definition (the recipe)
  source: MetricRef
  overrides?: MetricOverrides
  include?: IncludedComponents
  derivations?: DerivedEntity[]
  combine?: MetricRef[]

  // Variant's own settings (NOT inherited from source)
  version: number
  public: boolean
  cache?: CachePreference
  refresh?: RefreshPolicy
  parameters?: Record<string, ParameterDefinition>
  meta?: Record<string, any>

  // Timestamps
  created_at: string
  updated_at: string
}

// ============================================================================
// Reference Types
// ============================================================================

export interface MetricRef {
  metric_id?: string
  metric?: SemanticMetric
  alias?: string
  join_on?: string[]
}

// ============================================================================
// Override Types
// ============================================================================

export interface MetricOverrides {
  add?: OverrideComponents
  replace?: OverrideComponents
  exclude?: ExcludeComponents

  // Scalar overrides
  table_name?: string
  limit?: number
  grouped?: boolean
  ordered?: boolean
}

export interface OverrideComponents {
  measures?: SemanticMeasure[]
  dimensions?: SemanticDimension[]
  filters?: SemanticFilter[]
  joins?: SemanticJoin[]
  order?: SemanticOrderSequence[]
}

export interface ExcludeComponents {
  measures?: string[]
  dimensions?: string[]
  filters?: string[]
  joins?: string[]
}

export interface IncludedComponents {
  measures?: string[]
  dimensions?: string[]
  filters?: string[]
  joins?: string[]
}

// ============================================================================
// Derivation Types
// ============================================================================

export type DerivedEntityType =
  // Aggregate-as-window (custom Cortex derivations)
  | 'percent_of_total'
  | 'running_total'
  | 'cumulative_count'
  | 'share'
  // Arithmetic (two-input operations)
  | 'divide'
  | 'multiply'
  | 'subtract'
  | 'add'
  // PostgreSQL general-purpose window functions
  | 'row_number'
  | 'rank'
  | 'dense_rank'
  | 'percent_rank'
  | 'cume_dist'
  | 'ntile'
  | 'lag'
  | 'lead'
  | 'first_value'
  | 'last_value'
  | 'nth_value'

export interface SourceRef {
  measure: string
  by?: string  // Second operand for two-input ops (divide, multiply, subtract, add)
}

export interface DerivedEntity {
  name: string
  type: DerivedEntityType
  source: SourceRef
  order_dimension?: string
  partition_by?: string
  offset?: number
  default_value?: any
  n?: number
  formatting?: OutputFormat[]
}

// ============================================================================
// Component Types (imported from metrics)
// ============================================================================

export interface SemanticMeasure {
  name: string
  type: string
  query: string
  alias?: string
  description?: string
  formatting?: OutputFormat[]
  meta?: Record<string, any>
}

export interface SemanticDimension {
  name: string
  query: string
  alias?: string
  description?: string
  type?: string
  meta?: Record<string, any>
}

export interface SemanticFilter {
  name: string
  query: string
  operator: string
  value?: any
  min_value?: any
  max_value?: any
  values?: any[]
  description?: string
  meta?: Record<string, any>
}

export interface SemanticJoin {
  name: string
  type: string
  table: string
  on: string
  alias?: string
  description?: string
  meta?: Record<string, any>
}

export interface SemanticOrderSequence {
  name: string
  direction: 'asc' | 'desc'
  nulls?: 'first' | 'last'
}

export interface OutputFormat {
  type: string
  config?: Record<string, any>
}

// ============================================================================
// Policy Types
// ============================================================================

export interface CachePreference {
  enabled: boolean
  ttl?: number
  strategy?: string
}

export interface RefreshPolicy {
  enabled: boolean
  interval?: number
  strategy?: string
}

export interface ParameterDefinition {
  type: string
  default?: any
  required?: boolean
  description?: string
  options?: any[]
}

// ============================================================================
// Composable Helper Types
// ============================================================================

export interface MetricVariantFilters {
  source_metric_id?: string
  public?: boolean
  search?: string
}

export interface MetricVariantExecutionRequest {
  environment_id: string
  measures?: string[]
  dimensions?: string[]
  filters?: any[]
  limit?: number
  cache?: CachePreference
  refresh?: RefreshPolicy
  parameters?: Record<string, any>
}

// ============================================================================
// API Response Types
// ============================================================================

export interface MetricVariantListResponse {
  variants: SemanticMetricVariant[]
  total: number
  page?: number
  page_size?: number
}

export interface MetricVariantExecutionResponse {
  data: any[]
  metadata: {
    columns: string[]
    row_count: number
    execution_time_ms: number
    cached: boolean
  }
  sql?: string
}

// ============================================================================
// UI State Types
// ============================================================================

export interface VariantFormState {
  basic: {
    name: string
    alias: string
    description: string
    public: boolean
  }
  source: MetricRef | null
  include: IncludedComponents | null
  overrides: MetricOverrides | null
  derivations: DerivedEntity[]
  combine: MetricRef[]
}

export type VariantFormStep = 'basic' | 'source' | 'overrides' | 'derivations' | 'combine'

export interface VariantValidationErrors {
  basic?: Record<string, string>
  source?: string
  include?: Record<string, string>
  overrides?: Record<string, string>
  derivations?: Record<string, string>
  combine?: Record<string, string>
}