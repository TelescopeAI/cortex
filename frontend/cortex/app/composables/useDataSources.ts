import { useFetch } from 'nuxt/app';
import { computed, watch } from 'vue';
import { useStorage } from '@vueuse/core';
import type { DataSource } from '~/types';

export function useDataSources() {
  const { apiUrl } = useApi();
  
  // Get selected environment ID from storage
  const selectedEnvironmentId = useStorage<string | null>('selectedEnvironmentId', null);

  // Fetch data sources for the selected environment
  const { data, pending, error, refresh, execute } = useFetch<DataSource[]>(
    apiUrl('/api/v1/environments/{environment_id}/data/sources'),
    { 
      watch: false, // Disable automatic watching
      default: () => [],
      immediate: false // Don't execute immediately
    }
  );

  // Watch for environment changes and execute fetch only when environment is selected
  watch(selectedEnvironmentId, (newEnvironmentId) => {
    if (newEnvironmentId) {
      // Manually construct the URL and execute
      const url = apiUrl(`/api/v1/environments/${newEnvironmentId}/data/sources`);
      $fetch(url).then(result => {
        data.value = result as DataSource[];
      }).catch(err => {
        console.error('Failed to fetch data sources:', err);
        data.value = [];
      });
    } else {
      // Clear data when no environment is selected
      data.value = [];
    }
  }, { immediate: true });

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
    
    // Refresh the data sources list
    await refresh();
    
    return response;
  }

  // Return empty array if no environment is selected
  const dataSources = computed(() => {
    if (!selectedEnvironmentId.value) return [];
    return data.value || [];
  });

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
    loading: pending,
    error,
    refresh,
    selectedEnvironmentId,
    createDataSource,
    getDataSource,
    getDataSourceSchema
  };
} 