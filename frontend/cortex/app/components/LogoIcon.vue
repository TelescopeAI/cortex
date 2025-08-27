<template>
  <div class="flex-shrink-0">
    <NuxtImg 
      :src="logoSrc" 
      :alt="altText" 
      :class="logoClasses"
      :width="size"
      :height="size"
    />
  </div>
</template>

<script setup lang="ts">
interface Props {
  /** Custom logo source URL */
  logoSrc?: string
  /** Alt text for the logo image */
  altText?: string
  /** Size of the logo in pixels */
  size?: number
  /** CSS classes for the logo image */
  logoClasses?: string
}

const props = withDefaults(defineProps<Props>(), {
  logoSrc: 'TS_Planet_Logo_Blue.svg',
  altText: 'Cortex',
  size: 24,
  logoClasses: 'w-6 h-6'
})
</script>

<style scoped>
/* Component-specific styles can be added here if needed */
</style>
