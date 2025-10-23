import { computed } from 'vue'
import { useDark } from '@vueuse/core'

/**
 * Composable to provide ECharts theme based on dark mode
 * @returns computed theme string for ECharts ('dark' or undefined for light)
 */
export function useChartTheme() {
  // Use the same dark mode configuration as the rest of the app
  const isDark = useDark({
    valueDark: 'dark',
    valueLight: 'shine',
    selector: 'html',
    attribute: 'class',
    storageKey: 'cortex-color-scheme'
  })

  // ECharts built-in theme: 'dark' for dark mode, undefined for light mode
  const chartTheme = computed(() => isDark.value ? 'dark' : undefined)

  return {
    isDark,
    chartTheme
  }
}

