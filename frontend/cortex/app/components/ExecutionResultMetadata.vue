<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Copy } from 'lucide-vue-next'
import CodeHighlight from './CodeHighlight.vue'

interface Props {
  metadata?: Record<string, any>
  compiledQuery?: string
  originalQuery?: string
  isPreview?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  metadata: () => ({}),
  isPreview: false,
})

const emit = defineEmits<{
  'copy-query': []
}>()

const displayQuery = computed(() => props.compiledQuery || props.metadata?.query)
const hasErrors = computed(() => !!props.metadata?.errors)
</script>

<template>
  <Card>
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

      <!-- Compiled / Generated Query -->
      <div v-if="displayQuery" class="space-y-1">
        <div class="flex items-center gap-2">
          <div class="text-muted-foreground">Generated Query</div>
          <Badge v-if="hasErrors" variant="destructive">Invalid</Badge>
          <Badge v-else variant="default">Valid</Badge>
          <Button variant="outline" size="sm" class="ml-auto h-7" @click="emit('copy-query')">
            <Copy class="h-3.5 w-3.5 mr-1.5" />
            Copy
          </Button>
        </div>
        <CodeHighlight lang="sql" :code="displayQuery" />
      </div>

      <!-- Original Query -->
      <div v-if="originalQuery && originalQuery !== displayQuery" class="space-y-1">
        <div class="text-muted-foreground">Original Query</div>
        <CodeHighlight lang="sql" :code="originalQuery" />
      </div>

      <!-- Parameters -->
      <div v-if="metadata.parameters && Object.keys(metadata.parameters).length > 0" class="space-y-1">
        <div class="text-muted-foreground">Parameters</div>
        <div class="p-2 bg-muted rounded font-mono text-xs overflow-x-auto">
          <pre>{{ JSON.stringify(metadata.parameters, null, 2) }}</pre>
        </div>
      </div>

      <!-- Errors -->
      <div v-if="metadata.errors" class="space-y-1">
        <div class="text-destructive">Errors</div>
        <div class="p-2 bg-destructive/10 rounded text-destructive font-mono text-xs overflow-x-auto">
          <pre>{{ metadata.errors }}</pre>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
