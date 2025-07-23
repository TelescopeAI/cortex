<template>
  <NuxtLayout>
    <SidebarProvider>
      <div class="w-full h-full flex min-h-screen">
        <Sidebar />
        <main class="flex-1">
          <NuxtPage />
        </main>
      </div>
    </SidebarProvider>
  </NuxtLayout>
</template>

<script setup lang="ts">
import { SidebarProvider } from '~/components/ui/sidebar';
import Sidebar from '~/components/Sidebar.vue';
</script>
