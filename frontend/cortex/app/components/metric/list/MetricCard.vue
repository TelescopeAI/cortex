<template>
  <Card 
    class="hover:shadow-md transition-shadow cursor-pointer"
    @click="$emit('click')"
  >
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between">
        <div class="space-y-1 flex-1">
          <CardTitle class="text-base font-medium">{{ metric.title || metric.name }}</CardTitle>
          <p class="text-sm text-muted-foreground line-clamp-2">
            {{ metric.description || 'No description available' }}
          </p>
        </div>
        <div class="flex flex-col items-end space-y-1">
          <Badge :variant="getStatusBadgeVariant(metric.status)">
            {{ getStatusIcon(metric.status) }} {{ metric.status || 'valid' }}
          </Badge>
          <Badge v-if="metric.public" variant="secondary" class="text-xs">Public</Badge>
        </div>
      </div>
    </CardHeader>
    
    <CardContent class="pt-0">
      <div class="space-y-3">
        <!-- Metric Info -->
        <div class="flex items-center justify-between text-sm">
          <div class="flex items-center space-x-2 text-muted-foreground">
            <FolderOpen class="h-3 w-3" />
            <span>{{ metric.data_model_name || 'Unknown Model' }}</span>
          </div>
          <span class="text-muted-foreground">{{ metric.alias || metric.name }}</span>
        </div>
        
        <!-- Parameters -->
        <div v-if="metric.parameters && metric.parameters.length > 0" class="flex items-center space-x-1 text-sm text-muted-foreground">
          <Settings class="h-3 w-3" />
          <span>{{ metric.parameters.length }} parameters</span>
        </div>
        
        <div class="flex items-center justify-between">
          <span class="text-xs text-muted-foreground">
            {{ formatRelativeTime(metric.updated_at) }}
          </span>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { FolderOpen, Settings } from 'lucide-vue-next'

interface Props {
  metric: {
    id: string
    name: string
    title?: string
    alias?: string
    description?: string
    data_model_name?: string
    public: boolean
    status?: string
    parameters?: any[]
    updated_at: string
  }
}

defineProps<Props>()

defineEmits<{
  'click': []
}>()

const { language } = useNavigatorLanguage()

const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

const formatRelativeTime = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, { 
    updateInterval: 1000
  })
}

const getStatusBadgeVariant = (status?: string) => {
  switch (status) {
    case 'valid': return 'default'
    case 'invalid': return 'destructive'
    case 'pending': return 'secondary'
    default: return 'outline'
  }
}

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'valid': return '✅'
    case 'invalid': return '⚠️'
    case 'pending': return '🔄'
    default: return '❓'
  }
}
</script>

