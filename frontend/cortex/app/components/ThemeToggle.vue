<template>
  <button
    class="theme-toggle"
    :class="{ 'theme-toggle--toggled': !isDark }"
    type="button"
    title="Toggle theme"
    aria-label="Toggle theme"
    @click="toggleTheme"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      class="theme-toggle__within h-5 w-5"
      :class="svgColorClass"
      viewBox="0 0 32 32"
      fill="currentColor"
    >
      <clipPath id="theme-toggle__within__clip">
        <path d="M0 0h32v32h-32ZM6 16A1 1 0 0026 16 1 1 0 006 16" />
      </clipPath>
      <g clip-path="url(#theme-toggle__within__clip)">
        <path d="M30.7 21.3 27.1 16l3.7-5.3c.4-.5.1-1.3-.6-1.4l-6.3-1.1-1.1-6.3c-.1-.6-.8-.9-1.4-.6L16 5l-5.4-3.7c-.5-.4-1.3-.1-1.4.6l-1 6.3-6.4 1.1c-.6.1-.9.9-.6 1.3L4.9 16l-3.7 5.3c-.4.5-.1 1.3.6 1.4l6.3 1.1 1.1 6.3c.1.6.8.9 1.4.6l5.3-3.7 5.3 3.7c.5.4 1.3.1 1.4-.6l1.1-6.3 6.3-1.1c.8-.1 1.1-.8.7-1.4zM16 25.1c-5.1 0-9.1-4.1-9.1-9.1 0-5.1 4.1-9.1 9.1-9.1s9.1 4.1 9.1 9.1c0 5.1-4 9.1-9.1 9.1z" />
      </g>
      <path
        class="theme-toggle__within__circle"
        d="M16 7.7c-4.6 0-8.2 3.7-8.2 8.2s3.6 8.4 8.2 8.4 8.2-3.7 8.2-8.2-3.6-8.4-8.2-8.4zm0 14.4c-3.4 0-6.1-2.9-6.1-6.2s2.7-6.1 6.1-6.1c3.4 0 6.1 2.9 6.1 6.2s-2.7 6.1-6.1 6.1z"
      />
      <path
        class="theme-toggle__within__inner"
        d="M16 9.5c-3.6 0-6.4 2.9-6.4 6.4s2.8 6.5 6.4 6.5 6.4-2.9 6.4-6.4-2.8-6.5-6.4-6.5z"
      />
    </svg>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDark } from '@vueuse/core'
import { Button } from '@/components/ui/button'

// Load the CSS for the "within" toggle from toggles.dev
useHead({
  link: [
    {
      rel: 'stylesheet',
      href: 'https://cdn.jsdelivr.net/npm/theme-toggles@4.10.1/css/within.min.css'
    }
  ]
})

// Use the same configuration as the parent component
const isDark = useDark({
  valueDark: 'dark',
  valueLight: 'light',
  selector: 'html',
  attribute: 'class',
  storageKey: 'cortex-color-scheme'
})

const toggleTheme = () => {
  isDark.value = !isDark.value
}

// Computed class for SVG color based on theme
const svgColorClass = computed(() => {
  return isDark.value 
    ? 'text-yellow-500'  // Dark mode active, show yellow (light mode button)
    : 'text-blue-500'    // Light mode active, show blue (dark mode button)
})

const unclippedStarClasses = computed(() => {
  return isDark.value 
    ? 'opacity-0' 
    : 'opacity-100'
})

const clippedStarClasses = computed(() => {
  return isDark.value 
    ? 'opacity-100' 
    : 'opacity-0'
})

const circleClasses = computed(() => {
  return isDark.value 
    ? 'opacity-0 scale-75' 
    : 'opacity-100 scale-100'
})

const innerClasses = computed(() => {
  return isDark.value 
    ? 'opacity-0 scale-75' 
    : 'opacity-100 scale-100'
})
</script>

<style scoped>
/* Screen reader only text */
/* .theme-toggle-sr {
  @apply sr-only;
} */

/* Smooth transitions for all elements */
/* .theme-toggle__within,
.theme-toggle__within__circle,
.theme-toggle__within__inner {
  transform-origin: center;
} */
</style> 
