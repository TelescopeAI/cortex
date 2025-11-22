<template>
  <div ref="logoRef" class="flex items-center justify-start gap-3">
    <!-- Logo SVG -->
    <div class="flex-shrink-0">
      <NuxtImg 
        :src="logoSrc" 
        :alt="altText" 
        class="hover:scale-110 hover:rotate-12 z-60 transition-transform duration-500"
        :class="logoClasses"
        :width="logoSize"
        :height="logoSize"
      />
    </div>
    
    <!-- Text - only show if showText is true -->
    <h1 v-if="showText" class="dark:text-white z-10"  :class="textClasses">
      {{ text }}
    </h1>
  </div>
</template>

<script setup lang="ts">
import { useElementHover } from '@vueuse/core'
import { ref, watch } from 'vue'

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

const emit = defineEmits<{
  (e: 'hover', value: boolean): void
}>()

const logoRef = ref<HTMLElement | null>(null)
const isHovered = useElementHover(logoRef)

watch(isHovered, (value) => {
  emit('hover', value)
})
</script>

<style scoped>
/* Component-specific styles can be added here if needed */
</style>
