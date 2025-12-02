<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Target, BarChart3, Users, Database, ArrowRight, Loader2, Clock } from 'lucide-vue-next'
import { useWorkspaces } from '~/composables/useWorkspaces'
import { useEnvironments } from '~/composables/useEnvironments'
import { useMetrics } from '~/composables/useMetrics'
import { useDashboards } from '~/composables/useDashboards'
import { useConsumers } from '~/composables/useConsumers'
import { useDataSources } from '~/composables/useDataSources'
import DynamicGreeting from '~/components/DynamicGreeting.vue'

// Page metadata
definePageMeta({
  title: 'Home',
  layout: 'default'
})

const router = useRouter()
const { selectedWorkspaceId, workspaces } = useWorkspaces()
const { selectedEnvironmentId, environments } = useEnvironments()

// Get composables for data fetching
const { metrics, loading: metricsLoading, fetchMetrics } = useMetrics()
const { dashboards, loading: dashboardsLoading, fetchDashboards } = useDashboards()
const { consumers, loading: consumersLoading, fetchConsumers } = useConsumers()
const { dataSources, loading: dataSourcesLoading, refresh: refreshDataSources } = useDataSources()

// Computed values for counts
const metricsCount = computed(() => metrics.value?.length || 0)
const dashboardsCount = computed(() => dashboards.value?.length || 0)
const consumersCount = computed(() => consumers.value?.length || 0)
const dataSourcesCount = computed(() => dataSources.value?.length || 0)

// Overall loading state
const isLoading = computed(() => metricsLoading.value || dashboardsLoading.value || consumersLoading.value || dataSourcesLoading.value)

// Recent items (sorted by updated_at, then created_at, limit to 5)
const recentMetrics = computed(() => {
  if (!Array.isArray(metrics.value)) return []
  return [...metrics.value]
    .sort((a, b) => {
      const aDate = new Date(a.updated_at || a.created_at || 0).getTime()
      const bDate = new Date(b.updated_at || b.created_at || 0).getTime()
      return bDate - aDate
    })
    .slice(0, 5)
})

const recentDashboards = computed(() => {
  if (!Array.isArray(dashboards.value)) return []
  return [...dashboards.value]
    .sort((a, b) => {
      const aDate = new Date(a.updated_at || a.created_at || 0).getTime()
      const bDate = new Date(b.updated_at || b.created_at || 0).getTime()
      return bDate - aDate
    })
    .slice(0, 5)
})

const recentConsumers = computed(() => {
  if (!Array.isArray(consumers.value)) return []
  return [...consumers.value]
    .sort((a, b) => {
      const aDate = new Date(a.updated_at || a.created_at || 0).getTime()
      const bDate = new Date(b.updated_at || b.created_at || 0).getTime()
      return bDate - aDate
    })
    .slice(0, 5)
})

const recentDataSources = computed(() => {
  if (!Array.isArray(dataSources.value)) return []
  return [...dataSources.value]
    .sort((a, b) => {
      const aDate = new Date(a.updated_at || a.created_at || 0).getTime()
      const bDate = new Date(b.updated_at || b.created_at || 0).getTime()
      return bDate - aDate
    })
    .slice(0, 5)
})

// Calculate card order based on counts
// When starting out all count would be 0: Data Sources > Metrics > Dashboards > Consumers
// If at least 1 Data Source exists: Metrics > Dashboards > Consumers > Data Sources
// If at least 1 Data Source and 1 Metric exists: Dashboards > Metrics > Consumers > Data Sources
// If at least 1 Data Source, 1 Metric and 1 Dashboard exists: Dashboards > Metrics > Consumers > Data Sources
const cardOrder = computed(() => {
  // If no data sources exist (starting state)
  if (dataSourcesCount.value === 0) {
    return {
      dataSources: 1,
      metrics: 2,
      dashboards: 3,
      consumers: 4
    }
  }
  
  // If at least 1 data source exists but no metrics
  if (metricsCount.value === 0) {
    return {
      metrics: 1,
      dashboards: 2,
      consumers: 3,
      dataSources: 4
    }
  }
  
  // If at least 1 data source AND at least 1 metric (regardless of dashboard count)
  // Dashboards > Metrics > Consumers > Data Sources
  return {
    dashboards: 1,
    metrics: 2,
    consumers: 3,
    dataSources: 4
  }
})

// Get selected workspace and environment names
const selectedWorkspace = computed(() => {
  if (!Array.isArray(workspaces.value)) return null
  return workspaces.value.find(w => w.id === selectedWorkspaceId.value)
})

