<script setup lang="ts">
import { computed } from 'vue'
import { useDark } from '@vueuse/core'
import { FileSpreadsheet, Database } from 'lucide-vue-next'
import { DATA_SOURCE_TYPES } from '~/config/dataSourceTypes'

interface Props {
  sourceType: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'sm'
})

const isDark = useDark({
  valueDark: 'dark',
  valueLight: 'light',
  selector: 'html',
  attribute: 'class',
  storageKey: 'cortex-color-scheme'
})

const iconConfig = computed(() => {
  const metadata = DATA_SOURCE_TYPES[props.sourceType]
  return metadata?.icon || { type: 'lucide', name: 'database' }
})

const assetPath = computed(() => {
  if (iconConfig.value.type === 'asset') {
    const mode = isDark.value ? 'dark' : 'light'
    return `/icons/brands/${iconConfig.value.name}-${mode}.svg`
  }
  return ''
})

const sizeMap = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6'
}

const iconClass = computed(() => sizeMap[props.size])

const alt = computed(() => {
  const metadata = DATA_SOURCE_TYPES[props.sourceType]
  return metadata?.label || props.sourceType
})
</script>

<template>
  <!-- Lucide Icons -->
  <FileSpreadsheet
    v-if="iconConfig.type === 'lucide' && iconConfig.name === 'file-spreadsheet'"
    :class="iconClass"
  />
  <Database
    v-else-if="iconConfig.type === 'lucide' && iconConfig.name === 'database'"
    :class="iconClass"
  />
  <!-- Asset Icons -->
  <NuxtImg
    v-else-if="iconConfig.type === 'asset' && assetPath"
    :src="assetPath"
    :alt="alt"
    :class="iconClass"
  />
</template>
