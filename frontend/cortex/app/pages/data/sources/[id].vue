<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useDataSources } from '~/composables/useDataSources';
import { useApi } from '~/composables/useApi';
import type { DataSource } from '~/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { ArrowLeft, Calendar, Edit, Trash2, Database, Globe, FileText, Settings, Activity } from 'lucide-vue-next';
import EditDataSourceDialog from '~/components/EditDataSourceDialog.vue';
import { toast } from 'vue-sonner';

// Import database configuration components
import PostgreSQLConfig from '~/components/data-sources/PostgreSQLConfig.vue'
import MySQLConfig from '~/components/data-sources/MySQLConfig.vue'
import SQLiteConfig from '~/components/data-sources/SQLiteConfig.vue'
import BigQueryConfig from '~/components/data-sources/BigQueryConfig.vue'
import CommonSQLConfig from '~/components/data-sources/CommonSQLConfig.vue'

const route = useRoute();
const router = useRouter();
const { apiUrl } = useApi();
const { dataSources } = useDataSources();

// Fetch specific data source data
const { data: dataSource, pending, error, refresh } = useFetch<DataSource>(
  () => apiUrl(`/api/v1/data/sources/${route.params.id}`),
  { default: () => undefined }
);

// Use data source from list if available, otherwise use fetched data
const currentDataSource = computed<DataSource | undefined>(() => {
  // Always prioritize the fetched data source if it exists
  if (dataSource.value) {
    return dataSource.value;
  }
  // Fall back to the list data if fetched data is not available
  return dataSources.value?.find((ds) => ds.id === route.params.id);
});

// Get catalog icon based on source catalog
function getCatalogIcon(catalog: string) {
  switch (catalog) {
    case 'DATABASE':
      return Database;
    case 'API':
      return Globe;
    case 'FILE':
      return FileText;
    default:
      return Database;
  }
}

