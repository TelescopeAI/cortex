<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useDataSources } from '~/composables/useDataSources';
import { useApi } from '~/composables/useApi';
import type { DataSource, DataSourceDependenciesError } from '~/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from '~/components/ui/alert-dialog';
import { ArrowLeft, Calendar, Edit, Trash2, Database, Globe, FileText, Settings, Activity, Server, Cloud, Zap, CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-vue-next';
import EditDataSourceDialog from '~/components/EditDataSourceDialog.vue';
import SourceSchemaViewer from '~/components/SourceSchemaViewer.vue';
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
const { dataSources, deleteDataSource } = useDataSources();

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

// State for Quick Actions results
const connectionTestResult = ref<{
  status: 'success' | 'failed' | null
  message: string
  timestamp: Date | null
}>({
  status: null,
  message: '',
  timestamp: null
});

const schemaResult = ref<{
  tables: Array<{
    name: string
    columns: Array<{
      name: string
      type: string
      max_length?: number
      precision?: number
      scale?: number
      nullable?: boolean
      default_value?: string
    }>
    primary_keys: string[]
    foreign_keys: Array<{
      table: string
      relations: Array<{
        column: string
        referenced_table: string
        referenced_column: string
      }>
    }>
  }>
} | null>(null);

const isLoadingConnection = ref(false);
const isLoadingSchema = ref(false);

// State for delete dialogs
const showDeleteDialog = ref(false);
const showCascadeDialog = ref(false);
const dependenciesToDelete = ref<DataSourceDependenciesError | null>(null);
const isDeleting = ref(false);

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

// Humanize source type names
function getSourceTypeName(sourceType: string): string {
  const typeMap: Record<string, string> = {
    'postgresql': 'PostgreSQL',
    'mysql': 'MySQL',
    'sqlite': 'SQLite',
    'oracle': 'Oracle',
    'bigquery': 'BigQuery',
    'snowflake': 'Snowflake',
    'redshift': 'Redshift',
    'mongodb': 'MongoDB',
    'dynamodb': 'DynamoDB',
    'couchbase': 'Couchbase'
  };
  
  return typeMap[sourceType] || sourceType.charAt(0).toUpperCase() + sourceType.slice(1);
}

// Get source type icon
function getSourceTypeIcon(sourceType: string) {
  switch (sourceType) {
    case 'postgresql':
      return Database;
    case 'mysql':
      return Database;
    case 'sqlite':
      return Database;
    case 'oracle':
      return Server;
    case 'bigquery':
      return Cloud;
    case 'snowflake':
      return Cloud;
    case 'redshift':
      return Cloud;
    case 'mongodb':
      return Database;
    case 'dynamodb':
      return Zap;
    case 'couchbase':
      return Database;
    default:
      return Database;
  }
}

async function handleDataSourceUpdated(updatedDataSource: DataSource) {
  // Directly update the fetched data source with the API response
  if (dataSource.value) {
    dataSource.value = updatedDataSource;
  }
  
  toast.success('Data source updated successfully');
}

function confirmDelete() {
  showDeleteDialog.value = true;
}

async function handleDelete(cascade: boolean = false) {
  if (!currentDataSource.value) return;

  isDeleting.value = true;

  try {
    await deleteDataSource(currentDataSource.value.id, cascade);

    toast.success('Data source deleted successfully');
    showDeleteDialog.value = false;
    showCascadeDialog.value = false;
    router.push('/data/sources');
  } catch (error: any) {
    console.error('Error deleting data source:', error);

    // Check if it's a dependencies error (409 Conflict)
    if (error.error === 'DataSourceHasDependencies') {
      dependenciesToDelete.value = error;
      showDeleteDialog.value = false;
      showCascadeDialog.value = true;
    } else {
      toast.error(error?.message || error?.data?.detail || 'Failed to delete data source');
      showDeleteDialog.value = false;
    }
  } finally {
    isDeleting.value = false;
  }
}

function handleCancelDelete() {
  showDeleteDialog.value = false;
  showCascadeDialog.value = false;
  dependenciesToDelete.value = null;
}

async function handleCascadeDelete() {
  await handleDelete(true);
}

async function testConnection() {
  if (!currentDataSource.value) return;
  
  isLoadingConnection.value = true;
  connectionTestResult.value = {
    status: null,
    message: '',
    timestamp: null
  };
  
  try {
    const response = await $fetch<{
      status: 'success' | 'failed'
      message: string
      data_source_id: string
      data_source_name: string
      source_type: string
      error?: string
    }>(apiUrl(`/api/v1/data/sources/${currentDataSource.value.id}/ping`), {
      method: 'POST'
    });
    
    connectionTestResult.value = {
      status: response.status || 'success',
      message: response.message || 'Connection test successful!',
      timestamp: new Date()
    };
    
    if (response.status === 'success') {
    toast.success('Connection test successful!');
    } else {
      toast.error(response.message || 'Connection test failed');
    }
  } catch (error: any) {
    console.error('Error testing connection:', error);
    const errorMessage = error?.data?.detail || error?.message || 'Failed to test connection';
    connectionTestResult.value = {
      status: 'failed',
      message: errorMessage,
      timestamp: new Date()
    };
    toast.error(errorMessage);
  } finally {
    isLoadingConnection.value = false;
  }
}

async function viewSchema() {
  if (!currentDataSource.value) return;
  
  isLoadingSchema.value = true;
  schemaResult.value = null;
  
  try {
    const response = await $fetch<{
      data_source_id: string
      data_source_name: string
      source_type: string
      schema: {
        tables: Array<{
          name: string
          columns: Array<{
            name: string
            type: string
            max_length?: number
            precision?: number
            scale?: number
            nullable?: boolean
            default_value?: string
          }>
          primary_keys: string[]
          foreign_keys: Array<{
            table: string
            relations: Array<{
              column: string
              referenced_table: string
              referenced_column: string
            }>
          }>
        }>
      }
    }>(apiUrl(`/api/v1/data/sources/${currentDataSource.value.id}/schema`), {
      method: 'GET'
    });
    
    schemaResult.value = response.schema;
    toast.success('Schema fetched successfully!');
  } catch (error: any) {
    console.error('Error fetching schema:', error);
    toast.error(error?.data?.detail || 'Failed to fetch schema');
    schemaResult.value = null;
  } finally {
    isLoadingSchema.value = false;
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
      </div>
      <div class="flex gap-2">
        <EditDataSourceDialog 
          v-if="currentDataSource" 
          :data-source="currentDataSource" 
          @updated="handleDataSourceUpdated"
        />
        <Button variant="outline" size="sm" class="text-red-600 hover:text-red-700" @click="confirmDelete">
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
          <div class="flex flex-col items-start gap-2">
            <div class="space-y-2">
            <div>
              <span class="font-mono text-sm">{{ currentDataSource.id }}</span>
            </div>
          </div>
          <div class="flex gap-x-4">
            <Badge :class="getCatalogColor(currentDataSource.source_catalog)">
              {{ currentDataSource.source_catalog }}
            </Badge>
            <Badge variant="outline" class="flex items-center gap-1">
              <component :is="getSourceTypeIcon(currentDataSource.source_type)" class="w-3 h-3" />
              {{ getSourceTypeName(currentDataSource.source_type) }}
            </Badge>
          </div>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <div v-if="currentDataSource.description">
            <h3 class="font-medium text-gray-900 mb-2">Description</h3>
            <p class="text-gray-600">{{ currentDataSource.description }}</p>
          </div>
          
          <div v-if="currentDataSource.alias" class="flex gap-x-2">
            <h3 class="font-medium text-gray-600 mb-2">Alias</h3>
            <p class="font-mono w-fit text-sm bg-gray-100 px-2 py-1 rounded">{{ currentDataSource.alias }}</p>
          </div>
          
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <Calendar class="w-4 h-4" />
            <span>Created {{ new Date(currentDataSource.created_at).toLocaleDateString() }}</span>
            <span>•</span>
            <span>Updated {{ new Date(currentDataSource.updated_at).toLocaleDateString() }}</span>
          </div>
          
        </CardContent>
      </Card>

      <!-- Configuration Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Credentials</CardTitle>
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
        <CardContent class="space-y-6">
          <!-- Action Buttons -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button 
              variant="outline" 
              class="justify-start" 
              @click="testConnection"
              :disabled="isLoadingConnection"
            >
              <Loader2 v-if="isLoadingConnection" class="w-4 h-4 mr-2 animate-spin" />
              <Activity v-else class="w-4 h-4 mr-2" />
              Test Connection
            </Button>
            <Button 
              variant="outline" 
              class="justify-start" 
              @click="viewSchema"
              :disabled="isLoadingSchema"
            >
              <Loader2 v-if="isLoadingSchema" class="w-4 h-4 mr-2 animate-spin" />
              <Settings v-else class="w-4 h-4 mr-2" />
              View Schema
            </Button>
          </div>

          <!-- Connection Test Result -->
          <div v-if="connectionTestResult.status" class="border rounded-lg p-4 space-y-2">
            <div class="flex items-center gap-2">
              <CheckCircle2 v-if="connectionTestResult.status === 'success'" class="w-5 h-5 text-green-600" />
              <XCircle v-else class="w-5 h-5 text-red-600" />
              <h3 class="font-semibold">Connection Test Result</h3>
              <span v-if="connectionTestResult.timestamp" class="text-xs text-muted-foreground ml-auto">
                {{ connectionTestResult.timestamp.toLocaleTimeString() }}
              </span>
            </div>
            <p :class="[
              'text-sm',
              connectionTestResult.status === 'success' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'
            ]">
              {{ connectionTestResult.message }}
            </p>
          </div>

          <!-- Schema Result -->
          <SourceSchemaViewer v-if="schemaResult" :schema="schemaResult" :data-source-id="currentDataSource?.id" />
        </CardContent>
      </Card>
    </div>

    <!-- Not Found -->
    <div v-else class="text-center py-8">
      <p class="text-gray-500">Data source not found</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog :open="showDeleteDialog" @update:open="(val) => !val && handleCancelDelete()">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle class="flex items-center gap-2">
            <AlertTriangle class="w-5 h-5 text-destructive" />
            Delete Data Source
          </AlertDialogTitle>
          <AlertDialogDescription class="space-y-2">
            <p>
              Are you sure you want to delete the data source "<strong>{{ currentDataSource?.name }}</strong>"?
            </p>
            <p class="text-sm text-muted-foreground">
              This action cannot be undone.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <Button
            variant="destructive"
            @click="() => handleDelete(false)"
            :disabled="isDeleting"
          >
            {{ isDeleting ? 'Deleting...' : 'Delete Data Source' }}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <!-- Cascade Delete Confirmation Dialog -->
    <AlertDialog :open="showCascadeDialog" @update:open="(val) => !val && handleCancelDelete()">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle class="flex items-center gap-2">
            <AlertTriangle class="w-5 h-5 text-destructive" />
            Warning
          </AlertDialogTitle>
          <AlertDialogDescription class="space-y-3">
            <p>
              The data source "<strong>{{ currentDataSource?.name }}</strong>" cannot be deleted because other entities depend on it.
            </p>

            <div
              v-if="dependenciesToDelete"
              class="p-3 bg-destructive/10 border border-destructive/30 rounded-md"
            >
              <p class="text-destructive font-medium mb-2">
                ⚠️ The following will be permanently deleted:
              </p>
              <ul class="text-sm text-destructive space-y-1">
                <li class="font-semibold">
                  {{ dependenciesToDelete.dependencies.metrics.length }} metric{{ dependenciesToDelete.dependencies.metrics.length !== 1 ? 's' : '' }}:
                </li>
                <li
                  v-for="metric in dependenciesToDelete.dependencies.metrics"
                  :key="metric.id"
                  class="ml-4 list-disc list-inside"
                >
                  {{ metric.name }}{{ metric.alias ? ` (${metric.alias})` : '' }}
                  <span v-if="metric.version_count > 0" class="text-xs">
                    - {{ metric.version_count }} version{{ metric.version_count !== 1 ? 's' : '' }}
                  </span>
                </li>
              </ul>
            </div>

            <p class="text-sm font-medium">
              Do you want to delete the data source and all its dependent metrics?
            </p>

            <p class="text-sm text-muted-foreground">
              This action cannot be undone.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="handleCancelDelete">Cancel</AlertDialogCancel>
          <Button
            variant="destructive"
            @click="handleCascadeDelete"
            :disabled="isDeleting"
          >
            {{ isDeleting ? 'Deleting...' : 'Delete All' }}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template> 