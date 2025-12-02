<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { useRouter } from 'vue-router';
import { computed, watch, onMounted } from 'vue';
import type { Workspace, Environment } from '~/types';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem
} from '~/components/ui/dropdown-menu';
import CreateWorkspaceDialog from '~/components/CreateWorkspaceDialog.vue';
import CreateEnvironmentDialog from '~/components/CreateEnvironmentDialog.vue';
import { ChevronDown, Plus } from 'lucide-vue-next';

const { workspaces, selectedWorkspaceId, selectWorkspace, refresh: refreshWorkspaces } = useWorkspaces();
const { 
  environments, 
  selectedEnvironmentId, 
  selectEnvironment,
  getEnvironmentsForWorkspace: fetchEnvsForWorkspace,
  environmentsByWorkspace
} = useEnvironments();
const router = useRouter();

function handleWorkspaceSelect(id: string) {
  selectWorkspace(id);
  router.push('/environments');
}

async function handleEnvironmentSelect(id: string, workspaceId: string) {
  console.log('[WorkspaceEnvironmentSelector] handleEnvironmentSelect called:', { id, workspaceId });
  console.log('[WorkspaceEnvironmentSelector] Current state before selection:', {
    currentWorkspaceId: selectedWorkspaceId.value,
    currentEnvironmentId: selectedEnvironmentId.value,
    environmentsByWorkspace: environmentsByWorkspace.value
  });
  
  // Always select the workspace first
  console.log('[WorkspaceEnvironmentSelector] Selecting workspace:', workspaceId);
  selectWorkspace(workspaceId);
  console.log('[WorkspaceEnvironmentSelector] Workspace selected, new value:', selectedWorkspaceId.value);
  
  // Ensure environments for this workspace are loaded
  console.log('[WorkspaceEnvironmentSelector] Fetching environments for workspace:', workspaceId);
  const envs = await fetchEnvsForWorkspace(workspaceId);
  console.log('[WorkspaceEnvironmentSelector] Environments fetched:', envs);
  console.log('[WorkspaceEnvironmentSelector] Updated environmentsByWorkspace:', environmentsByWorkspace.value);
  
  // Then select the environment
  console.log('[WorkspaceEnvironmentSelector] Selecting environment:', id);
  selectEnvironment(id);
  console.log('[WorkspaceEnvironmentSelector] Environment selected, new value:', selectedEnvironmentId.value);
  console.log('[WorkspaceEnvironmentSelector] Final state:', {
    selectedWorkspaceId: selectedWorkspaceId.value,
    selectedEnvironmentId: selectedEnvironmentId.value,
    selectedWorkspace: selectedWorkspace.value,
    selectedEnvironment: selectedEnvironment.value
  });
}

const selectedWorkspace = computed<Workspace | undefined>(() => {
  if (!Array.isArray(workspaces.value)) {
    console.log('[WorkspaceEnvironmentSelector] selectedWorkspace: workspaces is not an array');
    return undefined;
  }
  const workspace = workspaces.value.find((w: Workspace) => w.id === selectedWorkspaceId.value);
  console.log('[WorkspaceEnvironmentSelector] selectedWorkspace computed:', {
    selectedWorkspaceId: selectedWorkspaceId.value,
    workspace: workspace?.name || 'not found',
    allWorkspaces: workspaces.value.map(w => ({ id: w.id, name: w.name }))
  });
  return workspace;
});

