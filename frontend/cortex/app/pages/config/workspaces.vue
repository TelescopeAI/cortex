<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { useRouter } from 'vue-router';
import { computed } from 'vue';
import type { Workspace, Environment } from '~/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
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
import { ChevronDown, Check } from 'lucide-vue-next';

const { workspaces, selectedWorkspaceId, selectWorkspace, loading: workspacesLoading } = useWorkspaces();
const { environments, selectedEnvironmentId, selectEnvironment, loading: environmentsLoading } = useEnvironments();
const router = useRouter();

function handleWorkspaceSelect(id: string) {
  selectWorkspace(id);
}

function handleEnvironmentSelect(id: string) {
  selectEnvironment(id);
  // Redirect to home after both are configured
  router.push('/');
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
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-center">Configure Your Workspace</CardTitle>
      </CardHeader>
      <CardContent class="space-y-6">
        <div class="text-center text-gray-600 mb-6">
          <p>Please select your workspace and environment to get started.</p>
        </div>

        <!-- Workspace & Environment Dropdown -->
        <div>
          <DropdownMenu>
            <DropdownMenuTrigger class="w-full text-left p-4 border rounded-md hover:bg-gray-50 flex items-center justify-between">
              <div class="flex flex-col items-start">
                <span class="text-sm font-medium">{{ displayText }}</span>
              </div>
              <ChevronDown class="w-4 h-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent class="w-64">
              <DropdownMenuLabel v-if="dropdownLabel">{{ dropdownLabel }}</DropdownMenuLabel>
              <DropdownMenuSeparator v-if="dropdownLabel" />
              
              <!-- Loading State -->
              <div v-if="workspacesLoading" class="p-4 text-center text-gray-500">
                Loading workspaces...
              </div>
              
              <!-- Workspace Items -->
              <DropdownMenuItem 
                v-else
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
              
              <!-- Environment Submenu -->
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <span>Environments</span>
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    <div v-if="environmentsLoading" class="p-4 text-center text-gray-500">
                      Loading environments...
                    </div>
                    <DropdownMenuItem 
                      v-else
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

        <!-- Status -->
        <div class="text-center text-sm text-gray-500">
          <p v-if="!selectedWorkspaceId">Please select a workspace first</p>
          <p v-else-if="!selectedEnvironmentId">Now select an environment</p>
          <p v-else class="text-green-600">Configuration complete! Redirecting...</p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>