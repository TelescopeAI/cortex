<template>
  <div class="space-y-4">
    <Alert>
      <TrendingUp class="h-4 w-4" />
      <AlertTitle>Derived Measures</AlertTitle>
      <AlertDescription>
        Create derived measures using window functions (running_total, percent_of_total) or arithmetic operations (divide, multiply).
      </AlertDescription>
    </Alert>

    <Card>
      <CardContent class="pt-6">
        <div class="text-center py-8 text-muted-foreground">
          <TrendingUp class="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p class="text-sm">Derivations builder coming soon</p>
          <p class="text-xs mt-1">
            You'll be able to create window functions and arithmetic derivations
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Card, CardContent } from '~/components/ui/card'
import { TrendingUp } from 'lucide-vue-next'
import type { DerivedEntity } from '~/types/metric_variants'

interface Props {
  modelValue: DerivedEntity[]
}

defineProps<Props>()

defineEmits<{
  'update:modelValue': [value: DerivedEntity[]]
}>()
</script>
