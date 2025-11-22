<script setup lang="ts">
import { computed } from 'vue'
import { Plus } from 'lucide-vue-next'
import type { ColumnField, Transform } from '~/types/conditionals'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import TransformPill from './TransformPill.vue'

interface Props {
  modelValue: ColumnField
  availableTables: string[]
  availableColumns: Record<string, string[]>
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: ColumnField]
}>()

const field = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const updateTable = (table: string) => {
  emit('update:modelValue', { 
    ...field.value, 
    table,
    column: '' // Reset column when table changes
  })
}

const updateColumn = (column: string) => {
  emit('update:modelValue', { ...field.value, column })
}

const getAvailableColumns = (): string[] => {
  if (field.value.table && props.availableColumns[field.value.table]) {
    return props.availableColumns[field.value.table]
  }
  
  // If only one table, return its columns
  if (props.availableTables.length === 1) {
    return props.availableColumns[props.availableTables[0]] || []
  }
  
  // Otherwise, return all columns from all tables
  return Object.values(props.availableColumns).flat()
}

const addTransform = () => {
  const transforms = field.value.transforms || []
  emit('update:modelValue', {
    ...field.value,
    transforms: [...transforms, { function: 'COALESCE', params: {} }]
  })
}

const removeTransform = (index: number) => {
  const transforms = [...(field.value.transforms || [])]
  transforms.splice(index, 1)
  emit('update:modelValue', { ...field.value, transforms })
}

const updateTransform = (index: number, transform: Transform) => {
  const transforms = [...(field.value.transforms || [])]
  transforms[index] = transform
  emit('update:modelValue', { ...field.value, transforms })
}

const moveTransform = (index: number, direction: number) => {
  const transforms = [...(field.value.transforms || [])]
  const newIndex = index + direction
  
  if (newIndex >= 0 && newIndex < transforms.length) {
    const temp = transforms[index]
    transforms[index] = transforms[newIndex]
    transforms[newIndex] = temp
    emit('update:modelValue', { ...field.value, transforms })
  }
}
</script>

<template>
  <div class="column-field-builder space-y-3">
    <!-- Column Selection -->
    <div class="flex gap-2">
      <!-- Table Selector (if multiple tables) -->
      <Select 
        v-if="availableTables.length > 1"
        :model-value="field.table"
        @update:model-value="updateTable"
      >
        <SelectTrigger class="w-40">
          <SelectValue placeholder="Table" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem 
            v-for="table in availableTables" 
            :key="table"
            :value="table"
          >
            {{ table }}
          </SelectItem>
        </SelectContent>
      </Select>

      <!-- Column Selector -->
      <Select :model-value="field.column" @update:model-value="updateColumn">
        <SelectTrigger class="flex-1">
          <SelectValue placeholder="Select column" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem
            v-for="column in getAvailableColumns()"
            :key="column"
            :value="column"
          >
            {{ column }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Transform Pipeline -->
    <div v-if="field.column" class="transform-pipeline">
      <div class="flex items-center justify-between mb-2">
        <Label class="text-xs text-muted-foreground">Transform Pipeline</Label>
        <Button variant="ghost" size="sm" @click="addTransform">
          <Plus class="h-3 w-3 mr-1" />
          Add Transform
        </Button>
      </div>

      <!-- Visual Pipeline Display -->
      <div v-if="field.transforms && field.transforms.length > 0" class="space-y-2">
        <TransformPill
          v-for="(transform, index) in field.transforms"
          :key="index"
          :model-value="transform"
          @update:model-value="updateTransform(index, $event)"
          :index="index"
          :total="field.transforms.length"
          @remove="removeTransform(index)"
          @move-up="moveTransform(index, -1)"
          @move-down="moveTransform(index, 1)"
        />
      </div>
      
      <p v-else class="text-xs text-muted-foreground italic">
        No transforms applied
      </p>
    </div>
  </div>
</template>

