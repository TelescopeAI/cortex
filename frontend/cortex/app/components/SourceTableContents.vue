<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useDataSources } from '~/composables/useDataSources'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Textarea } from '~/components/ui/textarea'
import { Skeleton } from '~/components/ui/skeleton'
import { Alert, AlertDescription } from '~/components/ui/alert'
import { Badge } from '~/components/ui/badge'
import { RefreshCw, Play, AlertCircle } from 'lucide-vue-next'
import ExecutionResultTable from '~/components/ExecutionResultTable.vue'
import type { DataSourceQueryResponse } from '~/types'

interface Props {
  dataSourceId: string
  tableName: string
}

const props = defineProps<Props>()

const { queryDataSource } = useDataSources()

const loading = ref(false)
const result = ref<DataSourceQueryResponse | null>(null)
const viewAll = ref(false)
const customMode = ref(false)
const customStatement = ref('')

async function fetchTableData() {
  loading.value = true
  result.value = null

  try {
    if (customMode.value && customStatement.value.trim()) {
      result.value = await queryDataSource(props.dataSourceId, {
        statement: customStatement.value.trim(),
      })
    } else {
      const params: { table: string; limit?: number } = { table: props.tableName }
      if (!viewAll.value) params.limit = 100
      result.value = await queryDataSource(props.dataSourceId, params)
    }
  } catch (err: any) {
    result.value = {
      success: false,
      data: null,
      rowCount: 0,
      query: '',
      duration: 0,
      error: err.message || 'Failed to query data source',
    }
  } finally {
    loading.value = false
  }
}

function handleRefresh() {
  fetchTableData()
}

function handleExecuteCustom() {
  if (customStatement.value.trim()) {
    fetchTableData()
  }
}

watch(viewAll, () => {
  if (!customMode.value) {
    fetchTableData()
  }
})

watch(customMode, (isCustom) => {
  if (!isCustom) {
    fetchTableData()
  }
})

onMounted(() => {
  fetchTableData()
})
</script>

<template>
  <div class="space-y-4 pt-2">
    <!-- Controls Row -->
    <div class="flex items-center justify-between">
      <!-- Left: Stats -->
      <div class="flex items-center gap-2">
        <template v-if="result && result.success">
          <Badge variant="secondary">{{ result.rowCount }} rows</Badge>
          <Badge variant="outline">{{ result.duration }} ms</Badge>
          <code class="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded max-w-xs truncate">
            {{ result.query }}
          </code>
        </template>
      </div>

      <!-- Right: Controls -->
      <div class="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          :disabled="loading"
          @click="handleRefresh"
        >
          <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" />
        </Button>

        <div class="flex items-center gap-2">
          <Switch id="view-all" v-model="viewAll" :disabled="customMode" />
          <Label for="view-all" class="text-sm">View All</Label>
        </div>

        <div class="flex items-center gap-2">
          <Switch id="custom-mode" v-model="customMode" />
          <Label for="custom-mode" class="text-sm">Custom</Label>
        </div>
      </div>
    </div>

    <!-- Custom SQL Area -->
    <div v-if="customMode" class="flex gap-2">
      <Textarea
        v-model="customStatement"
        :placeholder="`SELECT * FROM ${tableName} WHERE ...`"
        class="font-mono text-sm"
        rows="3"
      />
      <Button
        :disabled="loading || !customStatement.trim()"
        @click="handleExecuteCustom"
        class="self-end"
      >
        <Play class="h-4 w-4 mr-2" />
        Execute
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-3">
      <Skeleton class="h-8 w-full" />
      <Skeleton class="h-8 w-full" />
      <Skeleton class="h-8 w-full" />
      <Skeleton class="h-8 w-3/4" />
    </div>

    <!-- Error State -->
    <Alert v-else-if="result && !result.success" variant="destructive">
      <AlertCircle class="h-4 w-4" />
      <AlertDescription>{{ result.error }}</AlertDescription>
    </Alert>

    <!-- Data Table -->
    <ExecutionResultTable
      v-else-if="result && result.success && result.data && result.data.length > 0"
      :data="result.data"
    />

    <!-- Empty State -->
    <div v-else-if="result && result.success && (!result.data || result.data.length === 0)" class="text-center py-8">
      <p class="text-sm text-muted-foreground">No data returned.</p>
    </div>
  </div>
</template>
