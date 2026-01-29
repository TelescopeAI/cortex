export interface Workspace {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Environment {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  environment_id: string;
  name: string;
  alias?: string;
  description?: string;
  source_catalog: 'DATABASE' | 'API' | 'FILE';
  source_type: 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift' | 'mongodb' | 'dynamodb' | 'couchbase' | 'spreadsheet';
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UploadedFile {
  filename: string;
  size: number;
  type: string;
  session_id: string;
  uploaded_at: string;
}

export interface SpreadsheetSourceConfig {
  provider_type: 'csv' | 'gsheets';
  session_id?: string;
  selected_sheets?: string[];
  sqlite_path?: string;
  last_synced?: string;
  table_mappings?: Record<string, string>;
  table_hashes?: Record<string, string>;
}

// Database config type definitions
export interface HostBasedSQLConfig {
  host: string
  port: number
  username: string
  password: string
  database: string
  dialect: string
}

export interface SQLiteConfig {
  database: string
  dialect: string
}

export interface BigQueryConfig {
  project_id: string
  dataset_id?: string
  service_account_details: Record<string, any>
  serviceAccountJson?: string
}

export interface SpreadsheetConfig {
  provider_type: 'csv' | 'gsheets'
  file_id?: string
  spreadsheet_id?: string
  session_id?: string
  selected_sheets?: string[]
  sqlite_path?: string
  last_synced?: string
  table_mappings?: Record<string, string>
  table_hashes?: Record<string, string>
}

// Union type for all database configs
export type DatabaseConfig =
  | HostBasedSQLConfig
  | SQLiteConfig
  | BigQueryConfig
  | SpreadsheetConfig

export interface SheetMetadata {
  name: string;
  row_count: number;
  columns: string[];
  source_type?: string;
}

export interface DependentMetricInfo {
  id: string;
  name: string;
  alias?: string | null;
  version_count: number;
}

export interface DataSourceDependencies {
  metrics: DependentMetricInfo[];
}

export interface DataSourceDependenciesError {
  error: 'DataSourceHasDependencies';
  message: string;
  data_source_id: string;
  dependencies: DataSourceDependencies;
}

export interface DependentDataSourceInfo {
  id: string;
  name: string;
  alias?: string;
  metrics: DependentMetricInfo[];
}

export interface FileDependencies {
  data_sources: DependentDataSourceInfo[];
}

export interface FileDependenciesError {
  error: 'FileHasDependencies';
  message: string;
  file_id: string;
  dependencies: FileDependencies;
}
