<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <TrendingUp class="h-5 w-5" />
        Derivations
      </CardTitle>
      <CardDescription>
        Derived measures using window functions and arithmetic operations
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="!derivations || derivations.length === 0" class="text-center py-8 text-muted-foreground">
        <TrendingUp class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No derivations configured</p>
        <p class="text-xs mt-1">All measures computed directly from source</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="derivation in derivations"
          :key="derivation.name"
          class="border rounded-lg p-4 space-y-2"
        >
          <!-- Derivation Header -->
          <div class="flex items-start justify-between">
            <div>
              <div class="font-medium text-base">{{ derivation.name }}</div>
              <Badge variant="outline" class="mt-1">{{ derivation.type }}</Badge>
            </div>
          </div>

          <!-- Source Info -->
          <div class="text-sm space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-muted-foreground">Source:</span>
              <Badge variant="secondary">{{ derivation.source.measure }}</Badge>
            </div>
            <div v-if="derivation.source.by" class="flex items-center gap-2">
              <span class="text-muted-foreground">By:</span>
              <Badge variant="secondary">{{ derivation.source.by }}</Badge>
            </div>
          </div>

          <!-- Additional Config -->
          <div v-if="hasAdditionalConfig(derivation)" class="text-xs space-y-1 pt-2 border-t">
            <div v-if="derivation.order_dimension" class="flex justify-between">
              <span class="text-muted-foreground">Order By:</span>
              <span>{{ derivation.order_dimension }}</span>
            </div>
            <div v-if="derivation.partition_by" class="flex justify-between">
              <span class="text-muted-foreground">Partition By:</span>
              <span>{{ derivation.partition_by }}</span>
            </div>
            <div v-if="derivation.offset !== undefined" class="flex justify-between">
              <span class="text-muted-foreground">Offset:</span>
              <span>{{ derivation.offset }}</span>
            </div>
            <div v-if="derivation.n !== undefined" class="flex justify-between">
              <span class="text-muted-foreground">N:</span>
              <span>{{ derivation.n }}</span>
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { TrendingUp } from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import type { DerivedEntity } from '~/types/metric_variants'

interface Props {
  derivations: DerivedEntity[] | null | undefined
}

defineProps<Props>()

const hasAdditionalConfig = (derivation: DerivedEntity) => {
  return !!(
    derivation.order_dimension ||
    derivation.partition_by ||
    derivation.offset !== undefined ||
    derivation.n !== undefined
  )
}
</script>