const selectedEnvironment = computed<Environment | undefined>(() => {
  console.log('[WorkspaceEnvironmentSelector] selectedEnvironment computed - inputs:', {
    selectedEnvironmentId: selectedEnvironmentId.value,
    selectedWorkspaceId: selectedWorkspaceId.value,
    environmentsByWorkspaceKeys: Object.keys(environmentsByWorkspace.value)
  });
  
  if (!selectedEnvironmentId.value || !selectedWorkspaceId.value) {
    console.log('[WorkspaceEnvironmentSelector] selectedEnvironment: missing id or workspace id');
    return undefined;
  }
  
  // Look in the cached environments for the selected workspace
  const workspaceEnvs = environmentsByWorkspace.value[selectedWorkspaceId.value];
  console.log('[WorkspaceEnvironmentSelector] selectedEnvironment - workspaceEnvs:', {
    workspaceId: selectedWorkspaceId.value,
    envsCount: Array.isArray(workspaceEnvs) ? workspaceEnvs.length : 'not an array',
    envs: Array.isArray(workspaceEnvs) ? workspaceEnvs.map(e => ({ id: e.id, name: e.name })) : null
  });
  
  if (!Array.isArray(workspaceEnvs)) {
    console.log('[WorkspaceEnvironmentSelector] selectedEnvironment: workspaceEnvs is not an array');
    return undefined;
  }
  
  const environment = workspaceEnvs.find((e: Environment) => e.id === selectedEnvironmentId.value);
  console.log('[WorkspaceEnvironmentSelector] selectedEnvironment computed result:', {
    found: environment ? environment.name : 'not found',
    environment
  });
  return environment;
});

const displayText = computed(() => {
  const workspaceName = selectedWorkspace.value?.name || 'Create Workspace';
  const environmentName = selectedEnvironment.value?.name || 'Select Environment';
  const text = `${workspaceName} / ${environmentName}`;
  console.log('[WorkspaceEnvironmentSelector] displayText computed:', {
    workspaceName,
    environmentName,
    displayText: text,
    selectedWorkspaceId: selectedWorkspaceId.value,
    selectedEnvironmentId: selectedEnvironmentId.value
  });
  return text;
});

const hasWorkspaces = computed(() => Array.isArray(workspaces.value) && workspaces.value.length > 0);

// Get environments for a specific workspace from cache
function getEnvironmentsForWorkspace(workspaceId: string): Environment[] {
  if (!workspaceId) return [];
  return environmentsByWorkspace.value[workspaceId] || [];
}

