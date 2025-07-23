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
  source_type: 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift' | 'mongodb' | 'dynamodb' | 'couchbase';
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}
