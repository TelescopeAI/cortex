<template>
  <div class="flex items-center justify-start gap-3">
    <!-- Logo SVG -->
    <div class="flex-shrink-0">
      <NuxtImg 
        :src="logoSrc" 
        :alt="altText" 
        :class="logoClasses"
        :width="logoSize"
        :height="logoSize"
      />
    </div>
    
    <!-- Text - only show if showText is true -->
    <h1 v-if="showText" :class="textClasses">
      {{ text }}
    </h1>
  </div>
</template>

<script setup lang="ts">
interface Props {
  /** Whether to show the text alongside the logo */
  showText?: boolean
  /** Custom text to display (defaults to "Cortex") */
  text?: string
  /** Custom logo source URL */
  logoSrc?: string
  /** Alt text for the logo image */
  altText?: string
  /** Size of the logo in pixels */
  logoSize?: number
  /** CSS classes for the logo image */
  logoClasses?: string
  /** CSS classes for the text */
  textClasses?: string
}

const props = withDefaults(defineProps<Props>(), {
  showText: true,
  text: 'Cortex',
  logoSrc: '/TS_Planet_Logo_Blue.svg',
  altText: 'Cortex Logo',
  logoSize: 32,
  logoClasses: 'w-8 h-8',
  textClasses: 'text-2xl font-sans font-light tracking-tight text-selection-none text-blue-500 group-data-[collapsible=icon]:hidden'
})
</script>

<style scoped>
/* Component-specific styles can be added here if needed */
</style>
