<script setup lang="ts">
import { useDataSources } from '~/composables/useDataSources';
import { useRouter, useRoute } from 'vue-router';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { watch, onMounted, ref, computed } from 'vue';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Badge } from '~/components/ui/badge';
import { Skeleton } from '~/components/ui/skeleton';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu';
import CreateDataSourceDialog from '~/components/CreateDataSourceDialog.vue';
import ExpandableSearch from '~/components/ExpandableSearch.vue';
import { Calendar, Database, Globe, FileText, Settings, MoreHorizontal, Eye, Edit, Trash2, FileSpreadsheet } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';

const searchQuery = ref('');

const { dataSources, loading, error, selectedEnvironmentId, refresh } = useDataSources();
const { selectedWorkspaceId } = useWorkspaces();
const { selectedEnvironmentId: envId } = useEnvironments();
const router = useRouter();
const route = useRoute();

// Dialog auto-open state from URL params
const dialogAutoOpen = ref(false);
const dialogInitialSourceType = ref<string>();
const dialogInitialFileId = ref<string>();
const dialogInitialFileName = ref<string>();

// Load data sources when component mounts
onMounted(() => {
  if (selectedEnvironmentId.value) {
    refresh();
  }

  // Check for URL query parameters to auto-open dialog
  if (route.query.create === 'spreadsheet' && route.query.file_id) {
    dialogAutoOpen.value = true;
    dialogInitialSourceType.value = 'spreadsheet';
    dialogInitialFileId.value = route.query.file_id as string;
    dialogInitialFileName.value = route.query.file_name as string;

    // Clear query params after reading them
    router.replace({ query: {} });
  }
});

// Watch for environment changes and load data sources
watch(selectedEnvironmentId, (newEnvironmentId) => {
  if (newEnvironmentId) {
    refresh();
  }
}, { immediate: true });

// Handle data source creation event
function handleDataSourceCreated(dataSource: import('~/types').DataSource) {
  // Redirect to the newly created data source page
  router.push(`/data/sources/${dataSource.id}`)
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
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'API':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'FILE':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  }
}

// Filtered data sources based on search
const filteredDataSources = computed(() => {
  if (!dataSources.value || dataSources.value.length === 0) return [];
  if (!searchQuery.value) return dataSources.value;
  
  const query = searchQuery.value.toLowerCase();
  return dataSources.value.filter(source => 
    source.name.toLowerCase().includes(query) ||
    source.description?.toLowerCase().includes(query) ||
    source.source_type.toLowerCase().includes(query)
  );
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-5xl font-bold tracking-tight">Data Sources</h1>
      </div>
      
      <div class="flex items-center gap-4">
        <!-- Search -->
        <ExpandableSearch
          v-model="searchQuery"
          :placeholder="['Search data sources...', 'Search by name...', 'Search by type...']"
          default-mode="minimal"
          full-width="350px"
          :expand-on-focus="true"
          expand-to="full"
        />
        
        <Button variant="outline" size="sm" @click="router.push('/data/sources/files')">
          <FileSpreadsheet class="w-4 h-4 mr-2" />
          Manage Files
        </Button>
        
        <CreateDataSourceDialog
          v-if="selectedEnvironmentId"
          :auto-open="dialogAutoOpen"
          :initial-source-type="dialogInitialSourceType"
          :initial-file-id="dialogInitialFileId"
          :initial-file-name="dialogInitialFileName"
          @data-source-created="handleDataSourceCreated"
        />
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card v-for="i in 6" :key="i" class="animate-pulse">
        <CardHeader>
          <div class="h-4 bg-muted rounded w-3/4"></div>
          <div class="h-3 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div class="h-3 bg-muted rounded"></div>
            <div class="h-3 bg-muted rounded w-2/3"></div>
          </div>
        </CardContent>
      </Card>
    </div>
    
    <div v-else-if="error" class="text-center py-12">
      <Database class="w-12 h-12 mx-auto text-destructive mb-4" />
      <h3 class="text-lg font-semibold mb-2">Error loading data sources</h3>
      <p class="text-muted-foreground mb-4">Something went wrong. Please try again.</p>
      <Button variant="outline" @click="refresh">
        Retry
      </Button>
    </div>
    
    <div v-else-if="!selectedWorkspaceId" class="text-center py-12">
      <Settings class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Workspace Selected</h3>
      <p class="text-muted-foreground mb-4">Please select a workspace from the dropdown above to view data sources.</p>
    </div>
    
    <div v-else-if="!selectedEnvironmentId" class="text-center py-12">
      <Settings class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Environment Selected</h3>
      <p class="text-muted-foreground mb-4">Please select an environment from the dropdown above to view data sources.</p>
    </div>
    
    <div v-else-if="dataSources.length === 0" class="text-center py-12">
      <Database class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No data sources connected</h3>
      <p class="text-muted-foreground mb-4">Get started by connecting your first data source.</p>
      <CreateDataSourceDialog
        :auto-open="dialogAutoOpen"
        :initial-source-type="dialogInitialSourceType"
        :initial-file-id="dialogInitialFileId"
        :initial-file-name="dialogInitialFileName"
        @data-source-created="handleDataSourceCreated"
      />
    </div>

    <div v-else-if="filteredDataSources.length === 0" class="text-center py-12">
      <Database class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No data sources match your search</h3>
      <p class="text-muted-foreground mb-4">Try adjusting your search criteria</p>
      <Button variant="outline" @click="searchQuery = ''">
        Clear Filters
      </Button>
    </div>
    
    <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card 
        v-for="dataSource in filteredDataSources" 
        :key="dataSource.id" 
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="router.push(`/data/sources/${dataSource.id}`)"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <CardTitle class="text-lg mb-1 flex items-center gap-2">
                <component :is="getCatalogIcon(dataSource.source_catalog)" class="w-5 h-5 text-muted-foreground" />
                {{ dataSource.name }}
              </CardTitle>
              <p v-if="dataSource.description" class="text-sm text-muted-foreground line-clamp-2">
                {{ dataSource.description }}
              </p>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger as-child @click.stop>
                <Button variant="ghost" size="icon" class="h-8 w-8">
                  <MoreHorizontal class="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click.stop="router.push(`/data/sources/${dataSource.id}`)">
                  <Eye class="w-4 h-4 mr-2" />
                  View
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop>
                  <Edit class="w-4 h-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop class="text-destructive">
                  <Trash2 class="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        
        <CardContent class="pt-0">
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Badge :class="getCatalogColor(dataSource.source_catalog)">
                {{ dataSource.source_catalog }}
              </Badge>
              <Badge variant="outline">
                {{ dataSource.source_type }}
              </Badge>
            </div>
            
            <div class="flex items-center gap-2 text-xs text-muted-foreground">
              <Calendar class="w-3 h-3" />
              <span>Created {{ new Date(dataSource.created_at).toLocaleDateString() }}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template> 