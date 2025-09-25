export enum OutputFormatType {
  RAW = "raw",
  COMBINE = "combine",
  CALCULATE = "calculate",
  FORMAT = "format",
  CAST = "cast"
}

export enum OutputFormatMode {
  IN_QUERY = "in_query",
  POST_QUERY = "post_query"
}

export enum FormatType {
  DATETIME = "datetime",
  NUMBER = "number",
  CURRENCY = "currency",
  PERCENTAGE = "percentage",
  CUSTOM = "custom"
}

export interface OutputFormat {
  name: string
  type: OutputFormatType
  description?: string
  mode?: OutputFormatMode

  // For COMBINE type
  source_columns?: string[]
  delimiter?: string
  
  // For CALCULATE type
  operation?: string // e.g., "add", "subtract", "multiply", "divide"
  operands?: string[]
  
  // For CAST type
  target_type?: string // e.g., "string", "integer", "float", "date"
  
  // For FORMAT type
  format_type?: FormatType
  format_string?: string // e.g., "%.2f", "YYYY-MM-DD", "DD-MM-YYYY"
}

export interface SemanticMeasure {
  name: string
  description?: string
  type: string
  formatting?: OutputFormat[]
  alias?: string
  query?: string
  table?: string
  primary_key?: string
}

export interface SemanticDimension {
  name: string
  description?: string
  query: string
  table?: string
  formatting?: OutputFormat[]
}

export interface SemanticFilter {
  name: string
  description?: string
  query: string
  table?: string
  operator?: string
  value?: any
  value_type?: string
  filter_type?: string
  is_active?: boolean
  custom_expression?: string
  values?: any[]
  min_value?: any
  max_value?: any
  formatting?: OutputFormat[]
}

export type SemanticJoinType = 'inner' | 'left' | 'right' | 'full'

export interface SemanticJoinCondition {
  left_table: string
  left_column: string
  right_table: string
  right_column: string
}

export interface SemanticJoin {
  name: string
  description?: string
  join_type: SemanticJoinType
  left_table: string
  right_table: string
  conditions?: SemanticJoinCondition[]
  on?: string
  alias?: string
}
