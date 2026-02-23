<template>
  <div class="container py-6 space-y-6">
    <!-- Breadcrumb Navigation -->
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink href="/metrics">Metrics</BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbLink :href="`/metrics/${metricId}`">
            {{ sourceMetric?.title || sourceMetric?.name || 'Metric' }}
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbLink :href="`/metrics/${metricId}/variants`">
            Variants
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>{{ variant?.name || 'Variant' }}</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- Loading State -->
    <div v-if="loading && !variant" class="space-y-4">
      <div class="h-16 rounded-lg border bg-card animate-pulse"></div>
      <div class="h-96 rounded-lg border bg-card animate-pulse"></div>
    </div>

    <!-- Variant Not Found -->
    <Card v-else-if="!variant && !loading">
      <CardContent class="py-12 text-center">
        <AlertCircle class="h-12 w-12 mx-auto mb-4 text-destructive" />
        <h3 class="text-lg font-semibold mb-2">Variant Not Found</h3>
        <p class="text-muted-foreground mb-4">
          The variant you're looking for doesn't exist or has been deleted.
        </p>
        <Button @click="router.push(`/metrics/${metricId}/variants`)">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Variants
        </Button>
      </CardContent>
    </Card>

    <!-- Variant Content -->
    <template v-else-if="variant">
      <!-- Header with Actions -->
      <div class="flex items-start justify-between">
        <div class="space-y-1 flex-1">
          <div class="flex items-center gap-3">
            <GitBranch class="h-8 w-8 text-purple-600 dark:text-purple-400" />
            <h1 class="text-3xl font-bold tracking-tight">{{ variant.name }}</h1>
            <Badge :variant="variant.public ? 'default' : 'secondary'">
              {{ variant.public ? 'Public' : 'Private' }}
            </Badge>
          </div>
          <p v-if="variant.description" class="text-muted-foreground">
            {{ variant.description }}
          </p>
          <div class="flex items-center gap-4 text-sm text-muted-foreground pt-2">
            <span>Version {{ variant.version }}</span>
            <span>•</span>
            <span>Created {{ formatRelativeTime(variant.created_at) }}</span>
            <span>•</span>
            <span>Updated {{ formatRelativeTime(variant.updated_at) }}</span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="outline" size="icon">
                <MoreVertical class="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem @click="editVariant">
                <Edit class="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem @click="cloneVariant">
                <Copy class="h-4 w-4 mr-2" />
                Clone
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="resetVariant">
                <RotateCcw class="h-4 w-4 mr-2" />
                Reset to Source
              </DropdownMenuItem>
              <DropdownMenuItem @click="detachVariant">
                <Unlink class="h-4 w-4 mr-2" />
                Detach (Convert to Metric)
              </DropdownMenuItem>
              <DropdownMenuItem @click="overrideSource">
                <Upload class="h-4 w-4 mr-2" />
                Override Source
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="deleteVariant" class="text-destructive">
                <Trash class="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <!-- Tabs -->
      <Tabs v-model="activeTab" class="space-y-4">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="overview">
            <Info class="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="composition">
            <Layers class="h-4 w-4 mr-2" />
            Composition
          </TabsTrigger>
          <TabsTrigger value="execute">
            <Play class="h-4 w-4 mr-2" />
            Execute
          </TabsTrigger>
          <TabsTrigger value="history">
            <Clock class="h-4 w-4 mr-2" />
            History
          </TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-4">
          <MetricVariantsDisplaySourceMetricCard
            :source="variant.source"
            :environment-id="selectedEnvironmentId!"
          />

          <MetricVariantsDisplayOverridesCard
            :overrides="variant.overrides"
          />

          <MetricVariantsDisplayDerivationsCard
            :derivations="variant.derivations"
          />

          <MetricVariantsDisplayCombineCard
            :combine="variant.combine"
          />
        </TabsContent>

        <!-- Composition Tab -->
        <TabsContent value="composition" class="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Resolved Composition</CardTitle>
              <CardDescription>
                View the fully resolved metric after compilation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="text-center py-8 text-muted-foreground">
                <Layers class="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Composition viewer coming soon</p>
                <p class="text-sm mt-2">This will show the resolved metric structure</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Execute Tab -->
        <TabsContent value="execute" class="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Execute Variant</CardTitle>
              <CardDescription>
                Run this variant and view results
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center gap-4">
                <Button @click="executeVariantQuery" :disabled="executing">
                  <Play v-if="!executing" class="h-4 w-4 mr-2" />
                  <Loader2 v-else class="h-4 w-4 mr-2 animate-spin" />
                  {{ executing ? 'Executing...' : 'Execute Variant' }}
                </Button>
                <div v-if="executionTime" class="text-sm text-muted-foreground">
                  Executed in {{ executionTime }}ms
                </div>
              </div>

              <!-- Results -->
              <div v-if="executionResults">
                <div v-if="executionResults.success" class="space-y-4">
                  <Alert>
                    <CheckCircle2 class="h-4 w-4" />
                    <AlertTitle>Success</AlertTitle>
                    <AlertDescription>
                      Returned {{ executionResults.data?.length || 0 }} rows
                    </AlertDescription>
                  </Alert>

                  <!-- Results Table -->
                  <div v-if="executionResults.data && executionResults.data.length > 0" class="border rounded-lg overflow-x-auto">
                    <table class="w-full text-sm">
                      <thead class="border-b bg-muted/50">
                        <tr>
                          <th v-for="key in Object.keys(executionResults.data[0])" :key="key" class="px-4 py-2 text-left font-medium">
                            {{ key }}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, idx) in executionResults.data.slice(0, 100)" :key="idx" class="border-b last:border-b-0">
                          <td v-for="key in Object.keys(row)" :key="key" class="px-4 py-2">
                            {{ row[key] }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <Alert v-else variant="destructive">
                  <AlertCircle class="h-4 w-4" />
                  <AlertTitle>Execution Failed</AlertTitle>
                  <AlertDescription>
                    {{ executionResults.error || 'Unknown error occurred' }}
                  </AlertDescription>
                </Alert>
              </div>

              <div v-else-if="!executing" class="text-center py-12 text-muted-foreground">
                <Play class="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Click "Execute Variant" to run this variant and see results</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- History Tab -->
        <TabsContent value="history" class="space-y-4">
          <MetricQueryHistory
            v-if="variant"
            :metric-id="variant.id"
          />
        </TabsContent>
      </Tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTimeAgo } from '@vueuse/core'
