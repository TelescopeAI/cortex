<script setup lang="ts">
import { computed } from 'vue'
import { ChevronUp, ChevronDown, X } from 'lucide-vue-next'
import type { Transform, TransformFunction } from '~/types/conditionals'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '~/components/ui/select'
import TransformParams from './TransformParams.vue'

interface Props {
  modelValue: Transform
  index: number
  total: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: Transform]
  'remove': []
  'move-up': []
  'move-down': []
}>()

const transform = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const updateFunction = (func: TransformFunction) => {
  emit('update:modelValue', { 
    ...transform.value, 
    function: func,
    // Reset params when function changes
    params: {}
  })
}

const updateParams = (params: Record<string, any>) => {
  emit('update:modelValue', { ...transform.value, params })
}

const requiresParams = (func: TransformFunction): boolean => {
  return ['COALESCE', 'ROUND', 'EXTRACT', 'CAST', 'CONCAT', 'SUBSTRING', 'DATE_TRUNC', 'DATE_PART'].includes(func)
}
</script>

<template>
  <div class="transform-pill flex items-center gap-2 p-2 border rounded-lg bg-card">
    <!-- Reorder Buttons -->
    <div class="flex flex-col gap-1">
      <Button 
        variant="ghost" 
        size="icon"
        class="h-6 w-6"
        :disabled="index === 0"
        @click="emit('move-up')"
      >
        <ChevronUp class="h-3 w-3" />
      </Button>
      <Button 
        variant="ghost" 
        size="icon"
        class="h-6 w-6"
        :disabled="index === total - 1"
        @click="emit('move-down')"
      >
        <ChevronDown class="h-3 w-3" />
      </Button>
    </div>

    <!-- Transform Function Selector -->
    <Select :model-value="transform.function" @update:model-value="updateFunction" class="flex-1">
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <!-- String Functions -->
        <SelectGroup>
          <SelectLabel>String Functions</SelectLabel>
          <SelectItem value="COALESCE">COALESCE (handle nulls)</SelectItem>
          <SelectItem value="LOWER">LOWER (to lowercase)</SelectItem>
          <SelectItem value="UPPER">UPPER (to uppercase)</SelectItem>
          <SelectItem value="CONCAT">CONCAT (join strings)</SelectItem>
          <SelectItem value="TRIM">TRIM (remove spaces)</SelectItem>
          <SelectItem value="SUBSTRING">SUBSTRING (extract text)</SelectItem>
        </SelectGroup>

        <!-- Math Functions -->
        <SelectGroup>
          <SelectLabel>Math Functions</SelectLabel>
          <SelectItem value="ROUND">ROUND (round number)</SelectItem>
          <SelectItem value="ABS">ABS (absolute value)</SelectItem>
          <SelectItem value="CEIL">CEIL (round up)</SelectItem>
          <SelectItem value="FLOOR">FLOOR (round down)</SelectItem>
        </SelectGroup>

        <!-- Date Functions -->
        <SelectGroup>
          <SelectLabel>Date Functions</SelectLabel>
          <SelectItem value="EXTRACT">EXTRACT (get date part)</SelectItem>
          <SelectItem value="DATE_TRUNC">DATE_TRUNC (truncate date)</SelectItem>
          <SelectItem value="DATE_PART">DATE_PART (get date part)</SelectItem>
        </SelectGroup>

        <!-- Type Conversion -->
        <SelectGroup>
          <SelectLabel>Type Conversion</SelectLabel>
          <SelectItem value="CAST">CAST (convert type)</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>

    <!-- Parameters (conditional based on function) -->
    <TransformParams 
      v-if="requiresParams(transform.function)"
      :model-value="transform.params || {}"
      @update:model-value="updateParams"
      :function="transform.function"
    />

    <!-- Remove Button -->
    <Button variant="ghost" size="icon" class="h-8 w-8" @click="emit('remove')">
      <X class="h-4 w-4" />
    </Button>
  </div>
</template>

