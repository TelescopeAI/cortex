<template>
  <Card 
    class="hover:shadow-2xl hover:shadow-blue-400/40 hover:border-blue-400
           hover:drop-shadow-2xl hover:inset-shadow-blue-900
          h-80 lg:h-40 justify-between
           transition-shadow cursor-pointer gap-0"
    @click="$emit('click')"
  >
    <CardHeader class="">
      <div class="flex flex-col items-start justify-between gap-y-2">
        <div class="space-y-1 flex-1">
          <CardTitle class="text-xl font-extrabold text-indigo-900 dark:text-white font-medium">{{ metric.title || metric.name }}</CardTitle>
          
        </div>
        <p v-if="metric.description"
        class="text-sm line-clamp-2 text-blue-600 dark:text-blue-200"
        :class="{ 'text-blue-600 dark:text-blue-200': metric.description, 'text-muted-foreground': !metric.description }"
        >
            {{ metric.description || '' }}
          </p>
      </div>
    </CardHeader>
    
    <CardContent class="pt-0">
      <div class="space-y-3">
        
        <div class="flex flex-col md:flex-row items-center justify-between">
          <div class="flex flex-row justify-start items-center gap-x-2">
            <FolderOpen class="h-3 w-3" />
            <span class="text-sm text-muted-foreground">{{ metric.data_model_name || 'Unknown Model' }}</span>
          </div>
          <span class="text-xs text-lime-700 dark:text-lime-300">
            Updated {{ formatRelativeTime(metric.updated_at) }}
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

