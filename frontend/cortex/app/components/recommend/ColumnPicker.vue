<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Badge } from '~/components/ui/badge'

interface Column {
  name: string
  type: string
  nullable?: boolean
  primary_key?: boolean
  foreign_key?: boolean
}

interface Props {
  columns: Column[]
  modelValue: string[]
  placeholder?: string
  disabled?: boolean
  tableName?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Select columns',
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const selectedColumns = computed({
  get: () => props.modelValue,
  set: (value: string[]) => emit('update:modelValue', value)
})

const selectedColumnsData = computed(() => {
  return props.columns.filter(col => selectedColumns.value.includes(col.name))
})

function getColumnTypeBadgeClass(type: string, muted: boolean = false): string {
  const typeUpper = type.toUpperCase()

  if (muted) {
    return 'bg-muted text-muted-foreground'
  }

  // Numeric types - blue
  if (/INT|DECIMAL|NUMERIC|FLOAT|DOUBLE|REAL|MONEY/.test(typeUpper)) {
    return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
  }
  // Text types - purple
  if (/CHAR|TEXT|VARCHAR|STRING|CLOB/.test(typeUpper)) {
    return 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
  }
  // Date/Time types - green
  if (/DATE|TIME|TIMESTAMP/.test(typeUpper)) {
    return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
  }
  // Boolean types - amber
  if (/BOOL|BIT/.test(typeUpper)) {
    return 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300'
  }
  // Default - gray
  return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
}

function isColumnSelected(columnName: string): boolean {
  return selectedColumns.value.includes(columnName)
}

// Normalize empty array to all column names for Select component
function normalizeSelection() {
  // If selectedColumns is empty, it means "all selected" by convention
  // But the Select component needs the actual array of all column names
  if (props.modelValue.length === 0 && props.columns.length > 0) {
    const allColumnNames = props.columns.map(col => col.name)
    emit('update:modelValue', allColumnNames)
  }
}

// Normalize on mount
onMounted(() => {
  normalizeSelection()
})

// Normalize when columns change (e.g., switching tables)
watch(() => props.columns, () => {
  normalizeSelection()
}, { immediate: true })
</script>

<template>
  <Select v-model="selectedColumns" multiple :disabled="disabled">
    <SelectTrigger class="size-0 w-full h-fit py-3 grow" size=null>
      <SelectValue :placeholder="placeholder">
        <div v-if="selectedColumnsData.length > 0" class="flex items-center flex-wrap gap-2 py-1">
          <Badge
            v-for="column in selectedColumnsData"
            :key="column.name"
            variant="outline"
            class="flex items-stretch p-0"
          >
            <span class="text-sm px-2 py-1">{{ column.name }}</span>
            <div :class="getColumnTypeBadgeClass(column.type, false)" class="flex items-center px-2 text-[10px]">
              {{ column.type }}
            </div>
          </Badge>
        </div>
      </SelectValue>
    </SelectTrigger>
    <SelectContent>
      <SelectGroup>
        <SelectItem v-for="column in columns" :key="column.name" :value="column.name">
          <div class="flex items-center justify-between w-full gap-2">
            <span :class="{ 'text-muted-foreground': !isColumnSelected(column.name) }">
              {{ column.name }}
            </span>
            <Badge
              :class="getColumnTypeBadgeClass(column.type, !isColumnSelected(column.name))"
              class="text-[10px] px-1.5 py-0.5"
            >
              {{ column.type }}
            </Badge>
          </div>
        </SelectItem>
      </SelectGroup>
    </SelectContent>
  </Select>
</template>
