<template>
  <div>
    <!-- Table Name -->
    <div v-if="item.configField === 'table_name'" class="space-y-1.5">
      <Label class="text-xs text-muted-foreground">Override Table Name</Label>
      <Input
        :model-value="item.configValue"
        placeholder="e.g., new_table_name"
        class="h-9"
        @update:model-value="emit('update:item', { configValue: $event })"
      />
    </div>

    <!-- Limit -->
    <div v-else-if="item.configField === 'limit'" class="space-y-1.5">
      <Label class="text-xs text-muted-foreground">Override Row Limit</Label>
      <Input
        type="number"
        :model-value="item.configValue"
        placeholder="e.g., 1000"
        class="h-9"
        @update:model-value="emit('update:item', { configValue: $event ? parseInt($event) : undefined })"
      />
    </div>

    <!-- Grouped -->
    <div v-else-if="item.configField === 'grouped'" class="flex items-center justify-between">
      <div class="space-y-0.5">
        <Label class="text-sm">Enable GROUP BY</Label>
        <p class="text-xs text-muted-foreground">Override grouping behavior in query</p>
      </div>
      <Switch
        :checked="item.configValue"
        @update:checked="emit('update:item', { configValue: $event })"
      />
    </div>

    <!-- Ordered -->
    <div v-else-if="item.configField === 'ordered'" class="flex items-center justify-between">
      <div class="space-y-0.5">
        <Label class="text-sm">Enable ORDER BY</Label>
        <p class="text-xs text-muted-foreground">Override ordering behavior in query</p>
      </div>
      <Switch
        :checked="item.configValue"
        @update:checked="emit('update:item', { configValue: $event })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Switch } from '~/components/ui/switch'
import type { OverrideItem } from './types'

interface Props {
  item: OverrideItem
}

defineProps<Props>()

const emit = defineEmits<{
  'update:item': [value: Partial<OverrideItem>]
}>()
</script>
