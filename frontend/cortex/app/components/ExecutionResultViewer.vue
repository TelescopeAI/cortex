<script setup lang="ts">
import { ref } from 'vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table2, BarChart3, FileJson } from 'lucide-vue-next'
import ExecutionResultTable from './ExecutionResultTable.vue'
import ExecutionResultChart from './ExecutionResultChart.vue'
import CodeHighlight from './CodeHighlight.vue'

const props = defineProps({
  data: {
    type: Array as () => Record<string, any>[],
    required: true,
  },
  metadata: {
    type: Object as () => Record<string, any>,
    default: () => ({}),
  },
})

const activeTab = ref('table')
</script>

<template>
  <div v-if="data && data.length > 0">
    <Card class="mb-4">
      <CardHeader>
        <CardTitle>Execution Metadata</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4 text-sm">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="space-y-1">
            <div class="text-muted-foreground">Execution Time</div>
            <div class="font-medium">{{ metadata.duration?.toFixed(2) || 'N/A' }} ms</div>
          </div>
          <div class="space-y-1">
            <div class="text-muted-foreground">Row Count</div>
            <div class="font-medium">{{ metadata.row_count ?? 'N/A' }}</div>
          </div>
        </div>
        <div v-if="metadata.query" class="space-y-1">
          <div class="text-muted-foreground">Query</div>
          <CodeHighlight lang="sql" :code="metadata.query" />
        </div>
        <div v-if="metadata.parameters && Object.keys(metadata.parameters).length > 0" class="space-y-1">
          <div class="text-muted-foreground">Parameters</div>
          <div class="p-2 bg-muted rounded font-mono text-xs overflow-x-auto">
            <pre>{{ JSON.stringify(metadata.parameters, null, 2) }}</pre>
          </div>
        </div>
        <div v-if="metadata.errors" class="space-y-1">
          <div class="text-destructive">Errors</div>
          <div class="p-2 bg-destructive/10 rounded text-destructive font-mono text-xs overflow-x-auto">
            <pre>{{ metadata.errors }}</pre>
          </div>
        </div>
      </CardContent>
    </Card>
    <div>
    </div>
    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-3">
        <TabsTrigger value="table" class="flex items-center gap-2">
          <Table2 class="h-4 w-4" />
          Table View
        </TabsTrigger>
        <TabsTrigger value="chart" class="flex items-center gap-2">
          <BarChart3 class="h-4 w-4" />
          Chart View
        </TabsTrigger>
        <TabsTrigger value="json" class="flex items-center gap-2">
          <FileJson class="h-4 w-4" />
          JSON View
        </TabsTrigger>
      </TabsList>
      
      <TabsContent value="table" class="mt-4 min-w-0">
        <ExecutionResultTable :data="data" />
      </TabsContent>
      
      <TabsContent value="chart" class="mt-4">
        <ExecutionResultChart :data="data" />
      </TabsContent>
      
      <TabsContent value="json" class="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Network Response</CardTitle>
          </CardHeader>
          <CardContent>
            <CodeHighlight 
              lang="json" 
              :code="JSON.stringify({ data, metadata }, null, 2)" 
            />
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
  <div v-else class="text-center py-8">
    <p class="text-sm text-muted-foreground">No data returned.</p>
  </div>
</template>
