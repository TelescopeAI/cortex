<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <Settings class="h-5 w-5" />
        Overrides
      </CardTitle>
      <CardDescription>
        Component and scalar modifications applied to the source metric
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div v-if="!hasAnyOverrides" class="text-center py-8 text-muted-foreground">
        <Settings class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">No overrides configured</p>
        <p class="text-xs mt-1">All components inherited from source</p>
      </div>

      <div v-else class="space-y-4">
        <!-- Summary Stats -->
        <div class="grid grid-cols-3 gap-4">
          <div v-if="addCount > 0" class="text-center p-3 rounded-lg bg-green-50 dark:bg-green-950">
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              +{{ addCount }}
            </div>
            <div class="text-xs text-muted-foreground">Added</div>
          </div>
          <div v-if="replaceCount > 0" class="text-center p-3 rounded-lg bg-blue-50 dark:bg-blue-950">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              ~{{ replaceCount }}
            </div>
            <div class="text-xs text-muted-foreground">Replaced</div>
          </div>
          <div v-if="excludeCount > 0" class="text-center p-3 rounded-lg bg-red-50 dark:bg-red-950">
            <div class="text-2xl font-bold text-red-600 dark:text-red-400">
              -{{ excludeCount }}
            </div>
            <div class="text-xs text-muted-foreground">Excluded</div>
          </div>
        </div>

        <!-- Excluded Components -->
        <div v-if="hasExclusions">
          <Label class="text-sm font-medium">Excluded Components</Label>
          <div class="mt-2 space-y-2">
            <div v-if="overrides.exclude?.measures?.length">
              <Label class="text-xs text-muted-foreground">Measures</Label>
              <div class="flex flex-wrap gap-1 mt-1">
                <Badge
                  v-for="name in overrides.exclude.measures"
                  :key="name"
                  variant="destructive"
                  class="text-xs"
                >
                  {{ name }}
                </Badge>
              </div>
            </div>
            <div v-if="overrides.exclude?.dimensions?.length">
              <Label class="text-xs text-muted-foreground">Dimensions</Label>
              <div class="flex flex-wrap gap-1 mt-1">
                <Badge
                  v-for="name in overrides.exclude.dimensions"
                  :key="name"
                  variant="destructive"
                  class="text-xs"
                >
                  {{ name }}
                </Badge>
              </div>
            </div>
            <div v-if="overrides.exclude?.filters?.length">
              <Label class="text-xs text-muted-foreground">Filters</Label>
              <div class="flex flex-wrap gap-1 mt-1">
                <Badge
                  v-for="name in overrides.exclude.filters"
                  :key="name"
                  variant="destructive"
                  class="text-xs"
                >
                  {{ name }}
                </Badge>
              </div>
            </div>
            <div v-if="overrides.exclude?.joins?.length">
              <Label class="text-xs text-muted-foreground">Joins</Label>
              <div class="flex flex-wrap gap-1 mt-1">
                <Badge
                  v-for="name in overrides.exclude.joins"
                  :key="name"
                  variant="destructive"
                  class="text-xs"
                >
                  {{ name }}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        <!-- Scalar Overrides -->
        <div v-if="hasScalarOverrides">
          <Label class="text-sm font-medium">Scalar Overrides</Label>
          <div class="mt-2 space-y-2 text-sm">
            <div v-if="overrides.table_name" class="flex justify-between">
              <span class="text-muted-foreground">Table Name:</span>
              <span class="font-medium">{{ overrides.table_name }}</span>
            </div>
            <div v-if="overrides.limit !== undefined" class="flex justify-between">
              <span class="text-muted-foreground">Limit:</span>
              <span class="font-medium">{{ overrides.limit }}</span>
            </div>
            <div v-if="overrides.grouped !== undefined" class="flex justify-between">
              <span class="text-muted-foreground">Grouped:</span>
              <Badge :variant="overrides.grouped ? 'default' : 'secondary'">
                {{ overrides.grouped ? 'Yes' : 'No' }}
              </Badge>
            </div>
            <div v-if="overrides.ordered !== undefined" class="flex justify-between">
              <span class="text-muted-foreground">Ordered:</span>
              <Badge :variant="overrides.ordered ? 'default' : 'secondary'">
                {{ overrides.ordered ? 'Yes' : 'No' }}
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Settings, Plus, Edit, Minus } from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Separator } from '~/components/ui/separator'
import type { MetricOverrides } from '~/types/metric_variants'

interface Props {
  overrides: MetricOverrides | null | undefined
}

const props = defineProps<Props>()

const addCount = computed(() => {
  if (!props.overrides?.add) return 0
  return Object.values(props.overrides.add).reduce((sum, arr) => sum + (arr?.length || 0), 0)
})

const replaceCount = computed(() => {
  if (!props.overrides?.replace) return 0
  return Object.values(props.overrides.replace).reduce((sum, arr) => sum + (arr?.length || 0), 0)
})

const excludeCount = computed(() => {
  if (!props.overrides?.exclude) return 0
  return Object.values(props.overrides.exclude).reduce((sum, arr) => sum + (arr?.length || 0), 0)
})

const hasExclusions = computed(() => excludeCount.value > 0)

const hasScalarOverrides = computed(() => {
  return !!(
    props.overrides?.table_name ||
    props.overrides?.limit !== undefined ||
    props.overrides?.grouped !== undefined ||
    props.overrides?.ordered !== undefined
  )
})

const hasAnyOverrides = computed(() => {
  return addCount.value > 0 || replaceCount.value > 0 || excludeCount.value > 0 || hasScalarOverrides.value
})
</script>
