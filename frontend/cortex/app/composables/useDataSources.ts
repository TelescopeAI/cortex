import { useEnvironments } from '~/composables/useEnvironments';
import { computed, ref, watch } from 'vue';
import type { DataSource, DataSourceDependenciesError, DataSourceQueryResponse } from '~/types';

export function useDataSources() {
  const { apiUrl } = useApi();
  
  // Get selected environment ID from the environments composable
  const { selectedEnvironmentId } = useEnvironments();

  // Use ref for local state to avoid reactivity issues
  const loading = ref(false);
  const executing = ref(false);
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

  // Watch for environment changes and refresh data sources
  watch(selectedEnvironmentId, (newEnvId) => {
    if (newEnvId) {
      refresh();
    }
  }, { immediate: true });

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

  // Query a data source directly
  const queryDataSource = async (
    dataSourceId: string,
    params: {
      table?: string
      statement?: string
      limit?: number | null
      offset?: number
    }
  ) => {
    if (!selectedEnvironmentId.value) {
      throw new Error('No environment selected')
    }

    executing.value = true

    try {
      const body: Record<string, any> = {
        environment_id: selectedEnvironmentId.value,
      }
      if (params.table) body.table = params.table
      if (params.statement) body.statement = params.statement
      if (params.limit != null) body.limit = params.limit
      if (params.offset !== undefined) body.offset = params.offset

      const response = await $fetch<DataSourceQueryResponse>(
        apiUrl(`/api/v1/data/sources/${dataSourceId}/query`),
        { method: 'POST', body }
      )
      return response
    } catch (err: any) {
      console.error('Failed to query data source:', err)
      throw new Error(err?.data?.detail || 'Failed to query data source')
    } finally {
      executing.value = false
    }
  }

  /**
   * Delete a data source
   * @param id - Data source ID
   * @param cascade - If true, delete all dependent metrics first
   * @returns Promise that resolves when deleted or rejects with error details
   */
  async function deleteDataSource(id: string, cascade: boolean = false) {
    try {
      await $fetch(apiUrl(`/api/v1/data/sources/${id}${cascade ? '?cascade=true' : ''}`), {
        method: 'DELETE'
      });

      // Refresh data sources list
      await refresh();

      return { success: true };
    } catch (err: any) {
      console.error('Failed to delete data source:', err);

      // Extract error detail
      let errorDetail = err.data?.detail || err.data;

      // Parse if it's a string
      if (typeof errorDetail === 'string') {
        try {
          errorDetail = JSON.parse(errorDetail);
        } catch (parseErr) {
          console.error('Failed to parse error detail:', parseErr);
        }
      }

      // If 409 Conflict, throw structured dependencies error
      if (err.status === 409 && errorDetail?.error === 'DataSourceHasDependencies') {
        throw {
          error: 'DataSourceHasDependencies',
          message: errorDetail.message,
          data_source_id: errorDetail.data_source_id,
          dependencies: errorDetail.dependencies
        } as DataSourceDependenciesError;
      }

      throw err;
    }
  }

  return {
    dataSources,
    loading,
    executing,
    error,
    refresh,
    selectedEnvironmentId,
    createDataSource,
    getDataSource,
    getDataSourceSchema,
    queryDataSource,
    deleteDataSource
  };
} 