<template>
  <div class="space-y-4">
    <!-- Table Selection -->
    <div class="space-y-2">
      <Label for="table-name">Source Table</Label>
      <Select :model-value="tableName" @update:model-value="(value) => $emit('update:tableName', value as string)">
        <SelectTrigger>
          <SelectValue placeholder="Select a table" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem
            v-for="table in availableTables"
            :key="table.name"
            :value="table.name"
          >
            {{ table.name }}
          </SelectItem>
        </SelectContent>
      </Select>
      <p class="text-xs text-muted-foreground">
        Choose the primary table for your metric data
      </p>
    </div>

    <!-- Data Source -->
    <div class="space-y-2">
      <Label for="data-source">Data Source Alias</Label>
      <Input
        id="data-source"
        :model-value="dataSource"
        @update:model-value="(value) => $emit('update:dataSource', value as string)"
        placeholder="default"
      />
      <p class="text-xs text-muted-foreground">
        Alias for the data source connection (usually 'default')
      </p>
    </div>

    <!-- Custom Query -->
    <div class="space-y-2">
      <Label for="custom-query">Custom SQL Query (Optional)</Label>
      <Textarea
        id="custom-query"
        :model-value="query"
        @update:model-value="(value) => $emit('update:query', value as string)"
        placeholder="SELECT * FROM your_table WHERE condition..."
        rows="8"
        class="font-mono text-sm"
      />
      <p class="text-xs text-muted-foreground">
        Provide a custom SQL query to override table-based generation. This will take precedence over the selected table.
      </p>
    </div>

    <!-- Info Alert -->
    <div class="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div>
          <h4 class="text-sm font-medium text-blue-800 dark:text-blue-200">
            Table vs Custom Query
          </h4>
          <p class="mt-1 text-sm text-blue-700 dark:text-blue-300">
            If you specify a custom query, it will be used instead of the selected table. 
            The table selection helps with column discovery for measures and dimensions.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

interface Props {
  tableName?: string
  query?: string
  dataSource?: string
  availableTables?: Array<{ name: string; columns: any[] }>
}

defineProps<Props>()
defineEmits<{
  'update:tableName': [value: string]
  'update:query': [value: string]
  'update:dataSource': [value: string]
}>()
</script> 