<template>
  <Card>
    <CardHeader>
      <CardTitle>Basic Information</CardTitle>
    </CardHeader>
    <CardContent class="space-y-6">
      <!-- Status and Model -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="space-y-2">
          <div class="text-sm font-medium text-muted-foreground">Status</div>
          <Badge :variant="getStatusBadgeVariant(metricStatus)" class="capitalize">
            {{ metricStatus }} 
          </Badge>
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-muted-foreground">Parent Model</div>
          <Button 
            variant="link" 
            class="p-0 h-auto text-sm justify-start"
            @click="$emit('model-click')"
          >
            📁 {{ parentModel?.name || 'Unknown Model' }}
          </Button>
        </div>
        <div class="space-y-2">
          <div class="text-sm font-medium text-muted-foreground">Visibility</div>
          <Badge variant="outline">
            {{ metric.public ? '🌐 Public' : '🔒 Private' }}
          </Badge>
        </div>
      </div>

      <Separator />

      <!-- Names and Identifiers -->
      <div v-if="metric.alias" class="flex items-center justify-start">
          <div class="text-sm font-medium text-muted-foreground">Alias</div>
          <div class="text-sm font-mono p-2 rounded">{{ metric.alias }}</div>
        </div>

      <!-- Grouping Configuration -->
      <div class="space-y-2">
        <div class="text-sm font-medium text-muted-foreground">Grouping Configuration</div>
        <div class="flex items-center space-x-2">
          <Badge :variant="metric.grouped ? 'default' : 'secondary'">
            {{ metric.grouped ? '📊 Grouped' : '📋 Ungrouped' }}
          </Badge>
          <span class="text-sm text-muted-foreground">
            {{ metric.grouped ? 'Results will be grouped by dimensions' : 'Results will not be grouped' }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <div v-if="metric.description" class="space-y-2">
        <div class="text-sm font-medium text-muted-foreground">Description</div>
        <p class="text-sm">{{ metric.description }}</p>
      </div>

      <!-- Parameters -->
      <div v-if="hasParameters" class="space-y-2">
        <div class="text-sm font-medium text-muted-foreground">Parameters</div>
        <div class="space-y-2">
          <div 
            v-for="param in metric.parameters" 
            :key="param.name"
            class="flex items-center justify-between p-3 bg-muted rounded"
          >
            <div class="space-y-1">
              <div class="font-medium text-sm">{{ param.name }}</div>
              <div class="text-xs text-muted-foreground">
                {{ param.type }}{{ param.required ? ' (required)' : ' (optional)' }}
              </div>
              <div v-if="param.description" class="text-xs text-muted-foreground">
                {{ param.description }}
              </div>
            </div>
            <div v-if="param.default_value !== undefined" class="text-xs text-muted-foreground">
              Default: {{ param.default_value }}
            </div>
          </div>
        </div>
      </div>

      <!-- Timestamps -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div class="space-y-1">
          <div class="text-muted-foreground">Created</div>
          <div class="space-y-1">
            <div>{{ formatAbsoluteDate(metric.created_at) }}</div>
            <div class="text-xs text-muted-foreground">{{ formatRelativeTime(metric.created_at) }}</div>
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-muted-foreground">Last Updated</div>
          <div class="space-y-1">
            <div>{{ formatAbsoluteDate(metric.updated_at) }}</div>
            <div class="text-xs text-muted-foreground">{{ formatRelativeTime(metric.updated_at) }}</div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Separator } from '~/components/ui/separator'

interface Props {
  metric: any
  parentModel: any
  metricStatus: string
  formatRelativeTime: (date: string | Date) => any
  formatAbsoluteDate: (date: string | Date) => any
  getStatusBadgeVariant: (status: string) => 'default' | 'destructive' | 'outline' | 'secondary' | null | undefined
}

const props = defineProps<Props>()

defineEmits<{
  'model-click': []
}>()

const hasParameters = computed(() => {
  return props.metric?.parameters && Array.isArray(props.metric.parameters) && props.metric.parameters.length > 0
})
</script>
