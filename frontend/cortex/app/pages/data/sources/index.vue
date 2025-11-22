<script setup lang="ts">
import { useDataSources } from '~/composables/useDataSources';
import { useRouter } from 'vue-router';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { watch, onMounted } from 'vue';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import { Skeleton } from '~/components/ui/skeleton';
import CreateDataSourceDialog from '~/components/CreateDataSourceDialog.vue';
import { Calendar, Database, Globe, FileText, Settings, RefreshCw } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';

const { dataSources, loading, error, selectedEnvironmentId, refresh } = useDataSources();
const { selectedWorkspaceId } = useWorkspaces();
const { selectedEnvironmentId: envId } = useEnvironments();
const router = useRouter();

// Load data sources when component mounts
onMounted(() => {
  if (selectedEnvironmentId.value) {
    refresh();
  }
});

// Watch for environment changes and load data sources
watch(selectedEnvironmentId, (newEnvironmentId) => {
  if (newEnvironmentId) {
    refresh();
  }
}, { immediate: true });

// Handle data source creation event
function handleDataSourceCreated() {
  refresh();
}

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
</script>

<template>
  <div class="p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Data Sources</h1>
      <div class="flex items-center gap-2">
            <CreateDataSourceDialog 
              v-if="selectedEnvironmentId" 
              @data-source-created="handleDataSourceCreated"
            />
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 lg:grid-cols-3 space-4">
      <Card v-for="i in 6" :key="i" class="p-6 m-3">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <!-- Icon and Title -->
            <div class="flex items-center gap-2 mb-3">
              <Skeleton class="h-6 w-24 rounded-full" />
              <Skeleton class="h-6 w-full" />
            </div>
            
            <!-- Badges -->
            <div class="flex items-center gap-2 mb-3">
              <Skeleton class="h-6 w-full rounded-full" />
            </div>
            
            <!-- Description lines -->
            <div class="space-y-2 mb-3">
              <Skeleton class="h-4 w-full" />
              <Skeleton class="h-4 w-full" />
            </div>
            
            <!-- Date with icon -->
            <div class="flex items-center gap-2 text-sm">
              <Skeleton class="h-4 w-full" />
            </div>
          </div>
        </div>
      </Card>
    </div>
    
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">Error loading data sources</p>
    </div>
    
    <div v-else-if="!selectedWorkspaceId">
      <div class="text-center py-8">
        <Settings class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Workspace Selected</h3>
        <p class="text-gray-500 mb-4">Please select a workspace from the dropdown above to view data sources.</p>
        <p class="text-sm text-gray-400">You can also create a new workspace if needed.</p>
      </div>
    </div>
    
    <div v-else-if="!selectedEnvironmentId">
      <div class="text-center py-8">
        <Settings class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Environment Selected</h3>
        <p class="text-gray-500 mb-4">Please select an environment from the dropdown above to view data sources.</p>
        <p class="text-sm text-gray-400">You can also create a new environment if needed.</p>
      </div>
    </div>
    
    <div v-else-if="dataSources.length === 0">
      <div class="text-center py-8">
        <Database class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No data sources connected</h3>
        <p class="text-gray-500 mb-4">Get started by connecting your first data source.</p>
        <CreateDataSourceDialog @data-source-created="handleDataSourceCreated" />
      </div>
    </div>
    
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" :key="dataSources.length">
        <div v-for="dataSource in dataSources" :key="dataSource.id" class="bg-white rounded-lg shadow p-6">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-2">
                <component :is="getCatalogIcon(dataSource.source_catalog)" class="w-5 h-5 text-gray-500" />
                <h3 class="text-lg font-semibold text-gray-900">{{ dataSource.name }}</h3>
              </div>
              <div class="flex items-center gap-2 mb-2">
                <Badge :class="getCatalogColor(dataSource.source_catalog)">
                  {{ dataSource.source_catalog }}
                </Badge>
                <Badge variant="outline">
                  {{ dataSource.source_type }}
                </Badge>
              </div>
              <p v-if="dataSource.description" class="text-gray-600 mb-2">{{ dataSource.description }}</p>
              <div class="flex items-center gap-2 text-sm text-gray-500">
                <Calendar class="w-4 h-4" />
                <span>Created {{ new Date(dataSource.created_at).toLocaleDateString() }}</span>
              </div>
            </div>
            <Button variant="outline" size="sm" @click="router.push(`/data/sources/${dataSource.id}`)">
              View Details
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 