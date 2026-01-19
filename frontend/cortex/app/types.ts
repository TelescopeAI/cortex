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

export interface SheetMetadata {
  name: string;
  row_count: number;
  columns: string[];
  source_type?: string;
}
