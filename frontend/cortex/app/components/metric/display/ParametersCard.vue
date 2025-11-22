<template>
  <Card v-if="parameters && parameters.length > 0" class="border-0 shadow-none">
    <CardHeader>
      <CardTitle>Parameters</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <KeyValuePairs
        :model-value="modelValue"
        @update:model-value="$emit('update:modelValue', $event || {})"
        :is-loading="isLoading"
      />
      <div class="text-xs text-muted-foreground">
        <p>Available parameters from metric schema: {{ parameters?.map((p: any) => p.name).join(', ') || 'None' }}</p>
        <p class="mt-1">Use $CORTEX_ prefix in metric schema to auto-substitute with consumer properties when context_id is provided.</p>
        <p v-if="availableCortexParameters.length > 0" class="mt-1">
          <span class="font-medium">$CORTEX_ parameters found:</span> {{ availableCortexParameters.join(', ') }}
        </p>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import KeyValuePairs from '~/components/KeyValuePairs.vue'

interface Props {
  modelValue: Record<string, any>
  parameters: any[]
  availableCortexParameters: string[]
  isLoading: boolean
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()
</script>
