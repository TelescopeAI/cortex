<script setup lang="ts">
import { ChartSelector } from './charts'

// Define props
const props = defineProps<{
  data: Record<string, any>[]
}>()
</script>

<template>
  <ChartSelector :data="data" />
</template>
