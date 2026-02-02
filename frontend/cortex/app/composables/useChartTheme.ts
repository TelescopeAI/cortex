import { computed } from 'vue'
import { useDark } from '@vueuse/core'
import { shadcnLightTheme } from '~/assets/themes/charts/shadcn-light'
import { shadcnDarkTheme } from '~/assets/themes/charts/shadcn-dark'

/**
 * Composable to provide ECharts theme based on dark mode
 * Now returns custom Shadcn theme objects instead of ECharts built-in themes
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

  // Return Shadcn theme objects (not strings!)
  // VChart accepts theme objects directly via :theme prop
  const chartTheme = computed(() => isDark.value ? shadcnDarkTheme : shadcnLightTheme)

  return {
    isDark,
    chartTheme
  }
}

