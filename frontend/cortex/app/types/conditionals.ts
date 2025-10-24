// TypeScript interfaces for conditional logic
export interface Condition {
  when_clauses: WhenClause[]
  else_return: any | ColumnField  // ← Can be ColumnField
}

export interface WhenClause {
  field: ColumnField
  operator: ComparisonOperator
  compare_values?: any | any[] | ColumnField  // ← Can be ColumnField
  then_return: any | ColumnField  // ← Can be ColumnField
  
  // NEW: Nested AND/OR support
  combine_with?: LogicalOperator
  additional_conditions?: WhenClause[]
}

export interface ColumnField {
  column: string
  table?: string
  transforms?: Transform[]
}

export interface Transform {
  function: TransformFunction
  params?: Record<string, any>
}

export type TransformFunction = 
  // String functions
  | 'COALESCE' | 'LOWER' | 'UPPER' | 'CONCAT' | 'TRIM' | 'SUBSTRING'
  // Math functions
  | 'ROUND' | 'ABS' | 'CEIL' | 'FLOOR'
  // Date functions
  | 'EXTRACT' | 'DATE_TRUNC' | 'DATE_PART'
  // Type casting
  | 'CAST'

export type ComparisonOperator = 
  | '=' | '!=' | '>' | '<' | '>=' | '<='
  | 'IN' | 'NOT IN' | 'LIKE' | 'BETWEEN'
  | 'IS NULL' | 'IS NOT NULL'

export type LogicalOperator = 'AND' | 'OR'

