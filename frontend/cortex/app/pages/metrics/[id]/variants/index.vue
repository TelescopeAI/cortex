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
            {{ metric?.title || metric?.name || 'Metric' }}
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <BreadcrumbPage>Variants</BreadcrumbPage>
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>

    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div class="space-y-1">
        <h1 class="text-3xl font-bold tracking-tight flex items-center gap-2">
          <GitBranch class="h-8 w-8 text-purple-600 dark:text-purple-400" />
          Metric Variants
        </h1>
        <p class="text-muted-foreground">
          {{ variants.length }} variant{{ variants.length !== 1 ? 's' : '' }}
          derived from <span class="font-medium">{{ metric?.title || metric?.name }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="refreshVariants">
          <RefreshCw :class="{ 'animate-spin': loading }" class="h-4 w-4 mr-2" />
          Refresh
        </Button>
        <Button @click="createNewVariant">
          <Plus class="h-4 w-4 mr-2" />
          New Variant
        </Button>
      </div>
    </div>

    <!-- Search and Filters -->
    <Card>
      <CardHeader>
        <CardTitle class="text-lg">Search & Filter</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center gap-4">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              placeholder="Search variants by name or description..."
              class="w-full"
            >
              <template #prefix>
                <Search class="h-4 w-4 text-muted-foreground" />
              </template>
            </Input>
          </div>
          <div class="flex items-center gap-2">
            <Label class="text-sm text-muted-foreground">Visibility:</Label>
            <Select v-model="visibilityFilter">
              <SelectTrigger class="w-[150px]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="public">Public</SelectItem>
                <SelectItem value="private">Private</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Variants List -->
    <div v-if="loading && variants.length === 0" class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div v-for="i in 6" :key="i" class="h-40 rounded-lg border bg-card animate-pulse"></div>
    </div>

    <div v-else-if="filteredVariants.length === 0 && !loading" class="text-center py-12">
      <Card>
        <CardContent class="pt-6">
          <GitBranch class="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
          <h3 class="text-lg font-semibold mb-2">No variants found</h3>
          <p class="text-muted-foreground mb-4">
            {{ searchQuery ? 'Try adjusting your search terms' : 'Create your first variant to get started' }}
          </p>
          <Button @click="createNewVariant">
            <Plus class="h-4 w-4 mr-2" />
            Create First Variant
          </Button>
        </CardContent>
      </Card>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <MetricVariantsListCard
        v-for="variant in filteredVariants"
        :key="variant.id"
        :variant="variant"
        :source-metric-name="metric?.name"
        @click="navigateToVariant(variant.id)"
      />
    </div>

    <!-- Create Variant Dialog -->
    <MetricVariantsFormDialog
      :open="createDialogOpen"
      :default-source-metric-id="metricId"
      @update:open="createDialogOpen = $event"
      @success="handleVariantCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { GitBranch, Plus, Search } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Label } from '~/components/ui/label'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator
} from '~/components/ui/breadcrumb'
import type { SemanticMetricVariant } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

const route = useRoute()
const router = useRouter()
const metricId = computed(() => route.params.id as string)

const { selectedEnvironmentId } = useEnvironments()
const { getVariantsForMetric, loading } = useMetricVariants()
const { getMetric } = useMetrics()

// State
const variants = ref<SemanticMetricVariant[]>([])
const metric = ref<SemanticMetric | null>(null)
const searchQuery = ref('')
const visibilityFilter = ref('all')
const createDialogOpen = ref(false)

// Computed
const filteredVariants = computed(() => {
  let filtered = variants.value

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(v =>
      v.name.toLowerCase().includes(query) ||
      v.description?.toLowerCase().includes(query) ||
      v.alias?.toLowerCase().includes(query)
    )
  }

  // Apply visibility filter
  if (visibilityFilter.value !== 'all') {
    const isPublic = visibilityFilter.value === 'public'
    filtered = filtered.filter(v => v.public === isPublic)
  }

  return filtered
})

// Methods
const loadVariants = async () => {
  if (!selectedEnvironmentId.value || !metricId.value) return

  const result = await getVariantsForMetric(metricId.value, selectedEnvironmentId.value)
  variants.value = result
}

const loadMetric = async () => {
  if (!selectedEnvironmentId.value || !metricId.value) return

  const result = await getMetric(metricId.value, selectedEnvironmentId.value)
  metric.value = result
}

const refreshVariants = async () => {
  await loadVariants()
}

const createNewVariant = () => {
  createDialogOpen.value = true
}

const handleVariantCreated = async (variant: SemanticMetricVariant) => {
  await loadVariants()
  navigateToVariant(variant.id)
}

const navigateToVariant = (variantId: string) => {
  router.push(`/metrics/${metricId.value}/variants/${variantId}`)
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadMetric(),
    loadVariants()
  ])
})

// Watch for environment changes
watch(selectedEnvironmentId, async (newEnvId) => {
  if (newEnvId) {
    await Promise.all([
      loadMetric(),
      loadVariants()
    ])
  }
})
</script>
