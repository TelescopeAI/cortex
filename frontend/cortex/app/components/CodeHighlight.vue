<template>
  <div class="max-w-full overflow-x-auto p-4 rounded-lg bg-[#FAFAFA]">
    <Shiki v-bind="$attrs" class="font-geist"/>
  </div>
</template>

<script setup lang="ts">
// This component wraps Shiki with consistent styling
// It passes through all props to the Shiki component
</script> 
<style scoped>
.shiki one-light,
.span {
  font-family: var(--shiki-font-family) !important;
}

html.dark .shiki,
html.dark .shiki span {
  /* Optional, if you also want font styles */
  font-style: var(--shiki-light-font-style) !important;
  font-weight: var(--shiki-dark-font-weight) !important;
  text-decoration: var(--shiki-dark-text-decoration) !important;
}
</style>