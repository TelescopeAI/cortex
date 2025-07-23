<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useEnvironments } from '~/composables/useEnvironments';
import { useApi } from '~/composables/useApi';
import type { Environment } from '~/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { ArrowLeft, Calendar, Edit, Trash2, Database, Users } from 'lucide-vue-next';
import EditEnvironmentDialog from '~/components/EditEnvironmentDialog.vue';
import { toast } from 'vue-sonner';

const route = useRoute();
const router = useRouter();
const { apiUrl } = useApi();
const { environments } = useEnvironments();

// Fetch specific environment data
const { data: environment, pending, error, refresh } = useFetch<Environment>(
  () => apiUrl(`/api/v1/environments/${route.params.id}`),
  { default: () => undefined }
);

// Use environment from list if available, otherwise use fetched data
const currentEnvironment = computed<Environment | undefined>(() => {
  // Always prioritize the fetched environment if it exists
  if (environment.value) {
    return environment.value;
  }
  // Fall back to the list data if fetched data is not available
  return environments.value?.find((env) => env.id === route.params.id);
});

function goBack() {
  router.push('/environments');
}

async function handleEnvironmentUpdated(updatedEnvironment: Environment) {
  // Directly update the fetched environment with the API response
  if (environment.value) {
    environment.value = updatedEnvironment;
  }
  
  toast.success('Environment updated successfully');
}

async function handleDelete() {
  if (!currentEnvironment.value) return;
  
  if (!confirm('Are you sure you want to delete this environment? This action cannot be undone.')) {
    return;
  }
  
  try {
    await $fetch(apiUrl(`/api/v1/environments/${currentEnvironment.value.id}`), {
      method: 'DELETE'
    });
    
    toast.success('Environment deleted successfully');
    await refresh();
    router.push('/environments');
  } catch (error: any) {
    console.error('Error deleting environment:', error);
    toast.error(error?.data?.detail || 'Failed to delete environment');
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
          Back to Environments
        </Button>
        <h1 class="text-2xl font-bold">Environment Details</h1>
      </div>
      <div class="flex gap-2">
        <EditEnvironmentDialog 
          v-if="currentEnvironment" 
          :environment="currentEnvironment" 
          @updated="handleEnvironmentUpdated"
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
      <p class="mt-2 text-gray-600">Loading environment details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-600">Error loading environment details</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>

    <!-- Environment Details -->
    <div v-else-if="currentEnvironment" class="space-y-6">
      <!-- Main Info Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-xl">{{ currentEnvironment.name }}</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div v-if="currentEnvironment.description">
            <h3 class="font-medium text-gray-900 mb-2">Description</h3>
            <p class="text-gray-600">{{ currentEnvironment.description }}</p>
          </div>
          
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <Calendar class="w-4 h-4" />
            <span>Created {{ new Date(currentEnvironment.created_at).toLocaleDateString() }}</span>
            <span>•</span>
            <span>Updated {{ new Date(currentEnvironment.updated_at).toLocaleDateString() }}</span>
          </div>
        </CardContent>
      </Card>

      <!-- Environment Information Card -->
      <Card>
        <CardHeader>
          <CardTitle class="text-lg">Environment Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div>
              <span class="font-medium text-gray-700">Environment ID:</span>
              <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{{ currentEnvironment.id }}</span>
            </div>
            <div>
              <span class="font-medium text-gray-700">Workspace ID:</span>
              <span class="font-mono text-sm bg-gray-100 px-2 py-1 rounded ml-2">{{ currentEnvironment.workspace_id }}</span>
            </div>
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
            <Button variant="outline" class="justify-start">
              <Database class="w-4 h-4 mr-2" />
              View Data Sources
            </Button>
            <Button variant="outline" class="justify-start">
              <Users class="w-4 h-4 mr-2" />
              View Consumers
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Not Found -->
    <div v-else class="text-center py-8">
      <p class="text-gray-500">Environment not found</p>
      <Button @click="goBack" class="mt-4">Go Back</Button>
    </div>
  </div>
</template> 