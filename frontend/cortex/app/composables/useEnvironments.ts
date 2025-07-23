import { useFetch } from 'nuxt/app';
import { computed, watch } from 'vue';
import { useStorage } from '@vueuse/core';
import type { Environment } from '~/types';

export function useEnvironments() {
  const { apiUrl } = useApi();
  
  // Persistent state for selected environment using localStorage
  const selectedEnvironmentId = useStorage<string | null>('selectedEnvironmentId', null);
  const selectedWorkspaceId = useStorage<string | null>('selectedWorkspaceId', null);

  // Fetch environments for the selected workspace
  const { data, pending, error, refresh, execute } = useFetch<Environment[]>(
    apiUrl('/api/v1/environments'),
    { 
      query: { workspace_id: selectedWorkspaceId },
      watch: false, // Disable automatic watching
      default: () => [],
      immediate: false // Don't execute immediately
    }
  );

  // Watch for workspace changes and execute fetch only when workspace is selected
  watch(selectedWorkspaceId, (newWorkspaceId) => {
    if (newWorkspaceId) {
      execute();
    } else {
      // Clear data when no workspace is selected
      data.value = [];
    }
  }, { immediate: true });

  // Helper to select an environment
  function selectEnvironment(id: string) {
    selectedEnvironmentId.value = id;
  }

  // Create a new environment
  async function createEnvironment(environment: { name: string; description?: string; workspace_id: string }) {
    const response = await $fetch<Environment>(apiUrl('/api/v1/environments'), {
      method: 'POST',
      body: environment,
    });
    
    // Refresh the environments list
    await refresh();
    
    return response;
  }

  // Return empty array if no workspace is selected
  const environments = computed(() => {
    if (!selectedWorkspaceId.value) return [];
    return data.value || [];
  });

  return {
    environments,
    loading: pending,
    error,
    refresh,
    selectedEnvironmentId,
    selectEnvironment,
    createEnvironment,
  };
} 