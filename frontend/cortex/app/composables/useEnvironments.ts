import { ref, computed, watch } from 'vue';
import { useStorage } from '@vueuse/core';
import type { Environment } from '~/types';

export function useEnvironments() {
  const { apiUrl } = useApi();

  // Persistent selections
  const selectedEnvironmentId = useStorage<string | null>('selectedEnvironmentId', null);
  const selectedWorkspaceId = useStorage<string | null>('selectedWorkspaceId', null);

  // Shared state across composable instances
  const data = useState<Environment[] | null>('environments:list', () => null);
  const loading = useState<boolean>('environments:loading', () => false);
  const error = useState<any>('environments:error', () => null);

  // Fetch environments for the current workspace
  async function fetchEnvironments() {
    if (!selectedWorkspaceId.value) {
      data.value = [];
      return;
    }
    loading.value = true;
    error.value = null;
    try {
      const result = await $fetch<Environment[]>(apiUrl('/api/v1/environments'), {
        query: { workspace_id: selectedWorkspaceId.value }
      });
      data.value = result || [];
    } catch (err: any) {
      console.error('Failed to fetch environments:', err);
      error.value = err;
      data.value = [];
    } finally {
      loading.value = false;
    }
  }

  // Guarded watcher: only refetch when the workspace id actually changes
  const lastWorkspaceId = useState<string | null>('environments:lastWorkspaceId', () => null);
  watch(selectedWorkspaceId, (newId) => {
    if (newId !== lastWorkspaceId.value) {
      lastWorkspaceId.value = newId;
      fetchEnvironments();
    }
  }, { immediate: true });

  function selectEnvironment(id: string) {
    selectedEnvironmentId.value = id;
  }

  async function createEnvironment(environment: { name: string; description?: string; workspace_id: string }) {
    const response = await $fetch<Environment>(apiUrl('/api/v1/environments'), {
      method: 'POST',
      body: environment,
    });
    // Refresh list after creation so UI updates everywhere
    await fetchEnvironments();
    return response;
  }

  async function getEnvironment(id: string) {
    try {
      const response = await $fetch<Environment>(apiUrl(`/api/v1/environments/${id}`));
      return response;
    } catch (err) {
      console.error('Failed to fetch environment:', err);
      return null;
    }
  }

  const environments = computed(() => data.value || []);

  return {
    environments,
    loading,
    error,
    refresh: fetchEnvironments,
    selectedEnvironmentId,
    selectEnvironment,
    createEnvironment,
    getEnvironment,
  };
} 