// Auto-select first workspace and first environment if they exist and nothing is selected
// Also validates and resets selections if they don't exist in the current backend
async function autoSelectFirstWorkspaceAndEnvironment() {
  console.log('[WorkspaceEnvironmentSelector] autoSelectFirstWorkspaceAndEnvironment called');
  console.log('[WorkspaceEnvironmentSelector] Current state:', {
    workspacesCount: Array.isArray(workspaces.value) ? workspaces.value.length : 0,
    selectedWorkspaceId: selectedWorkspaceId.value,
    selectedEnvironmentId: selectedEnvironmentId.value,
    environmentsByWorkspace: environmentsByWorkspace.value
  });

  // Check if we have workspaces
  if (!Array.isArray(workspaces.value) || workspaces.value.length === 0) {
    console.log('[WorkspaceEnvironmentSelector] No workspaces available for auto-select');
    return;
  }

  let needsWorkspaceSelection = false;
  let needsEnvironmentSelection = false;
  let targetWorkspaceId = selectedWorkspaceId.value;

  // Validate selected workspace exists in current backend
  if (selectedWorkspaceId.value) {
    const workspaceExists = workspaces.value.some((w: Workspace) => w.id === selectedWorkspaceId.value);
    if (!workspaceExists) {
      console.log('[WorkspaceEnvironmentSelector] Selected workspace does not exist in current backend, will reset');
      needsWorkspaceSelection = true;
      needsEnvironmentSelection = true;
      targetWorkspaceId = null;
    } else {
      // Workspace exists, validate environment
      // Ensure environments for this workspace are loaded
      const envs = await fetchEnvsForWorkspace(selectedWorkspaceId.value);
      const workspaceEnvs = environmentsByWorkspace.value[selectedWorkspaceId.value];
      
      if (selectedEnvironmentId.value) {
        const environmentExists = Array.isArray(workspaceEnvs) && 
          workspaceEnvs.some((e: Environment) => e.id === selectedEnvironmentId.value);
        if (!environmentExists) {
          console.log('[WorkspaceEnvironmentSelector] Selected environment does not exist in current backend, will reset');
          needsEnvironmentSelection = true;
        }
      } else {
        // No environment selected
        needsEnvironmentSelection = true;
      }
    }
  } else {
    // No workspace selected
    needsWorkspaceSelection = true;
    needsEnvironmentSelection = true;
  }

  // If nothing needs to be changed and we have valid selections, return early
  if (!needsWorkspaceSelection && !needsEnvironmentSelection) {
    console.log('[WorkspaceEnvironmentSelector] Current selections are valid, no changes needed');
    return;
  }

  // Select the first workspace if needed
  if (needsWorkspaceSelection) {
    const firstWorkspace = workspaces.value[0];
    if (!firstWorkspace) {
      console.log('[WorkspaceEnvironmentSelector] First workspace is undefined');
      return;
    }

    console.log('[WorkspaceEnvironmentSelector] Auto-selecting first workspace:', firstWorkspace.name);
    selectWorkspace(firstWorkspace.id);
    targetWorkspaceId = firstWorkspace.id;

    // Ensure environments for this workspace are loaded
    console.log('[WorkspaceEnvironmentSelector] Fetching environments for first workspace:', firstWorkspace.id);
    await fetchEnvsForWorkspace(firstWorkspace.id);
  }

  // Select the first environment if needed
  if (needsEnvironmentSelection && targetWorkspaceId) {
    const workspaceEnvs = environmentsByWorkspace.value[targetWorkspaceId];
    if (Array.isArray(workspaceEnvs) && workspaceEnvs.length > 0) {
      const firstEnvironment = workspaceEnvs[0];
      if (firstEnvironment) {
        console.log('[WorkspaceEnvironmentSelector] Auto-selecting first environment:', firstEnvironment.name);
        selectEnvironment(firstEnvironment.id);
        console.log('[WorkspaceEnvironmentSelector] Auto-selection complete:', {
          workspaceId: selectedWorkspaceId.value,
          environmentId: selectedEnvironmentId.value
        });
      } else {
        console.log('[WorkspaceEnvironmentSelector] First environment is undefined');
      }
    } else {
      console.log('[WorkspaceEnvironmentSelector] No environments available for auto-select in workspace');
    }
  }
}

// Watch for changes in selected workspace and environment
watch(selectedWorkspaceId, (newId, oldId) => {
  console.log('[WorkspaceEnvironmentSelector] selectedWorkspaceId changed:', { oldId, newId });
}, { immediate: true });

watch(selectedEnvironmentId, (newId, oldId) => {
  console.log('[WorkspaceEnvironmentSelector] selectedEnvironmentId changed:', { oldId, newId });
}, { immediate: true });

// Fetch environments for all workspaces when workspaces are loaded
watch(workspaces, async (newWorkspaces) => {
  console.log('[WorkspaceEnvironmentSelector] workspaces changed:', {
    count: Array.isArray(newWorkspaces) ? newWorkspaces.length : 0,
    workspaces: Array.isArray(newWorkspaces) ? newWorkspaces.map(w => ({ id: w.id, name: w.name })) : null
  });
  if (Array.isArray(newWorkspaces) && newWorkspaces.length > 0) {
    // Fetch environments for all workspaces in parallel
    console.log('[WorkspaceEnvironmentSelector] Fetching environments for all workspaces...');
    await Promise.all(
      newWorkspaces.map((ws: Workspace) => fetchEnvsForWorkspace(ws.id))
    );
    console.log('[WorkspaceEnvironmentSelector] All environments fetched:', environmentsByWorkspace.value);
    
    // Auto-select first workspace and environment after environments are loaded
    await autoSelectFirstWorkspaceAndEnvironment();
  }
}, { immediate: true });

// Also watch environmentsByWorkspace to trigger auto-select when environments are loaded
watch(environmentsByWorkspace, async () => {
  console.log('[WorkspaceEnvironmentSelector] environmentsByWorkspace changed');
  await autoSelectFirstWorkspaceAndEnvironment();
}, { deep: true });

