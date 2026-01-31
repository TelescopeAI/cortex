<script setup lang="ts">
import { useRouter } from 'vue-router';
import { watch, ref, computed } from 'vue';
import { useDark } from '@vueuse/core';
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuButton
} from '~/components/ui/sidebar';
import { WarpBackground } from '~/components/ui/warp-background';
import { Database, Target, Users, BarChart3, Zap, Home } from 'lucide-vue-next';
import Logo from '~/components/Logo.vue';
import ThemeToggle from '~/components/ThemeToggle.vue';
import WorkspaceEnvironmentSelector from '~/components/WorkspaceEnvironmentSelector.vue';

const router = useRouter();
const { selectedWorkspaceId } = useWorkspaces();
const { selectedEnvironmentId } = useEnvironments();

// Track logo hover state
const isLogoHovered = ref(false)

const handleLogoHover = (hovered: boolean) => {
  isLogoHovered.value = hovered
}

// Configure useDark to properly handle system preferences and manual control
const isDark = useDark({
  valueDark: 'dark',
  valueLight: 'light',
  selector: 'html',
  attribute: 'class',
  storageKey: 'cortex-color-scheme'
})

const warpLightColor = '#ffffff'
const warpDarkColor = '#3b82f6'
const starColor = computed(() => isDark.value ? '#14203c' : '#b8d4fd2b')

const sidebarHeaderRef = ref<HTMLElement | null>(null)
const isSidebarHeaderHovered = useElementHover(sidebarHeaderRef)

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
  <ClientOnly>
  <Sidebar class="w-64">
    <SidebarHeader ref="sidebarHeaderRef" 
                  class="relative border-b p-4 md:h-20 flex flex-row
                         hover:drop-shadow-2xs
                         items-center justify-between overflow-hidden">
      <!-- Pattern Background Effect -->
      <div v-if="isSidebarHeaderHovered || isLogoHovered"
        class="absolute inset-0"
      >
        <WarpBackground 
        :perspective="60"
        :beamsPerSide="2"
        :beamSize="10"
        :beamDuration="3"
        :gridColor="starColor"
        class="!border-0 !rounded-none !p-0 w-full h-full"/>
        </div>

      <Logo @hover="handleLogoHover" class="z-60"/>
      <div class="mt-1 flex items-center justify-center z-60">
        <ThemeToggle />
      </div>
    </SidebarHeader>
    
    <SidebarContent class="p-4">
      <!-- Workspace & Environment Selector -->
      <WorkspaceEnvironmentSelector />

      <!-- Navigation -->
      <SidebarMenu>
        <SidebarMenuButton @click="router.push('/')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:inset-shadow-xl hover:border cursor-pointer transition-colors">
          <Home class="w-4 h-4 mr-2" />
          Home
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/metrics')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:inset-shadow-xl hover:border cursor-pointer transition-colors">
          <Target class="w-4 h-4 mr-2" />
          Metrics
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/dashboards')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:inset-shadow-xl hover:border cursor-pointer transition-colors">
          <BarChart3 class="w-4 h-4 mr-2" />
          Dashboards
        </SidebarMenuButton>
        <SidebarMenuButton @click="router.push('/data/sources')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:inset-shadow-xl hover:border cursor-pointer  transition-colors">
          <Database class="w-4 h-4 mr-2" />
          Data Sources
        </SidebarMenuButton>
        <!-- <SidebarMenuButton @click="router.push('/pre-aggregations')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors">
          <Zap class="w-4 h-4 mr-2" />
          Pre-Aggregations
        </SidebarMenuButton> -->
        <SidebarMenuButton @click="router.push('/consumers')" class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:inset-shadow-xl hover:border cursor-pointer transition-colors">
          <Users class="w-4 h-4 mr-2" />
          Consumers
        </SidebarMenuButton>
      </SidebarMenu>
    </SidebarContent>
  </Sidebar>
</ClientOnly>
</template>