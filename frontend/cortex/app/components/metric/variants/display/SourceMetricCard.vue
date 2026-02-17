<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <GitBranch class="h-5 w-5 text-purple-600 dark:text-purple-400" />
        Source Metric
      </CardTitle>
      <CardDescription>
        The base metric this variant is derived from
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <div v-if="loading" class="space-y-3">
        <div class="h-4 bg-muted rounded w-3/4 animate-pulse"></div>
        <div class="h-4 bg-muted rounded w-1/2 animate-pulse"></div>
      </div>

      <div v-else-if="sourceMetric" class="space-y-4">
        <!-- Metric Name -->
        <div>
          <Label class="text-sm text-muted-foreground">Metric</Label>
          <Button
            variant="link"
            class="h-auto p-0 font-medium text-base"
            @click="navigateToMetric"
          >
            {{ sourceMetric.title || sourceMetric.name }}
          </Button>
        </div>

        <!-- Source Alias -->
        <div v-if="source.alias">
          <Label class="text-sm text-muted-foreground">Alias</Label>
          <p class="font-medium">{{ source.alias }}</p>
        </div>

        <!-- Metric Stats -->
        <div class="grid grid-cols-2 gap-4 pt-2">
          <div class="text-center p-3 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ sourceMetric.measures?.length || 0 }}</div>
            <div class="text-xs text-muted-foreground">Measures</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ sourceMetric.dimensions?.length || 0 }}</div>
            <div class="text-xs text-muted-foreground">Dimensions</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ sourceMetric.filters?.length || 0 }}</div>
            <div class="text-xs text-muted-foreground">Filters</div>
          </div>
          <div class="text-center p-3 rounded-lg bg-muted">
            <div class="text-2xl font-bold">{{ sourceMetric.joins?.length || 0 }}</div>
            <div class="text-xs text-muted-foreground">Joins</div>
          </div>
        </div>

        <!-- Description -->
        <div v-if="sourceMetric.description">
          <Label class="text-sm text-muted-foreground">Description</Label>
          <p class="text-sm mt-1">{{ sourceMetric.description }}</p>
        </div>
      </div>

      <div v-else class="text-center py-4 text-muted-foreground">
        <AlertCircle class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">Source metric not found</p>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { GitBranch, AlertCircle } from 'lucide-vue-next'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import type { MetricRef } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  source: MetricRef
  environmentId: string
}

const props = defineProps<Props>()

const { getMetric } = useMetrics()
const router = useRouter()

const sourceMetric = ref<SemanticMetric | null>(null)
const loading = ref(false)

const loadSourceMetric = async () => {
  if (!props.source.metric_id) return

  loading.value = true
  try {
    sourceMetric.value = await getMetric(props.source.metric_id, props.environmentId)
  } catch (error) {
    console.error('Failed to load source metric:', error)
  } finally {
    loading.value = false
  }
}

const navigateToMetric = () => {
  if (props.source.metric_id) {
    router.push(`/metrics/${props.source.metric_id}`)
  }
}

onMounted(() => {
  loadSourceMetric()
})

watch(() => props.source.metric_id, () => {
  loadSourceMetric()
})
</script>
