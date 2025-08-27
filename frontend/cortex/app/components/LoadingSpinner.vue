<template>
  <div class="flex flex-col items-center justify-center space-y-4">
    <!-- Optional Logo -->
    <LogoIcon v-if="showLogo" :size="logoSize" class="opacity-75" />
    
    <!-- Spinner -->
    <div class="relative">
      <div 
        class="animate-spin rounded-full border-2 border-gray-300 border-t-primary"
        :class="spinnerClasses"
        :style="{ width: `${size}px`, height: `${size}px` }"
      ></div>
    </div>
    
    <!-- Loading Text -->
    <p v-if="text" class="text-sm text-muted-foreground text-center">
      {{ text }}
    </p>
  </div>
</template>

<script setup lang="ts">
import LogoIcon from './LogoIcon.vue'

interface Props {
  /** Whether to show the logo above the spinner */
  showLogo?: boolean
  /** Size of the logo in pixels */
  logoSize?: number
  /** Size of the spinner in pixels */
  size?: number
  /** Loading text to display */
  text?: string
  /** Additional CSS classes for the spinner */
  spinnerClasses?: string
}

const props = withDefaults(defineProps<Props>(), {
  showLogo: false,
  logoSize: 32,
  size: 24,
  text: '',
  spinnerClasses: ''
})
</script>

<style scoped>
/* Component-specific styles can be added here if needed */
</style>
