<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ComparisonOperator } from '~/types/conditionals'
import { Input } from '~/components/ui/input'

interface Props {
  modelValue: any | any[]
  operator: ComparisonOperator
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: any | any[]]
}>()

// Determine input type based on operator
const isSingleValue = computed(() => {
  return ['=', '!=', '>', '<', '>=', '<=', 'LIKE'].includes(props.operator)
})

const isListValue = computed(() => {
  return ['IN', 'NOT IN'].includes(props.operator)
})

const isRangeValue = computed(() => {
  return props.operator === 'BETWEEN'
})

const isNullCheck = computed(() => {
  return ['IS NULL', 'IS NOT NULL'].includes(props.operator)
})

// For single value
const value = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// For list values (IN, NOT IN)
const valuesString = ref('')

// Initialize valuesString from modelValue
watch(() => props.modelValue, (newVal) => {
  if (Array.isArray(newVal)) {
    valuesString.value = newVal.join(', ')
  }
}, { immediate: true })

const parseValues = () => {
  if (!valuesString.value) {
    emit('update:modelValue', [])
    return
  }
  
  // Split by comma and trim whitespace
  const values = valuesString.value
    .split(',')
    .map(v => v.trim())
    .filter(v => v.length > 0)
  
  emit('update:modelValue', values)
}

// For range values (BETWEEN)
const range = computed({
  get: () => {
    if (Array.isArray(props.modelValue) && props.modelValue.length === 2) {
      return props.modelValue
    }
    return [null, null]
  },
  set: (val) => emit('update:modelValue', val)
})

const updateRangeMin = (val: any) => {
  emit('update:modelValue', [val, range.value[1]])
}

const updateRangeMax = (val: any) => {
  emit('update:modelValue', [range.value[0], val])
}
</script>

<template>
  <!-- Single value input (=, !=, >, <, >=, <=, LIKE) -->
  <Input 
    v-if="isSingleValue"
    v-model="value"
    placeholder="Value"
    class="flex-1"
  />

  <!-- Multi-value input (IN, NOT IN) -->
  <div v-else-if="isListValue" class="flex-1 space-y-1">
    <Input
      v-model="valuesString"
      placeholder="Enter values (comma-separated)"
      @blur="parseValues"
    />
    <p class="text-xs text-muted-foreground">
      Separate multiple values with commas
    </p>
  </div>

  <!-- Range input (BETWEEN) -->
  <div v-else-if="isRangeValue" class="flex gap-2 items-center">
    <Input 
      :model-value="range[0]" 
      @update:model-value="updateRangeMin"
      placeholder="Min" 
      class="w-24" 
    />
    <span class="text-xs text-muted-foreground">and</span>
    <Input 
      :model-value="range[1]"
      @update:model-value="updateRangeMax"
      placeholder="Max" 
      class="w-24" 
    />
  </div>

  <!-- No input (IS NULL, IS NOT NULL) -->
  <span v-else-if="isNullCheck" class="text-sm text-muted-foreground italic">
    (no value needed)
  </span>
</template>

