<template>
  <div class="w-screen h-screen p-8 max-w-full overflow-auto">
    <slot />
    <Toaster />
  </div>
</template>

<script setup lang="ts">
import { Toaster } from '~/components/ui/sonner'
import 'vue-sonner/style.css'
</script> 