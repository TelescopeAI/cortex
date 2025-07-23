<script setup lang="ts">
import { useEnvironments } from '~/composables/useEnvironments';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useRouter } from 'vue-router';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import CreateEnvironmentDialog from '~/components/CreateEnvironmentDialog.vue';
import { Calendar } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';

const { environments, loading, error, selectEnvironment } = useEnvironments();
const { selectedWorkspaceId } = useWorkspaces();
const router = useRouter();

function handleSelect(id: string) {
  selectEnvironment(id);
}
</script>

<template>
  <div class="p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Environments</h1>
      <CreateEnvironmentDialog v-if="selectedWorkspaceId" />
    </div>
    
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
      <p class="mt-2 text-gray-600">Loading environments...</p>
    </div>
    
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">Error loading environments</p>
    </div>
    
    <div v-else-if="!selectedWorkspaceId">
      <div class="text-center py-8">
        <FolderOpen class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Workspace Selected</h3>
        <p class="text-gray-500 mb-4">Please select a workspace from the dropdown above to view its environments.</p>
        <p class="text-sm text-gray-400">You can also create a new workspace if needed.</p>
      </div>
    </div>
    
    <div v-else-if="environments.length === 0">
      <div class="text-center py-8">
        <FolderOpen class="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Environments Found</h3>
        <p class="text-gray-500 mb-4">This workspace doesn't have any environments yet.</p>
        <CreateEnvironmentDialog />
      </div>
    </div>
    
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="environment in environments" :key="environment.id" class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900">{{ environment.name }}</h3>
              <p v-if="environment.description" class="text-gray-600 mt-1">{{ environment.description }}</p>
              <div class="flex items-center gap-2 mt-2 text-sm text-gray-500">
                <Calendar class="w-4 h-4" />
                <span>Created {{ new Date(environment.created_at).toLocaleDateString() }}</span>
              </div>
            </div>
            <Button variant="outline" size="sm" @click="router.push(`/environments/${environment.id}`)">
              View Details
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 