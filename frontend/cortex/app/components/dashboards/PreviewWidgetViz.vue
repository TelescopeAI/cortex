<script setup lang="ts">
import { ref, watch } from 'vue'
import ChartRenderer from './ChartRenderer.vue'

interface Props {
  type: string
  data: any | null
  loading?: boolean
  error?: string | null
  gaugeConfig?: any
  singleValueConfig?: any
  chartConfig?: any
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null
})

// Create refs to store the data for proper reactivity
const processedData = ref<any>(null)
const metadata = ref<any>(null)
const chartType = ref<string>('')
const gaugeConfigData = ref<any>(null)
const singleValueConfigData = ref<any>(null)
const chartConfigData = ref<any>(null)

// Watch for changes in props and update refs
watch(() => props.data, (newData) => {
  if (newData) {
    processedData.value = newData.processed
    metadata.value = newData.metadata
  } else {
    processedData.value = null
    metadata.value = null
  }
}, { immediate: true, deep: true })

watch(() => props.type, (newType) => {
  chartType.value = newType
}, { immediate: true })

watch(() => props.gaugeConfig, (newConfig) => {
  gaugeConfigData.value = newConfig
}, { immediate: true, deep: true })

watch(() => props.singleValueConfig, (newConfig) => {
  singleValueConfigData.value = newConfig
}, { immediate: true, deep: true })

watch(() => props.chartConfig, (newConfig) => {
  chartConfigData.value = newConfig
}, { immediate: true, deep: true })
</script>

<template>
  <div class="h-full w-full">
    <div v-if="loading" class="space-y-3">
      <div class="h-6 w-40 bg-muted rounded animate-pulse" />
      <div class="h-64 w-full bg-muted rounded animate-pulse" />
    </div>
    <div v-else-if="error" class="text-sm text-destructive border border-destructive/30 bg-destructive/10 rounded p-2">
      {{ error }}
    </div>
    <ChartRenderer 
      v-else-if="processedData && metadata" 
      :processed="processedData" 
      :metadata="metadata" 
      :type="chartType" 
      :gauge-config="gaugeConfigData"
      :single-value-config="singleValueConfigData"
      :chart-config="chartConfigData"
    />
    <div v-else class="text-sm text-muted-foreground">No preview available</div>
  </div>
</template>


