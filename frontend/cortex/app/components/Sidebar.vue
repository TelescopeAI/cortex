<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { useRouter } from 'vue-router';
import { computed, watch } from 'vue';
import type { Workspace, Environment } from '~/types';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuButton
} from '~/components/ui/sidebar';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuPortal
} from '~/components/ui/dropdown-menu';
import CreateWorkspaceDialog from '~/components/CreateWorkspaceDialog.vue';
import CreateEnvironmentDialog from '~/components/CreateEnvironmentDialog.vue';
import { ChevronDown, Check, Database, Target, Users } from 'lucide-vue-next';

const { workspaces, selectedWorkspaceId, selectWorkspace } = useWorkspaces();
const { environments, selectedEnvironmentId, selectEnvironment } = useEnvironments();
const router = useRouter();

function handleWorkspaceSelect(id: string) {
  selectWorkspace(id);
  router.push('/environments');
}

function handleEnvironmentSelect(id: string) {
  selectEnvironment(id);
}

// Computed values for display
const selectedWorkspace = computed(() => 
  workspaces.value?.find((w: Workspace) => w.id === selectedWorkspaceId.value)
);

const selectedEnvironment = computed(() => 
  environments.value?.find((e: Environment) => e.id === selectedEnvironmentId.value)
);

const displayText = computed(() => {
  const workspaceName = selectedWorkspace.value?.name || 'Select Workspace';
  const environmentName = selectedEnvironment.value?.name || 'Select Environment';
  return `${workspaceName} / ${environmentName}`;
});

const dropdownLabel = computed(() => {
  if (!selectedWorkspace.value && !selectedEnvironment.value) {
    return 'Select Workspace & Environment';
  } else if (!selectedWorkspace.value) {
    return 'Select Workspace';
  } else if (!selectedEnvironment.value) {
    return 'Select Environment';
  }
  return ''; // Both are selected, no label needed
});

// Redirect logic for unconfigured state - only redirect from home page
watch([selectedWorkspaceId, selectedEnvironmentId], ([workspaceId, environmentId]) => {
  // Only redirect if we're on the home page and don't have both configured
  if (router.currentRoute.value.path === '/' && (!workspaceId || !environmentId)) {
    router.push('/config/workspaces');
  } else if (router.currentRoute.value.path === '/config/workspaces' && workspaceId && environmentId) {
    // Both are configured, redirect to home
    router.push('/');
  }
}, { immediate: true });
</script>

<template>
  <Sidebar class="w-64">
    <SidebarHeader class="border-b p-4">
      <h2 class="text-lg font-semibold">Cortex</h2>
    </SidebarHeader>
    
    <SidebarContent class="p-4">
      <!-- Workspace & Environment Dropdown -->
      <div class="mb-4">
        <DropdownMenu>
          <DropdownMenuTrigger class="w-full text-left p-3 border rounded-md hover:bg-gray-50 flex items-center justify-between">
            <div class="flex flex-col items-start">
              <span class="text-sm font-medium">{{ displayText }}</span>
            </div>
            <ChevronDown class="w-4 h-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-56">
            <DropdownMenuLabel v-if="dropdownLabel">{{ dropdownLabel }}</DropdownMenuLabel>
            <DropdownMenuSeparator v-if="dropdownLabel" />
            
            <!-- Workspace Items -->
            <DropdownMenuItem 
              v-for="ws in workspaces" 
              :key="ws.id" 
              @click="handleWorkspaceSelect(ws.id)"
            >
              <span>{{ ws.name }}</span>
              <Check v-if="ws.id === selectedWorkspaceId" class="w-4 h-4 text-blue-600" />
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            
            <!-- Create Workspace Button -->
            <div class="px-2 py-1">
              <CreateWorkspaceDialog />
            </div>
            
            <DropdownMenuSeparator />
            
            <!-- Environment Submenu - Only show if workspace is selected -->
            <DropdownMenuSub v-if="selectedWorkspaceId">
              <DropdownMenuSubTrigger>
                <span>Environments</span>
              </DropdownMenuSubTrigger>
              <DropdownMenuPortal>
                <DropdownMenuSubContent>
                  <DropdownMenuItem 
                    v-for="env in environments" 
                    :key="env.id" 
                    @click="handleEnvironmentSelect(env.id)"
                  >
                    <span>{{ env.name }}</span>
                    <Check v-if="env.id === selectedEnvironmentId" class="w-4 h-4 text-blue-600" />
                  </DropdownMenuItem>
                  
                  <DropdownMenuSeparator />
                  
                  <!-- Create Environment Button -->
                  <div class="px-2 py-1">
                    <CreateEnvironmentDialog />
                  </div>
                </DropdownMenuSubContent>
              </DropdownMenuPortal>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <!-- Navigation -->
      <SidebarMenu>
        <SidebarMenuButton @click="router.push('/workspaces')">
          Workspaces
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/environments')">
          Environments
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/data/sources')">
          <Database class="w-4 h-4 mr-2" />
          Data Sources
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/metrics')">
          <Target class="w-4 h-4 mr-2" />
          Metrics
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/consumers')">
          <Users class="w-4 h-4 mr-2" />
          Consumers
        </SidebarMenuButton>
      </SidebarMenu>
    </SidebarContent>
  </Sidebar>
</template> 