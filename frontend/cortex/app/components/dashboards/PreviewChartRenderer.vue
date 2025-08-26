<script setup lang="ts">
import ChartRenderer from './ChartRenderer.vue'
const props = defineProps<{ 
  processed: any; 
  metadata?: any; 
  type: string; 
  gaugeConfig?: any; 
  singleValueConfig?: any;
}>()
</script>

<template>
  <ChartRenderer 
    :processed="processed" 
    :metadata="metadata" 
    :type="type" 
    :gauge-config="gaugeConfig" 
    :single-value-config="singleValueConfig" 
  />
</template>


