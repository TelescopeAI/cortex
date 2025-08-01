<script setup lang="ts">
import { useDataSources } from '~/composables/useDataSources';
import { useRouter } from 'vue-router';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import CreateDataSourceDialog from '~/components/CreateDataSourceDialog.vue';
import { Calendar, Database, Globe, FileText, Settings } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';

const { dataSources, loading, error, selectedEnvironmentId } = useDataSources();
const { selectedWorkspaceId } = useWorkspaces();
const { selectedEnvironmentId: envId } = useEnvironments();
const router = useRouter();

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
      <CreateDataSourceDialog v-if="selectedEnvironmentId" />
    </div>
    
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading data sources...</p>
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
        <h3 class="text-lg font-medium text-gray-900 mb-2">No data sources found</h3>
        <p class="text-gray-500 mb-4">Get started by creating your first data source.</p>
        <CreateDataSourceDialog />
      </div>
    </div>
    
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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