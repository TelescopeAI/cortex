<template>
  <Card
    class="hover:ring-2 hover:ring-purple-900
          h-80 lg:h-40 justify-between
          transition-shadow cursor-pointer gap-0"
    @click="$emit('click')"
  >
    <CardHeader>
      <div class="flex flex-col items-start justify-between gap-y-2">
        <div class="flex items-start justify-between w-full">
          <div class="space-y-1 flex-1">
            <div class="flex items-center gap-2">
              <GitBranch class="h-4 w-4 text-purple-600 dark:text-purple-400" />
              <CardTitle class="text-xl font-extrabold text-purple-900 dark:text-white">
                {{ variant.name }}
              </CardTitle>
            </div>
          </div>
          <Badge :variant="variant.public ? 'default' : 'secondary'" class="ml-2">
            {{ variant.public ? 'Public' : 'Private' }}
          </Badge>
        </div>
        <p
          v-if="variant.description"
          class="text-sm line-clamp-2 text-purple-600 dark:text-purple-200"
        >
          {{ variant.description }}
        </p>
      </div>
    </CardHeader>

    <CardContent class="pt-0">
      <div class="space-y-3">
        <div class="flex flex-col md:flex-row items-center justify-between">
          <div class="flex flex-row justify-start items-center gap-x-2">
            <span class="text-sm text-muted-foreground">
              {{ sourceMetricName || 'Unknown Source' }}
            </span>
          </div>
          <span class="text-xs text-lime-700 dark:text-lime-300">
            Updated {{ formatRelativeTime(variant.updated_at) }}
          </span>
        </div>

        <!-- Show override counts if available -->
        <div v-if="hasOverrides" class="flex items-center gap-2 text-xs text-muted-foreground">
          <span v-if="overrideCounts.add > 0">+{{ overrideCounts.add }}</span>
          <span v-if="overrideCounts.replace > 0">~{{ overrideCounts.replace }}</span>
          <span v-if="overrideCounts.exclude > 0">-{{ overrideCounts.exclude }}</span>
          <span v-if="variant.derivations && variant.derivations.length > 0">
            {{ variant.derivations.length }} derived
          </span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTimeAgo } from '@vueuse/core'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { GitBranch } from 'lucide-vue-next'
import type { SemanticMetricVariant } from '~/types/metric_variants'

interface Props {
  variant: SemanticMetricVariant
  sourceMetricName?: string
}

const props = defineProps<Props>()

defineEmits<{
  'click': []
}>()

const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

const formatRelativeTime = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, {
    updateInterval: 1000
  })
}

const hasOverrides = computed(() => {
  return props.variant.overrides && (
    props.variant.overrides.add ||
    props.variant.overrides.replace ||
    props.variant.overrides.exclude
  )
})

const overrideCounts = computed(() => {
  if (!props.variant.overrides) {
    return { add: 0, replace: 0, exclude: 0 }
  }

  const add = props.variant.overrides.add ?
    Object.values(props.variant.overrides.add).reduce((sum, arr) => sum + (arr?.length || 0), 0) : 0

  const replace = props.variant.overrides.replace ?
    Object.values(props.variant.overrides.replace).reduce((sum, arr) => sum + (arr?.length || 0), 0) : 0

  const exclude = props.variant.overrides.exclude ?
    Object.values(props.variant.overrides.exclude).reduce((sum, arr) => sum + (arr?.length || 0), 0) : 0

  return { add, replace, exclude }
})
</script>
