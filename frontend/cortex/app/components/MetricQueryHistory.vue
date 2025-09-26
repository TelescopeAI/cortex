<template>
  <div class="space-y-6">
    <!-- Header with Refresh Button -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold">Query Execution History</h3>
        <p class="text-sm text-muted-foreground">
          Track all query executions for this metric
        </p>
      </div>
      <Button @click="refreshHistory" variant="outline" size="sm" :disabled="loading">
        <RefreshCw class="w-4 h-4 mr-2" :class="{ 'animate-spin': loading }" />
        Refresh
      </Button>
    </div>

    <!-- Filters -->
    <Card>
      <CardHeader>
        <CardTitle class="text-base">Filters</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="successFilter">Status Filter</Label>
            <Select v-model="filters.success">
              <SelectTrigger>
                <SelectValue placeholder="All executions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All executions</SelectItem>
                <SelectItem value="success">Successful only</SelectItem>
                <SelectItem value="failed">Failed only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="timeRange">Time Range</Label>
            <Select v-model="filters.timeRange">
              <SelectTrigger>
                <SelectValue placeholder="Select time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24 Hours</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Execution Stats -->
    <Card v-if="executionStats">
      <CardHeader>
        <CardTitle class="text-base">Execution Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary">{{ executionStats.total_executions }}</div>
            <div class="text-sm text-muted-foreground">Total</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ executionStats.successful_executions }}</div>
            <div class="text-sm text-muted-foreground">Successful</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-red-600">{{ executionStats.failed_executions }}</div>
            <div class="text-sm text-muted-foreground">Failed</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ executionStats.success_rate }}%</div>
            <div class="text-sm text-muted-foreground">Success Rate</div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Query History Table -->
    <Card>
      <CardHeader>
        <CardTitle class="text-base">Recent Executions</CardTitle>
        <CardDescription>
          Showing {{ paginatedData.length }} of {{ totalCount }} entries
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="loading" class="flex items-center justify-center py-8">
          <div class="flex items-center space-x-2">
            <Loader2 class="h-6 w-6 animate-spin" />
            <span>Loading query history...</span>
          </div>
        </div>

        <div v-else-if="error" class="text-center py-8">
          <div class="text-red-500 mb-2">
            <AlertCircle class="h-8 w-8 mx-auto mb-2" />
            <p class="font-medium">Error loading history</p>
          </div>
          <p class="text-sm text-muted-foreground">{{ error }}</p>
          <Button @click="refreshHistory" variant="outline" size="sm" class="mt-2">
            Try Again
          </Button>
        </div>

        <div v-else-if="queryHistory.length === 0" class="text-center py-8">
          <History class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-medium text-muted-foreground mb-2">No query history</h3>
          <p class="text-sm text-muted-foreground">
            Execute this metric to see query history.
          </p>
        </div>

        <div v-else class="space-y-4">
          <div class="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Executed At</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Cache Mode</TableHead>
                  <TableHead>Rows</TableHead>
                  <TableHead>Query</TableHead>
                  <TableHead class="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="entry in paginatedData" :key="entry.id">
                  <TableCell>
                    <div class="space-y-1">
                      <div class="font-medium">{{ formatDate(entry.executed_at) }}</div>
                      <div class="text-xs text-muted-foreground">{{ formatRelativeTime(entry.executed_at) }}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div class="flex items-center space-x-2">
                      <span class="font-mono">{{ entry.duration.toFixed(2) }}ms</span>
                      <div v-if="entry.duration > 1000" class="text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
                        Slow
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge :variant="entry.success ? 'default' : 'destructive'">
                      {{ entry.success ? 'Success' : 'Failed' }}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{{ entry.cache_mode || 'UNCACHED' }}</Badge>
                  </TableCell>
                  <TableCell>
                    <span class="font-mono">{{ entry.row_count || 0 }}</span>
                  </TableCell>
                  <TableCell>
                    <div class="max-w-xs">
                      <p class="text-sm font-mono truncate" :title="entry.query">
                        {{ truncateQuery(entry.query) }}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" @click="viewQueryDetails(entry)">
                      <Eye class="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <!-- Pagination Controls -->
          <div class="flex items-center justify-between px-2">
            <div class="flex-1 text-sm text-muted-foreground">
              Showing {{ paginatedData.length }} of {{ totalCount }} entries
            </div>
            <div class="flex items-center space-x-6 lg:space-x-8">
              <div class="flex items-center space-x-2">
                <p class="text-sm font-medium">Rows per page</p>
                <Select v-model="pageSize" @update:model-value="(value) => { pageSize = Number(value); currentPage = 1; }">
                  <SelectTrigger class="h-8 w-[70px]">
                    <SelectValue :placeholder="`${pageSize}`" />
                  </SelectTrigger>
                  <SelectContent side="top">
                    <SelectItem v-for="size in [10, 25, 50, 100]" :key="size" :value="size">
                      {{ size }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="flex w-[100px] items-center justify-center text-sm font-medium">
                Page {{ currentPage }} of {{ totalPages }}
              </div>
              <div class="flex items-center space-x-2">
                <Button
                  variant="outline"
                  class="hidden w-8 h-8 p-0 lg:flex"
                  :disabled="currentPage === 1"
                  @click="currentPage = 1"
                >
                  <span class="sr-only">Go to first page</span>
                  <ChevronsLeft class="w-4 h-8" />
                </Button>
                <Button
                  variant="outline"
                  class="w-8 h-8 p-0"
                  :disabled="currentPage === 1"
                  @click="currentPage--"
                >
                  <span class="sr-only">Go to previous page</span>
                  <ChevronLeft class="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  class="w-8 h-8 p-0"
                  :disabled="currentPage >= totalPages"
                  @click="currentPage++"
                >
                  <span class="sr-only">Go to next page</span>
                  <ChevronRight class="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  class="w-8 h-8 p-0"
                  :disabled="currentPage >= totalPages"
                  @click="currentPage = totalPages"
                >
                  <span class="sr-only">Go to last page</span>
                  <ChevronsRight class="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Query Details Dialog -->
    <Dialog v-model:open="showQueryDialog">
      <DialogContent class="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Query Execution Details</DialogTitle>
        </DialogHeader>
        <div v-if="selectedQuery" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <Label class="text-sm font-medium">Execution Time</Label>
              <p class="text-sm">{{ selectedQuery.executed_at }}</p>
            </div>
            <div>
              <Label class="text-sm font-medium">Duration</Label>
              <p class="text-sm">{{ selectedQuery.duration.toFixed(2) }}ms</p>
            </div>
            <div>
              <Label class="text-sm font-medium">Status</Label>
              <Badge :variant="selectedQuery.success ? 'default' : 'destructive'">
                {{ selectedQuery.success ? 'Success' : 'Failed' }}
              </Badge>
            </div>
            <div>
              <Label class="text-sm font-medium">Rows Returned</Label>
              <p class="text-sm">{{ selectedQuery.row_count || 0 }}</p>
            </div>
          </div>
          
          <div v-if="selectedQuery.error_message">
            <Label class="text-sm font-medium text-red-600">Error Message</Label>
            <p class="text-sm text-red-600 bg-red-50 p-3 rounded">{{ selectedQuery.error_message }}</p>
          </div>

          <div>
            <Label class="text-sm font-medium">SQL Query</Label>
            <div class="bg-muted p-3 rounded mt-1">
              <pre class="text-sm font-mono whitespace-pre-wrap">{{ selectedQuery.query }}</pre>
            </div>
          </div>

          <div v-if="selectedQuery.parameters">
            <Label class="text-sm font-medium">Parameters</Label>
            <div class="bg-muted p-3 rounded mt-1">
              <pre class="text-sm font-mono">{{ JSON.stringify(selectedQuery.parameters, null, 2) }}</pre>
            </div>
          </div>

          <div v-if="selectedQuery.meta">
            <Label class="text-sm font-medium">Metadata</Label>
            <div class="bg-muted p-3 rounded mt-1">
              <pre class="text-sm font-mono">{{ JSON.stringify(selectedQuery.meta, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useQueryHistory, type QueryLogEntry } from '~/composables/useQueryHistory'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import { Badge } from '~/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { History, RefreshCw, Loader2, AlertCircle, Eye, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-vue-next'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'


// Props
const props = defineProps<{
  metricId: string
}>()

// Emits
const emit = defineEmits<{
  refresh: []
}>()

// Composables
const { 
  queryHistory, 
  loading, 
  error, 
  totalCount,
  fetchMetricQueryHistory,
  getExecutionStats
} = useQueryHistory()

// Local state
const filters = ref({
  success: 'all' as 'all' | 'success' | 'failed',
  timeRange: '7d'
})

// Prevent infinite loops
const isInitialLoad = ref(true)
const isRefreshing = ref(false)

// Date formatting
const { language } = useNavigatorLanguage()

const convertUTCToLocal = (utcDateString: string) => {
  try {
    const utcDate = new Date(utcDateString)
    const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000)
    return localDate
  } catch (error) {
    console.error('Error converting UTC date:', error)
    return new Date(utcDateString)
  }
}

const executionStats = ref<any>(null)
const showQueryDialog = ref(false)
const selectedQuery = ref<QueryLogEntry | null>(null)

// Pagination state
const currentPage = ref(1)
const pageSize = ref(10)

// Computed paginated data
const paginatedData = computed(() => {
  const startIndex = (currentPage.value - 1) * pageSize.value
  const endIndex = startIndex + pageSize.value
  return queryHistory.value.slice(startIndex, endIndex)
})

const totalPages = computed(() => {
  return Math.ceil(queryHistory.value.length / pageSize.value)
})

// Computed
const hasFilters = computed(() => {
  return filters.value.success !== 'all' || 
         filters.value.timeRange !== '7d'
})

// Methods
const refreshHistory = async () => {
  // Prevent infinite loops
  if (isRefreshing.value) {
    console.log('Already refreshing, skipping...')
    return
  }
  
  isRefreshing.value = true
  console.log('Refreshing query history...')
  
  try {
    await Promise.all([
      fetchMetricQueryHistory(props.metricId, {
        success: filters.value.success === 'all' ? null : filters.value.success === 'success'
      }),
      fetchExecutionStats()
    ])
    // Reset pagination to first page when refreshing
    currentPage.value = 1
    emit('refresh')
  } finally {
    isRefreshing.value = false
  }
}

const fetchExecutionStats = async () => {
  const stats = await getExecutionStats(props.metricId, filters.value.timeRange)
  if (stats) {
    executionStats.value = stats
  }
}

const viewQueryDetails = (query: QueryLogEntry) => {
  selectedQuery.value = query
  showQueryDialog.value = true
}

const truncateQuery = (query: string, maxLength: number = 50) => {
  return query.length > maxLength ? query.substring(0, maxLength) + '...' : query
}

const formatDate = (dateString: string) => {
  // Convert UTC to local timezone before passing to useDateFormat
  const localDate = convertUTCToLocal(dateString)
  return useDateFormat(localDate, 'DD/MM/YYYY', { 
    locales: language.value || 'en-US' 
  })
}

const formatRelativeTime = (dateString: string) => {
  // Convert UTC to local timezone before passing to useTimeAgo
  const localDate = convertUTCToLocal(dateString)
  return useTimeAgo(localDate, { 
    updateInterval: 1000 // Update every second for real-time updates
  })
}

// Watchers - only watch specific filter changes, not the entire object
watch(() => filters.value.success, (newValue, oldValue) => {
  if (newValue !== oldValue) {
    refreshHistory()
  }
})

watch(() => filters.value.timeRange, (newRange, oldRange) => {
  if (newRange !== oldRange) {
    refreshHistory()
  }
})

// Lifecycle
onMounted(async () => {
  await refreshHistory()
  isInitialLoad.value = false
})

// Expose refresh method for parent components
defineExpose({
  refreshHistory
})
</script>
