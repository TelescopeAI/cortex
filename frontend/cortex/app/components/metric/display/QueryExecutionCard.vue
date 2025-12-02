<template>
  <Card>
    <CardHeader>
      <CardTitle>Query Execution</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex gap-4">
        <Button @click="$emit('preview')" :disabled="previewing" class="flex-1">
          <Settings class="h-4 w-4 mr-2" />
          {{ previewing ? 'Generating Query...' : 'Preview Query' }}
        </Button>
        <Button 
          @click="$emit('execute')" 
          :disabled="executing"
          class="flex-1"
        >
          <PlayCircle class="h-4 w-4 mr-2" />
          {{ executing ? 'Executing...' : 'Execute Metric' }}
        </Button>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Settings, PlayCircle } from 'lucide-vue-next'

interface Props {
  previewing: boolean
  executing: boolean
}

defineProps<Props>()

defineEmits<{
  'preview': []
  'execute': []
}>()
</script>

