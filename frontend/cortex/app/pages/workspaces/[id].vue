<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useApi } from '~/composables/useApi';
import type { Workspace } from '~/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { ArrowLeft, Calendar, Edit, Trash2 } from 'lucide-vue-next';
import EditWorkspaceDialog from '~/components/EditWorkspaceDialog.vue';
import { toast } from 'vue-sonner';

const route = useRoute();
const router = useRouter();
const { apiUrl } = useApi();
const { workspaces } = useWorkspaces();

// Fetch specific workspace data
const { data: workspace, pending, error, refresh } = useFetch<Workspace>(
  () => apiUrl(`/api/v1/workspaces/${route.params.id}`),
  { default: () => undefined }
);

// Use workspace from list if available, otherwise use fetched data
const currentWorkspace = computed<Workspace | undefined>(() => {
  // Always prioritize the fetched workspace if it exists
  if (workspace.value) {
    return workspace.value;
  }
  // Fall back to the list data if fetched data is not available
  return workspaces.value?.find((ws) => ws.id === route.params.id);
});

function goBack() {
  router.push('/workspaces');
}

async function handleWorkspaceUpdated(updatedWorkspace: Workspace) {
  // Directly update the fetched workspace with the API response
  if (workspace.value) {
    workspace.value = updatedWorkspace;
  }
  
  toast.success('Workspace updated successfully');
}

async function handleDelete() {
  if (!currentWorkspace.value) return;
  
  if (!confirm('Are you sure you want to delete this workspace? This action cannot be undone.')) {
    return;
  }
  
  try {
    await $fetch(apiUrl(`/api/v1/workspaces/${currentWorkspace.value.id}`), {
      method: 'DELETE'
    });
    
    toast.success('Workspace deleted successfully');
    await refresh();
    router.push('/workspaces');
  } catch (error: any) {
    console.error('Error deleting workspace:', error);
    toast.error(error?.data?.detail || 'Failed to delete workspace');
  }
}
</script>

<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <Button variant="outline" size="sm" @click="goBack">
          <ArrowLeft class="w-4 h-4 mr-2" />
          Back to Workspaces
        </Button>
        <h1 class="text-2xl font-bold">Workspace Details</h1>
      </div>
      <div class="flex gap-2">
        <EditWorkspaceDialog 
          v-if="currentWorkspace" 
          :workspace="currentWorkspace" 
          @updated="handleWorkspaceUpdated"
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
      <p class="mt-2 text-gray-600">Loading workspace details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">Error loading workspace details</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>

    <!-- Workspace Details -->
    <div v-else-if="currentWorkspace" class="space-y-6">
      <!-- Main Info Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-xl">{{ currentWorkspace.name }}</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div v-if="currentWorkspace.description">
            <h3 class="font-medium text-gray-900 mb-2">Description</h3>
            <p class="text-gray-600">{{ currentWorkspace.description }}</p>
          </div>
          
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <Calendar class="w-4 h-4" />
            <span>Created {{ new Date(currentWorkspace.created_at).toLocaleDateString() }}</span>
            <span>•</span>
            <span>Updated {{ new Date(currentWorkspace.updated_at).toLocaleDateString() }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Workspace ID Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Workspace Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div>
              <span class="font-medium text-gray-700">Workspace ID:</span>
              <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{{ currentWorkspace.id }}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Not Found -->
    <div v-else class="text-center py-8">
      <p class="text-gray-500">Workspace not found</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>
  </div>
</template> 