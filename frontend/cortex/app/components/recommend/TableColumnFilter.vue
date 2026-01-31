<script setup lang="ts">
import { RotateCcw, Check, X } from 'lucide-vue-next'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import ColumnPicker from './ColumnPicker.vue'

interface Column {
  name: string
  type: string
  nullable?: boolean
  primary_key?: boolean
  foreign_key?: boolean
}

interface Table {
  name: string
  columns: Column[]
}

interface TableSelection {
  excluded: boolean
  selectedColumns: string[]
}

interface Props {
  table: Table
  modelValue: TableSelection
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: TableSelection]
}>()

const selection = computed({
  get: () => props.modelValue,
  set: (value: TableSelection) => emit('update:modelValue', value)
})

const selectedColumns = computed({
  get: () => selection.value.selectedColumns,
  set: (value: string[]) => {
    emit('update:modelValue', {
      ...selection.value,
      selectedColumns: value
    })
  }
})

function toggleExcluded() {
  emit('update:modelValue', {
    ...selection.value,
    excluded: !selection.value.excluded
  })
}

function resetColumns() {
  // Reset to all column names (not empty array)
  const allColumnNames = props.table.columns.map(col => col.name)
  emit('update:modelValue', {
    ...selection.value,
    selectedColumns: allColumnNames
  })
}

const columnCountText = computed(() => {
  const total = props.table.columns.length
  const selected = selection.value.selectedColumns.length

  // If all columns are selected
  if (selected === total) {
    return 'All columns selected'
  }

  return `${selected}/${total} ${selected === 1 ? 'column' : 'columns'} selected`
})
</script>

<template>
  <div
    class="border rounded-lg p-4 space-y-3 transition-opacity"
    :class="{ 'opacity-50': selection.excluded }"
  >
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          class="h-6 w-6"
          @click="toggleExcluded"
        >
          <Check
            v-if="!selection.excluded"
            class="w-4 h-4 text-green-600 dark:text-green-400"
          />
          <X
            v-else
            class="w-4 h-4 text-red-600 dark:text-red-400"
          />
        </Button>
        <span class="font-medium text-center">{{ table.name }}</span>
        <Badge v-if="!selection.excluded" variant="secondary" class="text-xs">
          {{ columnCountText }}
        </Badge>
      </div>
    </div>

    <div class="space-y-2">
      <div v-if="!selection.excluded"
           class="flex items-center justify-start space-x-2">
        <Label  class="text-sm text-muted-foreground">Columns</Label>
        <Button
          v-if="selectedColumns.length > 0 && selectedColumns.length < table.columns.length"
          variant="ghost"
          size="sm"
          @click="resetColumns"
          class="h-7 px-2"
        >
          <RotateCcw class="w-3 h-3 mr-1" />
        </Button>
      </div>
      <ColumnPicker
        v-if="!selection.excluded"
        v-model="selectedColumns"
        :columns="table.columns"
        :table-name="table.name"
        :disabled="selection.excluded"
        :placeholder="
          selection.excluded
            ? 'Table excluded'
            : selectedColumns.length === table.columns.length
              ? 'All columns'
              : `${selectedColumns.length} of ${table.columns.length} columns`
        "
      />
    </div>
  </div>
</template>
