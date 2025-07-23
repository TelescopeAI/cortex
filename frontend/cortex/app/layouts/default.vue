<template>
  <div>
    <slot />
    <Toaster />
  </div>
</template>

<script setup lang="ts">
import { Toaster } from '~/components/ui/sonner'
import 'vue-sonner/style.css'
</script> 