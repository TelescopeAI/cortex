<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <Layers class="h-5 w-5" />
        Multi-Source Composition
      </CardTitle>
      <CardDescription>
        Additional metrics combined via CTEs (Common Table Expressions)
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="!combine || combine.length === 0" class="text-center py-8 text-muted-foreground">
        <Layers class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No combined metrics</p>
        <p class="text-xs mt-1">This variant uses a single source</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(combined, index) in combine"
          :key="index"
          class="border rounded-lg p-4 space-y-3"
        >
          <!-- Metric Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="p-2 rounded-md bg-purple-50 dark:bg-purple-950">
                <Database class="h-4 w-4 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div class="font-medium">{{ combined.alias || `Metric ${index + 1}` }}</div>
                <div class="text-xs text-muted-foreground">
                  {{ combined.metric_id ? `ID: ${combined.metric_id.slice(0, 8)}...` : 'Inline metric' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Join Configuration -->
          <div v-if="combined.join_on && combined.join_on.length > 0">
            <Label class="text-xs text-muted-foreground">Join On</Label>
            <div class="flex flex-wrap gap-1 mt-1">
              <Badge
                v-for="dimension in combined.join_on"
                :key="dimension"
                variant="outline"
              >
                {{ dimension }}
              </Badge>
            </div>
          </div>

          <!-- Inline Metric Info -->
          <div v-if="combined.metric" class="text-xs space-y-1 pt-2 border-t">
            <div class="grid grid-cols-2 gap-2">
              <div class="text-center p-2 rounded bg-muted">
                <div class="font-bold">{{ combined.metric.measures?.length || 0 }}</div>
                <div class="text-muted-foreground">Measures</div>
              </div>
              <div class="text-center p-2 rounded bg-muted">
                <div class="font-bold">{{ combined.metric.dimensions?.length || 0 }}</div>
                <div class="text-muted-foreground">Dimensions</div>
              </div>
            </div>
          </div>
        </div>

        <!-- CTE Info -->
        <Alert>
          <Info class="h-4 w-4" />
          <AlertTitle>Query Generation</AlertTitle>
          <AlertDescription class="text-xs">
            These metrics will be compiled into separate CTEs and joined in the outer query,
            enabling cross-metric derivations and calculations.
          </AlertDescription>
        </Alert>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Layers, Database, Info } from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Alert, AlertTitle, AlertDescription } from '~/components/ui/alert'
import type { MetricRef } from '~/types/metric_variants'

interface Props {
  combine: MetricRef[] | null | undefined
}

defineProps<Props>()
</script>
