<script setup lang="ts">
import { ref, computed, inject, type Ref } from 'vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Table2, BarChart3, FileJson, Info, CheckCircle, XCircle, Database, Eye, Loader2 } from 'lucide-vue-next'
import ExecutionResultTable from './ExecutionResultTable.vue'
import ExecutionResultChart from './ExecutionResultChart.vue'
import ExecutionResultMetadata from './ExecutionResultMetadata.vue'
import CodeHighlight from './CodeHighlight.vue'

interface Props {
  // Existing props (backward compat with variants/create.vue)
  data?: Record<string, any>[]
  metadata?: Record<string, any>

  // Full execution/preview result object
  executionResults?: {
    success: boolean
    data?: Record<string, any>[]
    metadata?: Record<string, any>
    errors?: string[]
  }

  // Query info for Statistics tab
  compiledQuery?: string
  originalQuery?: string

  // Preview mode indicator
  isPreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  metadata: () => ({}),
  isPreview: false,
})

const emit = defineEmits<{
  'execution-result-viewer:copy-query': []
}>()

const activeTab = ref('table')

// Inject loading states from parent (optional)
const executionLoading = inject<Ref<boolean>>('executionLoading', ref(false))
const previewLoading = inject<Ref<boolean>>('previewLoading', ref(false))

const isLoading = computed(() => executionLoading.value || previewLoading.value)
const loadingMessage = computed(() => executionLoading.value ? 'Executing...' : 'Generating preview...')

const hasExecutionResults = computed(() => !!props.executionResults)
const effectiveData = computed(() => props.executionResults?.data ?? props.data ?? [])
const effectiveMetadata = computed(() => props.executionResults?.metadata ?? props.metadata ?? {})
const hasData = computed(() => effectiveData.value.length > 0)
const isSuccess = computed(() => props.executionResults?.success ?? hasData.value)
const executionErrors = computed(() => props.executionResults?.errors ?? [])

// Combined state for rendering decisions
const showLoading = computed(() => isLoading.value)
const showEmpty = computed(() => !isLoading.value && !hasExecutionResults.value)
const showResults = computed(() => !isLoading.value && hasExecutionResults.value)
</script>

<template>
  <Card>
    <CardContent class="space-y-4">
      <!-- Loading State -->
      <div v-if="showLoading" class="flex items-center gap-2 text-sm text-muted-foreground py-8">
        <Loader2 class="h-4 w-4 animate-spin" />
        <span>{{ loadingMessage }}</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="showEmpty" class="text-center py-8 text-muted-foreground">
        <Eye class="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p class="text-sm">Results will appear here automatically as you configure the variant</p>
      </div>

      <!-- Results State -->
      <template v-else-if="showResults">
        <!-- Execution errors -->
        <div v-if="!isSuccess && executionErrors.length > 0" class="space-y-2">
          <h4 class="font-medium text-sm text-red-600">Execution Errors:</h4>
          <div class="space-y-1">
            <div v-for="error in executionErrors" :key="error" class="text-sm text-red-600 bg-red-50 dark:bg-red-950 p-2 rounded">
              {{ error }}
            </div>
          </div>
        </div>

        <!-- Preview mode: show only Statistics -->
        <ExecutionResultMetadata
          v-if="isSuccess && isPreview"
          :metadata="effectiveMetadata"
          :compiled-query="compiledQuery"
          :original-query="originalQuery"
          :is-preview="isPreview"
          @copy-query="emit('execution-result-viewer:copy-query')"
        />

        <!-- Execution mode: data tabs when successful with data -->
        <Tabs v-else-if="isSuccess && hasData" v-model="activeTab" class="w-full">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="table" class="flex items-center gap-2">
            <Table2 class="h-4 w-4" />
            Table
          </TabsTrigger>
          <TabsTrigger value="chart" class="flex items-center gap-2">
            <BarChart3 class="h-4 w-4" />
            Charts
          </TabsTrigger>
          <TabsTrigger value="json" class="flex items-center gap-2">
            <FileJson class="h-4 w-4" />
            JSON
          </TabsTrigger>
          <TabsTrigger value="metadata" class="flex items-center gap-2">
            <Info class="h-4 w-4" />
            Metadata
          </TabsTrigger>
        </TabsList>

        <TabsContent value="table" class="mt-4 min-w-0">
          <ExecutionResultTable :data="effectiveData" />
        </TabsContent>

        <TabsContent value="chart" class="mt-4">
          <ExecutionResultChart :data="effectiveData" />
        </TabsContent>

        <TabsContent value="json" class="mt-4">
          <Card>
            <CardContent>
              <CodeHighlight
                lang="json"
                :code="JSON.stringify({ data: effectiveData, metadata: effectiveMetadata }, null, 2)"
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metadata" class="mt-4">
          <ExecutionResultMetadata
            :metadata="effectiveMetadata"
            :compiled-query="compiledQuery"
            :original-query="originalQuery"
            :is-preview="isPreview"
            @copy-query="emit('execution-result-viewer:copy-query')"
          />
        </TabsContent>
      </Tabs>

      <!-- No data state (execution mode only) -->
      <div v-else-if="isSuccess && !hasData" class="text-center py-8">
        <Database class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-medium text-muted-foreground mb-2">No data returned</h3>
        <p class="text-sm text-muted-foreground">
          The query executed successfully but returned no results.
        </p>
      </div>
      </template>
    </CardContent>
  </Card>
</template>
