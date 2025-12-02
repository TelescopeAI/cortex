<script setup lang="ts">
import { computed } from 'vue'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '~/components/ui/select'
import type { TransformFunction } from '~/types/conditionals'
import TransformParams from './TransformParams.vue'

interface Props {
  modelValue: 'column' | 'function'
  selectedFunction?: TransformFunction
  functionParams?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'column'
})

const emit = defineEmits<{
  'update:modelValue': [value: 'column' | 'function']
  'update:selectedFunction': [value: TransformFunction]
  'update:functionParams': [value: Record<string, any>]
}>()

const conditionType = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedFunction = computed({
  get: () => props.selectedFunction || 'LOWER',
  set: (val) => emit('update:selectedFunction', val)
})

const functionParams = computed({
  get: () => props.functionParams || {},
  set: (val) => emit('update:functionParams', val)
})

const requiresParams = (func: TransformFunction): boolean => {
  return ['COALESCE', 'ROUND', 'EXTRACT', 'CAST', 'CONCAT', 'SUBSTRING', 'DATE_TRUNC', 'DATE_PART'].includes(func)
}
</script>

<template>
  <div class="space-y-3">
    <!-- Condition Type Selector -->
    <div class="flex items-center gap-2">
      <Label class="text-xs font-semibold">Type</Label>
      <Select v-model="conditionType">
        <SelectTrigger class="w-[180px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="column">Column Condition</SelectItem>
          <SelectItem value="function">Function</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Function Selector (if type is function) -->
    <div v-if="conditionType === 'function'" class="space-y-2">
      <Label class="text-xs font-semibold">Function</Label>
      <Select v-model="selectedFunction">
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
      
      <!-- Function parameters if needed -->
      <TransformParams 
        v-if="requiresParams(selectedFunction)"
        v-model="functionParams"
        :function="selectedFunction"
      />
    </div>
  </div>
</template>
