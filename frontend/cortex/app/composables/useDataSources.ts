import { useEnvironments } from '~/composables/useEnvironments';
import { computed, ref } from 'vue';
import type { DataSource } from '~/types';

export function useDataSources() {
  const { apiUrl } = useApi();
  
  // Get selected environment ID from the environments composable
  const { selectedEnvironmentId } = useEnvironments();

  // Use ref for local state to avoid reactivity issues
  const loading = ref(false);
  const error = ref<string | null>(null);
  const data = ref<DataSource[]>([]);

  // Simple refresh function that fetches data for the current environment
  async function refresh() {
    if (!selectedEnvironmentId.value) {
      // Clear data when no environment is selected
      data.value = [];
      loading.value = false;
      error.value = null;
      return;
    }

    loading.value = true;
    error.value = null;
    
    try {
      const url = apiUrl(`/api/v1/environments/${selectedEnvironmentId.value}/data/sources`);
      const result = await $fetch<DataSource[]>(url);
      data.value = result;
    } catch (err: any) {
      console.error('Failed to fetch data sources:', err);
      error.value = err.message || 'Failed to fetch data sources';
      data.value = [];
    } finally {
      loading.value = false;
    }
  }

  // Create a new data source
  async function createDataSource(dataSource: {
    environment_id: string;
    name: string;
    alias: string;
    description?: string;
    source_catalog: 'DATABASE' | 'API' | 'FILE';
    source_type: 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift' | 'mongodb' | 'dynamodb' | 'couchbase';
    config: Record<string, any>;
  }) {
    const response = await $fetch<DataSource>(apiUrl('/api/v1/data/sources'), {
      method: 'POST',
      body: dataSource,
    });
    
    return response;
  }

  // Return empty array if no environment is selected
  const dataSources = computed(() => {
    if (!selectedEnvironmentId.value) {
      return [];
    }
    
    return data.value || [];
  });

  // Remove the deep watcher as it might cause infinite loops

  // Get a specific data source by ID
  const getDataSource = async (dataSourceId: string): Promise<DataSource | null> => {
    try {
      const response = await $fetch<DataSource>(apiUrl(`/api/v1/data/sources/${dataSourceId}`));
      return response;
    } catch (err) {
      console.error('Failed to fetch data source:', err);
      return null;
    }
  };

  // Get data source schema
  const getDataSourceSchema = async (dataSourceId: string) => {
    if (!dataSourceId) {
      throw new Error('Data source ID is required')
    }

    try {
      const response = await $fetch<{
        status: string
        message: string
        data_source_id: string
        data_source_name: string
        source_type: string
        schema: {
          tables: Array<{
            name: string
            columns: Array<{
              name: string
              type: string
              nullable?: boolean
              default?: any
              primary_key?: boolean
              foreign_key?: boolean
            }>
          }>
        }
      }>(apiUrl(`/api/v1/data/sources/${dataSourceId}/schema`))

      return response.schema
    } catch (error: any) {
      console.error('Failed to fetch data source schema:', error)
      throw new Error(error?.data?.detail || 'Failed to fetch data source schema')
    }
  }

  return {
    dataSources,
    loading,
    error,
    refresh,
    selectedEnvironmentId,
    createDataSource,
    getDataSource,
    getDataSourceSchema
  };
} 