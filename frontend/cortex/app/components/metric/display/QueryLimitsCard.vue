<template>
  <Card class="border-0 shadow-none">
    <CardHeader>
      <CardTitle>Query Limits</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex items-center space-x-2">
        <Switch
          id="use-limit"
          :model-value="useLimit"
          @update:model-value="$emit('update:useLimit', $event)"
        />
        <Label for="use-limit">Enable custom limit and offset</Label>
      </div>
      
      <div v-if="useLimit" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="limit-value">Limit</Label>
            <Input
              id="limit-value"
              :model-value="limitValue"
              @update:model-value="$emit('update:limitValue', $event)"
              type="number"
              min="1"
              max="10000"
              placeholder="100"
            />
            <div class="text-xs text-muted-foreground">
              Maximum number of rows to return (1-10,000)
            </div>
          </div>
          
          <div class="space-y-2">
            <Label for="offset-value">Offset</Label>
            <Input
              id="offset-value"
              :model-value="offsetValue"
              @update:model-value="$emit('update:offsetValue', $event)"
              type="number"
              min="0"
              placeholder="0"
            />
            <div class="text-xs text-muted-foreground">
              Number of rows to skip (0+)
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'

interface Props {
  useLimit: boolean
  limitValue: number
  offsetValue: number
}

defineProps<Props>()

defineEmits<{
  'update:useLimit': [value: boolean]
  'update:limitValue': [value: number]
  'update:offsetValue': [value: number]
}>()
</script>
