<template>
  <Card class="border-0 shadow-none">
    <CardHeader>
      <CardTitle>Execution Context</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <ContextIdBuilder :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" />
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import ContextIdBuilder from '~/components/ContextIdBuilder.vue'

interface Props {
  modelValue: string
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>
