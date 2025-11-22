<template>
  <Card v-if="executionResults">
    <CardHeader>
      <CardTitle class="flex items-center space-x-2">
        <CheckCircle v-if="executionResults.success" class="h-5 w-5 text-green-500" />
        <XCircle v-else class="h-5 w-5 text-red-500" />
        <span>Execution Results</span>
        <Badge :variant="executionResults.success ? 'default' : 'destructive'">
          {{ executionResults.success ? 'Success' : 'Failed' }}
        </Badge>
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <!-- Show errors if execution failed -->
      <div v-if="!executionResults.success && executionResults.errors && executionResults.errors.length > 0" class="space-y-2">
        <h4 class="font-medium text-sm text-red-600">Execution Errors:</h4>
        <div class="space-y-1">
          <div v-for="error in executionResults.errors" :key="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
            {{ error }}
          </div>
        </div>
      </div>
      
      <!-- Show data if execution was successful -->
      <div v-if="executionResults.success && executionResults.data">
        <ExecutionResultViewer :data="executionResults.data || []" :metadata="executionResults.metadata || {}" />
      </div>
      
      <!-- Show message if no data returned -->
      <div v-if="executionResults.success && (!executionResults.data || executionResults.data.length === 0)" class="text-center py-8">
        <Database class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-medium text-muted-foreground mb-2">No data returned</h3>
        <p class="text-sm text-muted-foreground">
          The query executed successfully but returned no results.
        </p>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { CheckCircle, XCircle, Database } from 'lucide-vue-next'
import ExecutionResultViewer from '~/components/ExecutionResultViewer.vue'

interface Props {
  executionResults: any
}

defineProps<Props>()
</script>
