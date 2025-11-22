<template>
  <Card class="border-0 shadow-none">
    <CardHeader>
      <CardTitle>Query Grouping</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex items-center space-x-2">
        <Switch
          id="use-grouped"
          :model-value="useGrouped"
          @update:model-value="$emit('update:useGrouped', $event)"
        />
        <Label for="use-grouped">Override metric grouping</Label>
      </div>
      
      <div v-if="useGrouped" class="space-y-4">
        <div class="flex items-center space-x-3">
          <Switch
            id="grouped-value"
            :model-value="groupedValue"
            @update:model-value="$emit('update:groupedValue', $event)"
          />
          <Label for="grouped-value">
            {{ groupedValue ? 'Enable grouping' : 'Disable grouping' }}
          </Label>
        </div>
        <div class="text-xs text-muted-foreground">
          <p v-if="groupedValue">
            Results will be grouped by dimensions (applies GROUP BY clause).
          </p>
          <p v-else>
            Results will not be grouped (no GROUP BY clause applied).
          </p>
          <p class="mt-1">
            Current metric setting: <span class="font-medium">{{ metricGrouped ? 'Grouped' : 'Ungrouped' }}</span>
          </p>
        </div>
      </div>
      
      <div v-else class="text-xs text-muted-foreground">
        Using metric's default grouping setting: <span class="font-medium">{{ metricGrouped ? 'Grouped' : 'Ungrouped' }}</span>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'

interface Props {
  useGrouped: boolean
  groupedValue: boolean
  metricGrouped: boolean
}

defineProps<Props>()

defineEmits<{
  'update:useGrouped': [value: boolean]
  'update:groupedValue': [value: boolean]
}>()
</script>
