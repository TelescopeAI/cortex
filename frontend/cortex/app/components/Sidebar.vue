<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import { useRouter } from 'vue-router';
import { computed, watch } from 'vue';
import { useDark } from '@vueuse/core';
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
import { ChevronDown, Check, Database, Target, Users, BarChart3, Zap } from 'lucide-vue-next';
import Logo from '~/components/Logo.vue';
import ThemeToggle from '~/components/ThemeToggle.vue';

const { workspaces, selectedWorkspaceId, selectWorkspace } = useWorkspaces();
const { environments, selectedEnvironmentId, selectEnvironment } = useEnvironments();
const router = useRouter();

// Configure useDark to properly handle system preferences and manual control
const isDark = useDark({
  valueDark: 'dark',
  valueLight: 'light',
  selector: 'html',
  attribute: 'class',
  storageKey: 'cortex-color-scheme'
})

// Watch for changes and ensure proper synchronization
watch(isDark, (newValue) => {
  // Ensure the DOM is updated when the reactive state changes
  if (typeof document !== 'undefined') {
    if (newValue) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
}, { immediate: true })

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
  <Sidebar class="w-64 bg-sidebar border-r border-sidebar-border">
    <SidebarHeader class="border-b border-sidebar-border p-4 flex flex-row items-center justify-between">
      <Logo />
      <div class="mt-1 flex items-center justify-center">
        <ThemeToggle />
      </div>
    </SidebarHeader>
    
    <SidebarContent class="p-4">
      <!-- Workspace & Environment Dropdown -->
      <div class="mb-4">
        <DropdownMenu>
          <DropdownMenuTrigger class="w-full text-left p-3 border border-sidebar-border rounded-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex items-center justify-between transition-colors">
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
              <Check v-if="ws.id === selectedWorkspaceId" class="w-4 h-4 text-sidebar-primary" />
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
                    <Check v-if="env.id === selectedEnvironmentId" class="w-4 h-4 text-sidebar-primary" />
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
        <SidebarMenuButton @click="router.push('/data/sources')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <Database class="w-4 h-4 mr-2" />
          Data Sources
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/metrics')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <Target class="w-4 h-4 mr-2" />
          Metrics
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/dashboards')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <BarChart3 class="w-4 h-4 mr-2" />
          Dashboards
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/pre-aggregations')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <Zap class="w-4 h-4 mr-2" />
          Pre-Aggregations
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/consumers')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <Users class="w-4 h-4 mr-2" />
          Consumers
        </SidebarMenuButton>
      </SidebarMenu>
    </SidebarContent>
  </Sidebar>
</template> 