// Get catalog color for badge
function getCatalogColor(catalog: string) {
  switch (catalog) {
    case 'DATABASE':
      return 'bg-blue-100 text-blue-800';
    case 'API':
      return 'bg-green-100 text-green-800';
    case 'FILE':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

async function handleDataSourceUpdated(updatedDataSource: DataSource) {
  // Directly update the fetched data source with the API response
  if (dataSource.value) {
    dataSource.value = updatedDataSource;
  }
  
  toast.success('Data source updated successfully');
}

async function handleDelete() {
  if (!currentDataSource.value) return;
  
  if (!confirm('Are you sure you want to delete this data source? This action cannot be undone.')) {
    return;
  }
  
  try {
    await $fetch(apiUrl(`/api/v1/data/sources/${currentDataSource.value.id}`), {
      method: 'DELETE'
    });
    
    toast.success('Data source deleted successfully');
    await refresh();
    router.push('/data/sources');
  } catch (error: any) {
    console.error('Error deleting data source:', error);
    toast.error(error?.data?.detail || 'Failed to delete data source');
  }
}

async function testConnection() {
  if (!currentDataSource.value) return;
  
  try {
    toast.info('Testing connection...');
    const response = await $fetch(apiUrl(`/api/v1/data/sources/${currentDataSource.value.id}/ping`), {
      method: 'POST'
    });
    
    // The ping endpoint returns an empty object on success
    toast.success('Connection test successful!');
  } catch (error: any) {
    console.error('Error testing connection:', error);
    toast.error(error?.data?.detail || 'Failed to test connection');
  }
}

async function viewSchema() {
  if (!currentDataSource.value) return;
  
  try {
    toast.info('Fetching schema...');
    const response = await $fetch(apiUrl(`/api/v1/data/sources/${currentDataSource.value.id}/schema`), {
      method: 'GET'
    });
    
    // The schema endpoint returns schema information
    console.log('Schema:', response);
    toast.success('Schema fetched successfully! Check console for details.');
  } catch (error: any) {
    console.error('Error fetching schema:', error);
    toast.error(error?.data?.detail || 'Failed to fetch schema');
  }
}

function goBack() {
  router.push('/data/sources');
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <Button variant="outline" size="sm" @click="goBack">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Data Sources
        </Button>
        <h1 class="text-2xl font-bold">Data Source Details</h1>
      </div>
      <div class="flex gap-2">
        <EditDataSourceDialog 
          v-if="currentDataSource" 
          :data-source="currentDataSource" 
          @updated="handleDataSourceUpdated"
        />
        <Button variant="outline" size="sm" class="text-red-600 hover:text-red-700" @click="handleDelete">
          <Trash2 class="w-4 h-4 mr-2" />
          Delete
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="pending" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading data source details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">Error loading data source details</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>

    <!-- Data Source Details -->
    <div v-else-if="currentDataSource" class="space-y-6">
      <!-- Main Info Card -->
      <Card>
        <CardHeader>
          <div class="flex items-center justify-between">
            <CardTitle class="text-xl">{{ currentDataSource.name }}</CardTitle>
            <component :is="getCatalogIcon(currentDataSource.source_catalog)" class="w-6 h-6 text-gray-500" />
          </div>
          <div class="flex items-center gap-2">
            <Badge :class="getCatalogColor(currentDataSource.source_catalog)">
              {{ currentDataSource.source_catalog }}
            </Badge>
            <Badge variant="outline">
              {{ currentDataSource.source_type }}
            </Badge>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <div v-if="currentDataSource.description">
            <h3 class="font-medium text-gray-900 mb-2">Description</h3>
            <p class="text-gray-600">{{ currentDataSource.description }}</p>
          </div>
          
          <div v-if="currentDataSource.alias">
            <h3 class="font-medium text-gray-900 mb-2">Alias</h3>
            <p class="font-mono text-sm bg-gray-100 px-2 py-1 rounded">{{ currentDataSource.alias }}</p>
          </div>
          
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <Calendar class="w-4 h-4" />
            <span>Created {{ new Date(currentDataSource.created_at).toLocaleDateString() }}</span>
            <span>•</span>
            <span>Updated {{ new Date(currentDataSource.updated_at).toLocaleDateString() }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Data Source Information Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Data Source Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div>
              <span class="font-medium text-gray-700">Data Source ID:</span>
              <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{{ currentDataSource.id }}</span>
            </div>
            <div>
              <span class="font-medium text-gray-700">Environment ID:</span>
              <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{{ currentDataSource.environment_id }}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Configuration Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Database Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div v-if="currentDataSource.source_type" class="border rounded-lg p-4 bg-muted/50">
            <PostgreSQLConfig
              v-if="currentDataSource.source_type === 'postgresql'"
              :model-value="currentDataSource.config"
              disabled
            />
            <MySQLConfig
              v-else-if="currentDataSource.source_type === 'mysql'"
              :model-value="currentDataSource.config"
              disabled
            />
            <SQLiteConfig
              v-else-if="currentDataSource.source_type === 'sqlite'"
              :model-value="currentDataSource.config"
              disabled
            />
            <BigQueryConfig
              v-else-if="currentDataSource.source_type === 'bigquery'"
              :model-value="currentDataSource.config"
              disabled
            />
            <CommonSQLConfig
              v-else-if="['oracle', 'snowflake', 'redshift'].includes(currentDataSource.source_type)"
              :model-value="currentDataSource.config"
              :database-type="currentDataSource.source_type as 'oracle' | 'snowflake' | 'redshift'"
              disabled
            />
            <div v-else class="text-center py-4 text-muted-foreground">
              <p>Configuration display not available for this database type.</p>
            </div>
          </div>
          <div v-else class="text-center py-4 text-muted-foreground">
            <p>No configuration available</p>
          </div>
        </CardContent>
      </Card>

      <!-- Quick Actions Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" class="justify-start" @click="testConnection">
              <Activity class="w-4 h-4 mr-2" />
              Test Connection
            </Button>
            <Button variant="outline" class="justify-start" @click="viewSchema">
              <Settings class="w-4 h-4 mr-2" />
              View Schema
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Not Found -->
    <div v-else class="text-center py-8">
      <p class="text-gray-500">Data source not found</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>
  </div>
</template> 