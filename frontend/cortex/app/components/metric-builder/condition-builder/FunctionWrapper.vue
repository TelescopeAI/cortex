<script setup lang="ts">
import { inject, computed } from 'vue'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '~/components/ui/select'
import TransformParams from '../TransformParams.vue'

interface Props {
  modelValue?: string
  functionParams?: Record<string, any>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:functionParams': [value: Record<string, any>]
}>()

// Get context from parent
const context = inject('conditionContext', {
  wrapInFunction: (func: any, params?: any) => {},
  removeFunction: () => {}
})

const selectedFunction = computed({
  get: () => props.modelValue || 'LOWER',
  set: (val) => emit('update:modelValue', val)
})

const functionParams = computed({
  get: () => props.functionParams || {},
  set: (val) => emit('update:functionParams', val)
})

const requiresParams = (func: string): boolean => {
  return ['COALESCE', 'ROUND', 'EXTRACT', 'CAST', 'CONCAT', 'SUBSTRING', 'DATE_TRUNC', 'DATE_PART'].includes(func)
}

const updateFunction = (func: string) => {
  selectedFunction.value = func
  context.wrapInFunction(func as any, functionParams.value)
}

const updateParams = (params: Record<string, any>) => {
  functionParams.value = params
  context.wrapInFunction(selectedFunction.value as any, params)
}
</script>

<template>
  <div class="space-y-2">
    <Label class="text-xs font-semibold">Function</Label>
    <Select :model-value="selectedFunction" @update:model-value="(value) => updateFunction(String(value))">
      <SelectTrigger>
        <SelectValue placeholder="Select function" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>String Functions</SelectLabel>
          <SelectItem value="COALESCE">COALESCE (handle nulls)</SelectItem>
          <SelectItem value="LOWER">LOWER (to lowercase)</SelectItem>
          <SelectItem value="UPPER">UPPER (to uppercase)</SelectItem>
          <SelectItem value="CONCAT">CONCAT (join strings)</SelectItem>
          <SelectItem value="TRIM">TRIM (remove spaces)</SelectItem>
          <SelectItem value="SUBSTRING">SUBSTRING (extract text)</SelectItem>
        </SelectGroup>
        <SelectGroup>
          <SelectLabel>Math Functions</SelectLabel>
          <SelectItem value="ROUND">ROUND (round number)</SelectItem>
          <SelectItem value="ABS">ABS (absolute value)</SelectItem>
          <SelectItem value="CEIL">CEIL (round up)</SelectItem>
          <SelectItem value="FLOOR">FLOOR (round down)</SelectItem>
        </SelectGroup>
        <SelectGroup>
          <SelectLabel>Date Functions</SelectLabel>
          <SelectItem value="EXTRACT">EXTRACT (get date part)</SelectItem>
          <SelectItem value="DATE_TRUNC">DATE_TRUNC (truncate date)</SelectItem>
          <SelectItem value="DATE_PART">DATE_PART (get date part)</SelectItem>
        </SelectGroup>
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
      :function="selectedFunction as any"
      @update:model-value="updateParams"
    />
  </div>
</template>
