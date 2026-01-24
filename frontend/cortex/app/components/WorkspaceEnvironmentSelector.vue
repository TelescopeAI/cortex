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
  // Always select the workspace first
  selectWorkspace(workspaceId);

  // Ensure environments for this workspace are loaded
  await fetchEnvsForWorkspace(workspaceId);

  // Then select the environment
  selectEnvironment(id);
}

const selectedWorkspace = computed<Workspace | undefined>(() => {
  if (!Array.isArray(workspaces.value)) {
    return undefined;
  }
  const workspace = workspaces.value.find((w: Workspace) => w.id === selectedWorkspaceId.value);
  return workspace;
});

const selectedEnvironment = computed<Environment | undefined>(() => {
  if (!selectedEnvironmentId.value || !selectedWorkspaceId.value) {
    return undefined;
  }

  // Look in the cached environments for the selected workspace
  const workspaceEnvs = environmentsByWorkspace.value[selectedWorkspaceId.value];

  if (!Array.isArray(workspaceEnvs)) {
    return undefined;
  }

  const environment = workspaceEnvs.find((e: Environment) => e.id === selectedEnvironmentId.value);
  return environment;
});

const displayText = computed(() => {
  const workspaceName = selectedWorkspace.value?.name || 'Create Workspace';
  const environmentName = selectedEnvironment.value?.name || 'Select Environment';
  const text = `${workspaceName} / ${environmentName}`;
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
  // Check if we have workspaces
  if (!Array.isArray(workspaces.value) || workspaces.value.length === 0) {
    return;
  }

  let needsWorkspaceSelection = false;
  let needsEnvironmentSelection = false;
  let targetWorkspaceId = selectedWorkspaceId.value;

  // Validate selected workspace exists in current backend
  if (selectedWorkspaceId.value) {
    const workspaceExists = workspaces.value.some((w: Workspace) => w.id === selectedWorkspaceId.value);
    if (!workspaceExists) {
      needsWorkspaceSelection = true;
      needsEnvironmentSelection = true;
      targetWorkspaceId = null;
    } else {
      // Workspace exists, validate environment
      // Ensure environments for this workspace are loaded
      await fetchEnvsForWorkspace(selectedWorkspaceId.value);
      const workspaceEnvs = environmentsByWorkspace.value[selectedWorkspaceId.value];

      if (selectedEnvironmentId.value) {
        const environmentExists = Array.isArray(workspaceEnvs) &&
          workspaceEnvs.some((e: Environment) => e.id === selectedEnvironmentId.value);
        if (!environmentExists) {
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
    return;
  }

  // Select the first workspace if needed
  if (needsWorkspaceSelection) {
    const firstWorkspace = workspaces.value[0];
    if (!firstWorkspace) {
      return;
    }

    selectWorkspace(firstWorkspace.id);
    targetWorkspaceId = firstWorkspace.id;

    // Ensure environments for this workspace are loaded
    await fetchEnvsForWorkspace(firstWorkspace.id);
  }

  // Select the first environment if needed
  if (needsEnvironmentSelection && targetWorkspaceId) {
    const workspaceEnvs = environmentsByWorkspace.value[targetWorkspaceId];
    if (Array.isArray(workspaceEnvs) && workspaceEnvs.length > 0) {
      const firstEnvironment = workspaceEnvs[0];
      if (firstEnvironment) {
        selectEnvironment(firstEnvironment.id);
      }
    }
  }
}

// Watch for changes in selected workspace and environment
watch(selectedWorkspaceId, () => {
  // Workspace ID changed
}, { immediate: true });

watch(selectedEnvironmentId, () => {
  // Environment ID changed
}, { immediate: true });

// Fetch environments for all workspaces when workspaces are loaded
watch(workspaces, async (newWorkspaces) => {
  if (Array.isArray(newWorkspaces) && newWorkspaces.length > 0) {
    // Fetch environments for all workspaces in parallel
    await Promise.all(
      newWorkspaces.map((ws: Workspace) => fetchEnvsForWorkspace(ws.id))
    );

    // Auto-select first workspace and environment after environments are loaded
    await autoSelectFirstWorkspaceAndEnvironment();
  }
}, { immediate: true });

// Also watch environmentsByWorkspace to trigger auto-select when environments are loaded
watch(environmentsByWorkspace, async () => {
  await autoSelectFirstWorkspaceAndEnvironment();
}, { deep: true });

// Refresh workspaces on mount to ensure we have the latest data from the backend
// This is especially important when switching between different backends
onMounted(async () => {
  await refreshWorkspaces();
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
                    @update:model-value="(value: string) => handleEnvironmentSelect(value, ws.id)"
                  >
                    <DropdownMenuRadioItem
                      v-for="env in getEnvironmentsForWorkspace(ws.id)"
                      :key="env.id"
                      :value="env.id"
                      :class="[
                        env.id === selectedEnvironmentId ? 'bg-accent text-accent-foreground font-medium' : ''
                      ]"
                      @click="() => handleEnvironmentSelect(env.id, ws.id)"
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