const selectedEnvironment = computed(() => {
  if (!Array.isArray(environments.value)) return null
  return environments.value.find(e => e.id === selectedEnvironmentId.value)
})

// Fetch all data on mount
onMounted(async () => {
  if (selectedEnvironmentId.value) {
    await Promise.all([
      fetchMetrics(selectedEnvironmentId.value),
      fetchDashboards(selectedEnvironmentId.value),
      fetchConsumers(),
      refreshDataSources()
    ])
  }
})

// Watch for environment changes and refetch
watch(selectedEnvironmentId, async (newEnvId) => {
  if (newEnvId) {
    await Promise.all([
      fetchMetrics(newEnvId),
      fetchDashboards(newEnvId),
      fetchConsumers(),
      refreshDataSources()
    ])
  }
})
</script>

<template>
  <div class="container mx-auto px-4 py-8 max-w-7xl">
    <!-- Hero Section -->
    <div class="mb-8">
      <DynamicGreeting />
      <p class="text-muted-foreground text-lg">
        <span v-if="!selectedWorkspace && !selectedEnvironment">
          Select a workspace and environment to get started
        </span>
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground" />
    </div>

    <!-- Stats Grid -->
    <div v-else class="flex flex-col gap-y-6">
      <!-- Metrics Card -->
      <Card 
        class="hover:shadow hover:border hover:drop-shadow hover:text-fuchsia-600 dark:hover:text-fuchsia-400 hover:fill-fuchsia-600 dark:hover:fill-fuchsia-400"
        :class="[`order-${cardOrder.metrics}`]"
      >
        <CardHeader class="pb-4 flex flex-row items-start justify-between space-y-0">
          <div class="flex items-center gap-3 flex-1">
            <div class="">
              <Target class="w-5 h-5"/>
            </div>
            <div>
              <CardTitle class="text-lg">Metrics</CardTitle>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              class="group w-full hover:bg-fuchsia-600 dark:hover:bg-fuchsia-600 hover:text-white flex items-center justify-between cursor-pointer"
              @click="router.push('/metrics')"
            >
              <span class="font-extrabold text-md">{{ metricsCount }}</span>
              <ArrowRight class="w-4 h-4 text-black dark:text-white hidden group-hover:block group-hover:text-white" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="pt-0">
          <div v-if="recentMetrics.length > 0" class="gap-2 flex flex-wrap">
            <div v-for="metric in recentMetrics"
            :key="metric.id" class="flex flex-wrap gap-2 bg-white dark:bg-slate-900 rounded-md">
              <Button
                variant="ghost"
                class="px-2.5 py-1.5 text-xs rounded-md border text-black dark:text-white cursor-pointer hover:text-fuchsia-600 dark:hover:text-fuchsia-400 hover:shadow-sm"
                @click.stop="router.push(`/metrics/${metric.id}`)"
              >
                {{ metric.name || metric.alias || metric.title }}
              </Button>
            </div>
          </div>
          <div v-else class="text-xs text-muted-foreground py-2">
            No metrics yet. Create your first metric to get started.
          </div>
        </CardContent>
      </Card>

      <!-- Dashboards Card -->
      <Card 
        class="hover:shadow hover:border hover:drop-shadow hover:text-indigo-600 dark:hover:text-indigo-400 hover:fill-indigo-600 dark:hover:fill-indigo-400"
        :class="[`order-${cardOrder.dashboards}`]"
      >
        <CardHeader class="pb-4 flex flex-row items-start justify-between space-y-0">
          <div class="flex items-center gap-3 flex-1">
            <div class="">
              <BarChart3 class="w-5 h-5"/>
            </div>
            <div>
              <CardTitle class="text-lg">Dashboards</CardTitle>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              class="group w-full hover:bg-indigo-600 dark:hover:bg-indigo-600 hover:text-white flex items-center justify-between cursor-pointer"
              @click="router.push('/dashboards')"
            >
              <span class="font-extrabold text-md">{{ dashboardsCount }}</span>
              <ArrowRight class="w-4 h-4 text-black dark:text-white hidden group-hover:block group-hover:text-white" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="pt-0">
          <div v-if="recentDashboards.length > 0" class="gap-2 flex flex-wrap">
            <div v-for="dashboard in recentDashboards"
            :key="dashboard.id" class="flex flex-wrap gap-2 bg-white dark:bg-slate-900 rounded-md">
              <Button
                variant="ghost"
                class="px-2.5 py-1.5 text-xs rounded-md border text-black dark:text-white cursor-pointer hover:text-indigo-600 dark:hover:text-indigo-400 hover:shadow-sm"
                @click.stop="router.push(`/dashboards/${dashboard.id}`)"
              >
                {{ dashboard.name || dashboard.alias }}
              </Button>
            </div>
          </div>
          <div v-else class="text-xs text-muted-foreground py-2">
            No dashboards yet. Create your first dashboard to get started.
          </div>
        </CardContent>
      </Card>

      <!-- Consumers Card -->
      <Card 
        class="hover:shadow hover:border hover:drop-shadow hover:text-yellow-600 dark:hover:text-yellow-300 hover:fill-yellow-600 dark:hover:fill-yellow-300"
        :class="[`order-${cardOrder.consumers}`]"
      >
        <CardHeader class="pb-4 flex flex-row items-start justify-between space-y-0">
          <div class="flex items-center gap-3 flex-1">
            <div class="">
              <Users class="w-5 h-5"/>
            </div>
            <div>
              <CardTitle class="text-lg">Consumers</CardTitle>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              class="group w-full hover:bg-yellow-600 dark:hover:bg-yellow-600 hover:text-white flex items-center justify-between cursor-pointer"
              @click="router.push('/consumers')"
            >
              <span class="font-extrabold text-md">{{ consumersCount }}</span>
              <ArrowRight class="w-4 h-4 text-black dark:text-white hidden group-hover:block group-hover:text-white" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="pt-0">
          <div v-if="recentConsumers.length > 0" class="gap-2 flex flex-wrap">
            <div v-for="consumer in recentConsumers"
            :key="consumer.id" class="flex flex-wrap gap-2 bg-white dark:bg-slate-900 rounded-md">
              <Button
                variant="ghost"
                class="px-2.5 py-1.5 text-xs rounded-md border text-black dark:text-white cursor-pointer hover:text-yellow-600 dark:hover:text-yellow-300 hover:shadow-sm"
                @click.stop="router.push(`/consumers/${consumer.id}`)"
              >
                {{ consumer.first_name }} {{ consumer.last_name }} ({{ consumer.email }})
              </Button>
            </div>
          </div>
          <div v-else class="text-xs text-muted-foreground py-2">
            No consumers yet. Create your first consumer to get started.
          </div>
        </CardContent>
      </Card>

      <!-- Data Sources Card -->
      <Card 
        class="hover:shadow hover:border hover:drop-shadow hover:text-green-600 dark:hover:text-green-400 hover:fill-green-600 dark:hover:fill-green-400"
        :class="[`order-${cardOrder.dataSources}`]"
      >
        <CardHeader class="pb-4 flex flex-row items-start justify-between space-y-0">
          <div class="flex items-center gap-3 flex-1">
            <div class="">
              <Database class="w-5 h-5"/>
            </div>
            <div>
              <CardTitle class="text-lg">Data Sources</CardTitle>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <Button 
              variant="outline" 
              size="sm"
              class="group w-full hover:bg-green-600 dark:hover:bg-green-600 hover:text-white flex items-center justify-between cursor-pointer"
              @click="router.push('/data/sources')"
            >
              <span class="font-extrabold text-md">{{ dataSourcesCount }}</span>
              <ArrowRight class="w-4 h-4 text-black dark:text-white hidden group-hover:block group-hover:text-white" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="pt-0">
            <div v-if="recentDataSources.length > 0" class="gap-2 flex flex-wrap">
            <div v-for="dataSource in recentDataSources"
            :key="dataSource.id" class="flex flex-wrap gap-2 bg-white dark:bg-slate-900 rounded-md">
              <Button
                variant="ghost"
                class="px-2.5 py-1.5 text-xs rounded-md border text-black dark:text-white cursor-pointer hover:text-green-600 dark:hover:text-green-400 hover:shadow-sm"
                @click.stop="router.push(`/data/sources/${dataSource.id}`)"
              >
                {{ dataSource.name || dataSource.alias }}
              </Button>
            </div>
          </div>
          <div v-else class="text-xs text-muted-foreground py-2">
            No data sources yet. Create your first data source to get started.
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Empty State -->
    <div v-if="!isLoading && !selectedWorkspaceId && !selectedEnvironmentId" class="text-center py-12">
      <p class="text-muted-foreground text-lg">Please select a workspace and environment to view statistics</p>
    </div>
  </div>
</template> 
