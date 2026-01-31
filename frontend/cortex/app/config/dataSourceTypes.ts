// Capitalize first letter of each word
function capitalizeWords(str: string): string {
  return str
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

export interface DataSourceTypeMetadata {
  type: string
  label: string
  catalog: 'DATABASE' | 'API' | 'FILE'
  icon: {
    type: 'asset' | 'lucide'
    name: string
  }
  defaultConfig: Record<string, any>
  configComponent?: string
  validateConfig: (config: any) => boolean
  generateName?: (config: any) => string
}

export const DATA_SOURCE_TYPES: Record<string, DataSourceTypeMetadata> = {
  postgresql: {
    type: 'postgresql',
    label: 'PostgreSQL',
    catalog: 'DATABASE',
    icon: { type: 'asset', name: 'postgres' },
    defaultConfig: { host: '', port: 5432, username: '', password: '', database: '', dialect: 'postgresql' },
    configComponent: 'PostgreSQLConfig',
    validateConfig: (c) => !!(c.host && c.port && c.username && c.password && c.database && c.dialect),
    generateName: (c) => `${capitalizeWords(c.host)} PostgreSQL Dataset`
  },
  mysql: {
    type: 'mysql',
    label: 'MySQL',
    catalog: 'DATABASE',
    icon: { type: 'asset', name: 'mysql' },
    defaultConfig: { host: '', port: 3306, username: '', password: '', database: '', dialect: 'mysql' },
    configComponent: 'MySQLConfig',
    validateConfig: (c) => !!(c.host && c.port && c.username && c.password && c.database && c.dialect),
    generateName: (c) => `${capitalizeWords(c.host)} MySQL Dataset`
  },
  sqlite: {
    type: 'sqlite',
    label: 'SQLite',
    catalog: 'DATABASE',
    icon: { type: 'asset', name: 'sqlite' },
    defaultConfig: { database: '', dialect: 'sqlite' },
    configComponent: 'SQLiteConfig',
    validateConfig: (c) => !!(c.database && c.dialect),
    generateName: (c) => c.database ? `${capitalizeWords(c.database.split('/').pop()?.split('\\').pop()?.replace(/\.[^/.]+$/, '') || 'SQLite')} SQLite Dataset` : 'SQLite Dataset'
  },
  bigquery: {
    type: 'bigquery',
    label: 'BigQuery',
    catalog: 'DATABASE',
    icon: { type: 'asset', name: 'bigquery' },
    defaultConfig: { project_id: '', dataset_id: '', service_account_details: {}, serviceAccountJson: '' },
    configComponent: 'BigQueryConfig',
    validateConfig: (c) => !!(c.project_id && c.service_account_details && Object.keys(c.service_account_details).length > 0),
    generateName: (c) => `${c.project_id} BigQuery Dataset`
  },
  spreadsheet: {
    type: 'spreadsheet',
    label: 'Spreadsheets',
    catalog: 'FILE',
    icon: { type: 'lucide', name: 'file-spreadsheet' },
    defaultConfig: { provider_type: 'csv', file_id: '' },
    validateConfig: (c) => !!c.file_id,
    generateName: (c) => 'Spreadsheet'
  }
}

// Helper to get ordered list of source types for UI
export function getOrderedSourceTypes(): DataSourceTypeMetadata[] {
  const order = ['postgresql', 'mysql', 'sqlite', 'bigquery', 'spreadsheet']
  return order.map(type => DATA_SOURCE_TYPES[type]).filter((type): type is DataSourceTypeMetadata => !!type)
}