// Refresh workspaces on mount to ensure we have the latest data from the backend
// This is especially important when switching between different backends
onMounted(async () => {
  console.log('[WorkspaceEnvironmentSelector] Component mounted, refreshing workspaces...');
  await refreshWorkspaces();
  console.log('[WorkspaceEnvironmentSelector] Workspaces refreshed:', workspaces.value);
});
</script>

<template>
  <div class="mb-4">
    <!-- No Workspace State -->
    <CreateWorkspaceDialog v-if="!hasWorkspaces">
      <template #trigger>
        <button class="w-full text-left p-3 border border-sidebar-border rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex items-center justify-between transition-colors group">
          <div class="flex flex-col items-start">
            <span class="text-sm font-medium text-muted-foreground">Create a Workspace</span>
          </div>
          <Plus class="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
        </button>
      </template>
    </CreateWorkspaceDialog>

    <!-- With Workspace State -->
    <DropdownMenu v-else>
      <DropdownMenuTrigger class="w-full text-left p-3 border border-sidebar-border rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex items-center justify-between transition-colors">
        <div class="flex flex-col items-start">
          <span class="text-sm font-medium">{{ displayText }}</span>
        </div>
        <ChevronDown class="w-4 h-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent class="w-56">
        <!-- Workspace Items with Environment Submenus -->
        <template v-if="Array.isArray(workspaces)">
          <DropdownMenuSub v-for="ws in workspaces" :key="ws.id">
            <DropdownMenuSubTrigger :class="[
              'cursor-pointer',
              ws.id === selectedWorkspaceId ? 'bg-accent text-accent-foreground font-medium' : ''
            ]">
              <span>{{ ws.name }}</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <!-- Environments for this Workspace -->
                <template v-if="getEnvironmentsForWorkspace(ws.id).length > 0">
                  <DropdownMenuRadioGroup 
                    :model-value="selectedEnvironmentId || undefined" 
                    @update:model-value="(value: string) => {
                      console.log('[WorkspaceEnvironmentSelector] RadioGroup update:model-value triggered:', { value, workspaceId: ws.id, workspaceName: ws.name });
                      handleEnvironmentSelect(value, ws.id);
                    }"
                  >
                    <DropdownMenuRadioItem 
                      v-for="env in getEnvironmentsForWorkspace(ws.id)" 
                      :key="env.id" 
                      :value="env.id"
                      :class="[
                        env.id === selectedEnvironmentId ? 'bg-accent text-accent-foreground font-medium' : ''
                      ]"
                      @click="() => {
                        console.log('[WorkspaceEnvironmentSelector] RadioItem clicked:', { envId: env.id, envName: env.name, workspaceId: ws.id, workspaceName: ws.name });
                        handleEnvironmentSelect(env.id, ws.id);
                      }"
                    >
                      <span>{{ env.name }}</span>
                    </DropdownMenuRadioItem>
                  </DropdownMenuRadioGroup>
                  
                  <DropdownMenuSeparator />
                </template>

                <!-- Create Environment Button -->
                <CreateEnvironmentDialog :workspace-id="ws.id">
                  <template #trigger>
                    <div class="px-2 py-1.5 text-sm rounded-md hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2">
                      <Plus class="w-4 h-4" />
                      <span>Add Environment</span>
                    </div>
                  </template>
                </CreateEnvironmentDialog>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>
        </template>

        <DropdownMenuSeparator />

        <!-- Create Workspace Button -->
        <CreateWorkspaceDialog>
          <template #trigger>
            <div class="px-2 py-1.5 text-sm rounded-md hover:bg-accent hover:text-accent-foreground cursor-pointer flex items-center gap-2">
              <Plus class="w-4 h-4" />
              <span>Add Workspace</span>
            </div>
          </template>
        </CreateWorkspaceDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>

