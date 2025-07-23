import { useFetch } from 'nuxt/app';
import { useStorage } from '@vueuse/core';
import type { Workspace } from '~/types';

export function useWorkspaces() {
  const { apiUrl } = useApi();
  
  // Persistent state for selected workspace using localStorage
  const selectedWorkspaceId = useStorage<string | null>('selectedWorkspaceId', null);

  // Fetch all workspaces - adjust the URL to match your backend
  const { data, pending, error, refresh } = useFetch<Workspace[]>(apiUrl('/api/v1/workspaces'));

  // Helper to select a workspace
  function selectWorkspace(id: string) {
    selectedWorkspaceId.value = id;
  }

  // Create a new workspace
  async function createWorkspace(workspace: { name: string; description?: string }) {
    const response = await $fetch<Workspace>(apiUrl('/api/v1/workspaces'), {
      method: 'POST',
      body: workspace,
    });
    
    // Refresh the workspaces list
    await refresh();
    
    return response;
  }

  return {
    workspaces: data,
    loading: pending,
    error,
    refresh,
    selectedWorkspaceId,
    selectWorkspace,
    createWorkspace,
  };
} 