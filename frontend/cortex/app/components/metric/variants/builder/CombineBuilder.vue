<template>
  <div class="space-y-4">
    <Alert>
      <Layers class="h-4 w-4" />
      <AlertTitle>Multi-Source Composition</AlertTitle>
      <AlertDescription>
        Combine multiple metrics into a single query using CTEs (Common Table Expressions). Perfect for joining data from different sources.
      </AlertDescription>
    </Alert>

    <Card>
      <CardContent class="pt-6">
        <div class="text-center py-8 text-muted-foreground">
          <Layers class="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p class="text-sm">Multi-source composer coming soon</p>
          <p class="text-xs mt-1">
            You'll be able to combine multiple metrics with CTE-based joins
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Card, CardContent } from '~/components/ui/card'
import { Layers } from 'lucide-vue-next'
import type { MetricRef } from '~/types/metric_variants'

interface Props {
  modelValue: MetricRef[]
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: MetricRef[]]
}>()
</script>
