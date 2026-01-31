<script setup lang="ts">
import { useDataSources } from '~/composables/useDataSources';
import { useRouter, useRoute } from 'vue-router';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { watch, onMounted, ref, computed } from 'vue';
import { Skeleton } from '~/components/ui/skeleton';
import CreateDataSourceDialog from '~/components/CreateDataSourceDialog.vue';
import DataSourceCard from '~/components/data-sources/DataSourceCard.vue';
import ExpandableSearch from '~/components/ExpandableSearch.vue';
import { Database, Settings, FileSpreadsheet, Upload } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '~/components/ui/empty';

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
        
        <Button variant="outline" size="sm"
                class="cursor-pointer" @click="router.push('/data/sources/files')">
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
    
    <Empty v-else-if="dataSources.length === 0">
      <EmptyContent>
        <EmptyMedia variant="icon">
          <Database />
        </EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>No data sources connected</EmptyTitle>
          <EmptyDescription>
            Get started by connecting your first data source or uploading a file.
          </EmptyDescription>
        </EmptyHeader>
        <div class="flex gap-3">
          <CreateDataSourceDialog
            v-if="selectedEnvironmentId"
            :auto-open="dialogAutoOpen"
            :initial-source-type="dialogInitialSourceType"
            :initial-file-id="dialogInitialFileId"
            :initial-file-name="dialogInitialFileName"
            @data-source-created="handleDataSourceCreated"
          />
          <Button variant="outline" size="sm" @click="router.push('/data/sources/files')">
            <Upload class="w-4 h-4 mr-2" />
            Upload File
          </Button>
        </div>
      </EmptyContent>
    </Empty>

    <Empty v-else-if="filteredDataSources.length === 0">
      <EmptyContent>
        <EmptyMedia variant="icon">
          <Database />
        </EmptyMedia>
        <EmptyHeader>
          <EmptyTitle>No results found</EmptyTitle>
          <EmptyDescription>
            No data sources match your search criteria. Try adjusting your filters.
          </EmptyDescription>
        </EmptyHeader>
      </EmptyContent>
    </Empty>

    <div v-else class="grid gap-6 grid-cols-1 lg:grid-cols-4">
      <DataSourceCard
        v-for="dataSource in filteredDataSources"
        :key="dataSource.id"
        :data-source="dataSource"
        @click="router.push(`/data/sources/${dataSource.id}`)"
      />
    </div>
  </div>
</template> 