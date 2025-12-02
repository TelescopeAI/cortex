<template>
  <Card 
    class="hover:shadow-md transition-shadow cursor-pointer"
    @click="$emit('click')"
  >
    <CardHeader class="pb-3">
      <div class="flex items-start justify-between">
        <div class="space-y-1 flex-1">
          <CardTitle class="text-base font-medium">{{ model.name }}</CardTitle>
          <p class="text-sm text-muted-foreground line-clamp-2">
            {{ model.description || 'No description available' }}
          </p>
        </div>
        <Badge :variant="getStatusBadgeVariant(model.is_valid)" class="ml-2">
          {{ getStatusIcon(model.is_valid) }} {{ getStatusText(model.is_valid) }}
        </Badge>
      </div>
    </CardHeader>
    
    <CardContent class="pt-0">
      <div class="space-y-3">
        <!-- Model Info -->
        <div class="flex items-center justify-between text-sm">
          <div class="flex items-center space-x-2 text-muted-foreground">
            <span>📊</span>
            <span>Data Model</span>
          </div>
          <span class="text-muted-foreground">v{{ model.version }}</span>
        </div>
        
        <!-- Metrics Count -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-1 text-sm text-muted-foreground">
            <Target class="h-3 w-3" />
            <span>{{ model.metrics_count || 0 }} metrics</span>
          </div>
          <span class="text-xs text-muted-foreground">
            {{ formatRelativeTime(model.updated_at) }}
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
import { Target } from 'lucide-vue-next'

interface Props {
  model: {
    id: string
    name: string
    description?: string
    is_valid?: boolean
    version: number
    metrics_count?: number
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

const getStatusBadgeVariant = (isValid?: boolean) => {
  if (isValid === true) return 'default'
  if (isValid === false) return 'destructive'
  return 'secondary'
}

const getStatusIcon = (isValid?: boolean) => {
  if (isValid === true) return '✅'
  if (isValid === false) return '⚠️'
  return '🔄'
}

const getStatusText = (isValid?: boolean) => {
  if (isValid === true) return 'Valid'
  if (isValid === false) return 'Invalid'
  return 'Pending'
}
</script>

