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

  // Cache environments per workspace
  const environmentsByWorkspace = useState<Record<string, Environment[]>>('environments:byWorkspace', () => ({}));

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
      const envs = result || [];
      data.value = envs;
      // Cache environments for this workspace
      environmentsByWorkspace.value[selectedWorkspaceId.value] = envs;
    } catch (err: any) {
      console.error('Failed to fetch environments:', err);
      error.value = err;
      data.value = [];
    } finally {
      loading.value = false;
    }
  }

  // Fetch environments for a specific workspace
  async function fetchEnvironmentsForWorkspace(workspaceId: string) {
    if (!workspaceId) {
      return [];
    }
    try {
      const result = await $fetch<Environment[]>(apiUrl('/api/v1/environments'), {
        query: { workspace_id: workspaceId }
      });
      const envs = result || [];
      // Cache environments for this workspace
      environmentsByWorkspace.value[workspaceId] = envs;
      return envs;
    } catch (err: any) {
      console.error(`Failed to fetch environments for workspace ${workspaceId}:`, err);
      return [];
    }
  }

  // Get environments for a specific workspace (from cache or fetch if needed)
  async function getEnvironmentsForWorkspace(workspaceId: string) {
    if (!workspaceId) {
      return [];
    }
    // Return from cache if available
    if (environmentsByWorkspace.value[workspaceId]) {
      return environmentsByWorkspace.value[workspaceId];
    }
    // Otherwise fetch
    return await fetchEnvironmentsForWorkspace(workspaceId);
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
    // Also refresh the cache for this workspace
    await fetchEnvironmentsForWorkspace(environment.workspace_id);
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
    fetchEnvironmentsForWorkspace,
    getEnvironmentsForWorkspace,
    environmentsByWorkspace,
  };
} 