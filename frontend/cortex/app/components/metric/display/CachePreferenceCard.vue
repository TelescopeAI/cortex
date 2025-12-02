<template>
  <Card class="border-0 shadow-none">
    <CardHeader>
      <CardTitle>Cache Preference</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex items-center space-x-3">
        <Switch 
          id="cache-enabled" 
          :model-value="enabled" 
          @update:model-value="$emit('update:enabled', $event)" 
        />
        <Label for="cache-enabled">Enabled</Label>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="space-y-1">
          <Label for="req-cache-ttl">TTL (seconds)</Label>
          <Input 
            id="req-cache-ttl" 
            type="number" 
            min="1" 
            placeholder="300" 
            @input="(e: any) => $emit('update:ttl', parseInt(e?.target?.value || '0'))" 
          />
          <p class="text-xs text-muted-foreground">Override default cache TTL for this run.</p>
        </div>
      </div>
      <p class="text-xs text-muted-foreground">This overrides the metric default defined in the schema.</p>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'

interface Props {
  enabled: boolean
  ttl?: number
}

defineProps<Props>()

defineEmits<{
  'update:enabled': [value: boolean]
  'update:ttl': [value: number]
}>()
</script>
