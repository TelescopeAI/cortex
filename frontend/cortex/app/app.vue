<template>
  <div>
    <!-- Page metadata -->
    <Head>
      <title>Cortex - Data Analytics Platform</title>
      <link rel="icon" type="image/svg+xml" href="~/assets/images/TS_Planet_Logo_Blue.svg" />
      <meta name="description" content="Cortex - Advanced data analytics and visualization platform" />
    </Head>
    
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
  </div>
</template>

<script setup lang="ts">
import { SidebarProvider } from '~/components/ui/sidebar';
import Sidebar from '~/components/Sidebar.vue';
</script>
