import { computed } from 'vue'

export interface ColumnMetadata {
  name: string
  type: 'string' | 'number' | 'date' | 'boolean'
  nullable: boolean
  description?: string
}

export interface TableMetadata {
  name: string
  columns: ColumnMetadata[]
}

export function useSchemaMetadata(availableTables: string[], availableColumns: Record<string, string[]>) {
  // Enhanced column type detection
  const getColumnType = (table: string, column: string): 'string' | 'number' | 'date' | 'boolean' => {
    const col = column.toLowerCase()
    
    // Date/timestamp patterns
    if (col.includes('date') || col.includes('time') || col.includes('created') || col.includes('updated') || col.includes('timestamp')) {
      return 'date'
    }
    
    // Boolean patterns
    if (col.includes('is_') || col.includes('has_') || col.includes('active') || col.includes('enabled') || col === 'present') {
      return 'boolean'
    }
    
    // Numeric patterns
    if (col.includes('count') || col.includes('total') || col.includes('amount') || col.includes('price') || col.includes('percent') || col.includes('rate') || col.includes('score') || col.includes('duration')) {
      return 'number'
    }
    
    // Default to string
    return 'string'
  }

  // Get table metadata
  const getTableMetadata = (tableName: string): TableMetadata => {
    const columns = availableColumns[tableName] || []
    return {
      name: tableName,
      columns: columns.map(col => ({
        name: col,
        type: getColumnType(tableName, col),
        nullable: true, // Assume nullable unless we have schema info
        description: `${col} from ${tableName}`
      }))
    }
  }

  // Get all metadata
  const schemaMetadata = computed(() => {
    return availableTables.map(table => getTableMetadata(table))
  })

  // Find column metadata
  const findColumnMetadata = (table: string, column: string): ColumnMetadata | null => {
    const tableMeta = getTableMetadata(table)
    return tableMeta.columns.find(col => col.name === column) || null
  }

  // Get appropriate operators for column type
  const getOperatorsForType = (type: 'string' | 'number' | 'date' | 'boolean') => {
    const baseOperators = ['=', '!=', '>', '<', '>=', '<=', 'IS NULL', 'IS NOT NULL']
    
    switch (type) {
      case 'string':
        return [...baseOperators, 'LIKE', 'IN', 'NOT IN']
      case 'number':
        return [...baseOperators, 'BETWEEN', 'IN', 'NOT IN']
      case 'date':
        return [...baseOperators, 'BETWEEN', 'IN', 'NOT IN']
      case 'boolean':
        return ['=', '!=', 'IS NULL', 'IS NOT NULL']
      default:
        return baseOperators
    }
  }

  return {
    getColumnType,
    getTableMetadata,
    schemaMetadata,
    findColumnMetadata,
    getOperatorsForType
  }
}