import { toast } from 'vue-sonner'
import {
  AlertCircle, ArrowLeft, GitBranch, MoreVertical, Edit, Copy,
  RotateCcw, Unlink, Upload, Trash, Info, Layers, Play, Clock,
  CheckCircle2, Loader2
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '~/components/ui/card'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator
} from '~/components/ui/breadcrumb'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import type { SemanticMetricVariant } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

const route = useRoute()
const router = useRouter()
const metricId = computed(() => route.params.id as string)
const variantId = computed(() => route.params.variantId as string)

const { selectedEnvironmentId } = useEnvironments()
const { getVariant, loading, deleteVariant: deleteVariantApi, resetVariant: resetVariantApi, detachVariant: detachVariantApi, overrideSource: overrideSourceApi, executeVariant } = useMetricVariants()
const { getMetric } = useMetrics()

// State
const variant = ref<SemanticMetricVariant | null>(null)
const sourceMetric = ref<SemanticMetric | null>(null)
const activeTab = ref('overview')
const executing = ref(false)
const executionResults = ref<any>(null)
const executionTime = ref<number | null>(null)

// Methods
const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

const formatRelativeTime = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, { updateInterval: 1000 })
}

const loadVariant = async () => {
  if (!selectedEnvironmentId.value || !variantId.value) return

  const result = await getVariant(variantId.value, selectedEnvironmentId.value)
  variant.value = result

  // Load source metric if variant loaded successfully
  if (result?.source?.metric_id) {
    const source = await getMetric(result.source.metric_id, selectedEnvironmentId.value)
    sourceMetric.value = source
  }
}

const editVariant = () => {
  // TODO: Open edit dialog
  console.log('Edit variant:', variantId.value)
}

const cloneVariant = () => {
  // TODO: Open clone dialog
  console.log('Clone variant:', variantId.value)
}

const resetVariant = async () => {
  if (!variantId.value || !confirm('Reset this variant to match its source metric?')) return

  try {
    const result = await resetVariantApi(variantId.value)
    if (result) {
      variant.value = result
      toast.success('Variant has been reset to match its source metric')
    } else {
      toast.error('Failed to reset variant')
    }
  } catch (error) {
    console.error('Failed to reset variant:', error)
    toast.error(error instanceof Error ? error.message : 'Failed to reset variant')
  }
}

const detachVariant = async () => {
  if (!variantId.value || !confirm('Convert this variant to a standalone metric? This cannot be undone.')) return

  try {
    const result = await detachVariantApi(variantId.value)
    if (result) {
      toast.success('Variant has been converted to a standalone metric')
      router.push(`/metrics/${result.id}`)
    } else {
      toast.error('Failed to detach variant')
    }
  } catch (error) {
    console.error('Failed to detach variant:', error)
    toast.error(error instanceof Error ? error.message : 'Failed to detach variant')
  }
}

const overrideSource = async () => {
  if (!variantId.value || !confirm('Override the source metric with this variant\'s configuration? This cannot be undone.')) return

  try {
    await overrideSourceApi(variantId.value)
    toast.success('Source metric has been overridden with this variant\'s configuration')
    // Reload variant to reflect any changes
    await loadVariant()
  } catch (error) {
    console.error('Failed to override source:', error)
    toast.error(error instanceof Error ? error.message : 'Failed to override source')
  }
}

const deleteVariant = async () => {
  if (!selectedEnvironmentId.value || !variantId.value || !confirm('Delete this variant? This cannot be undone.')) return

  try {
    const success = await deleteVariantApi(variantId.value, selectedEnvironmentId.value)
    if (success) {
      toast.success('Variant has been deleted')
      router.push(`/metrics/${metricId.value}/variants`)
    } else {
      toast.error('Failed to delete variant')
    }
  } catch (error) {
    console.error('Failed to delete variant:', error)
    toast.error(error instanceof Error ? error.message : 'Failed to delete variant')
  }
}

const executeVariantQuery = async () => {
  if (!variantId.value || !selectedEnvironmentId.value) return

  executing.value = true
  executionResults.value = null
  executionTime.value = null

  try {
    const result = await executeVariant({
      variant_id: variantId.value,
      environment_id: selectedEnvironmentId.value
    })

    if (result) {
      executionTime.value = result.metadata.execution_time_ms
      executionResults.value = { success: true, data: result.data, metadata: result.metadata, sql: result.sql }
      toast.success(`Variant executed successfully - ${result.metadata.row_count} rows returned`)
    }
  } catch (error) {
    console.error('Failed to execute variant:', error)
    executionResults.value = {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }
    toast.error(error instanceof Error ? error.message : 'Failed to execute variant')
  } finally {
    executing.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loadVariant()
})

// Watch for environment changes
watch(selectedEnvironmentId, async (newEnvId) => {
  if (newEnvId) {
    await loadVariant()
  }
})
</script>
