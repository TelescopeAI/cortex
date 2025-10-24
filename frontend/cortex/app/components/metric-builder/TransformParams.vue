<script setup lang="ts">
import { computed } from 'vue'
import type { TransformFunction } from '~/types/conditionals'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'

interface Props {
  modelValue: Record<string, any>
  function: TransformFunction
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

const params = computed({
  get: () => props.modelValue || {},
  set: (val) => emit('update:modelValue', val)
})

const updateParam = (key: string, value: any) => {
  emit('update:modelValue', { ...params.value, [key]: value })
}
</script>

<template>
  <!-- For COALESCE -->
  <Input 
    v-if="props.function === 'COALESCE'"
    :model-value="params.fallback"
    @update:model-value="updateParam('fallback', $event)"
    placeholder="Fallback value"
    class="w-32"
  />

  <!-- For ROUND -->
  <Input 
    v-if="props.function === 'ROUND'"
    :model-value="params.decimals"
    @update:model-value="updateParam('decimals', typeof $event === 'string' ? parseInt($event) || 0 : $event)"
    type="number"
    placeholder="Decimals"
    class="w-24"
    min="0"
    max="10"
  />

  <!-- For EXTRACT -->
  <Select 
    v-if="props.function === 'EXTRACT'"
    :model-value="params.part"
    @update:model-value="updateParam('part', $event)"
  >
    <SelectTrigger class="w-32">
      <SelectValue placeholder="Part" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="YEAR">Year</SelectItem>
      <SelectItem value="MONTH">Month</SelectItem>
      <SelectItem value="DAY">Day</SelectItem>
      <SelectItem value="DOW">Day of Week</SelectItem>
      <SelectItem value="HOUR">Hour</SelectItem>
    </SelectContent>
  </Select>

  <!-- For CONCAT -->
  <Input 
    v-if="props.function === 'CONCAT'"
    :model-value="params.separator"
    @update:model-value="updateParam('separator', $event)"
    placeholder="Separator (optional)"
    class="w-32"
  />

  <!-- For SUBSTRING -->
  <div v-if="props.function === 'SUBSTRING'" class="flex gap-2">
    <Input 
      :model-value="params.start"
      @update:model-value="updateParam('start', typeof $event === 'string' ? (parseInt($event) || 1) : $event)"
      type="number"
      placeholder="Start position"
      class="w-24"
      min="1"
    />
    <Input 
      :model-value="params.length"
      @update:model-value="updateParam('length', typeof $event === 'string' ? parseInt($event) : $event)"
      type="number"
      placeholder="Length (optional)"
      class="w-24"
    />
  </div>

  <!-- For DATE_TRUNC -->
  <Select 
    v-if="props.function === 'DATE_TRUNC'"
    :model-value="params.unit"
    @update:model-value="updateParam('unit', $event)"
  >
    <SelectTrigger class="w-32">
      <SelectValue placeholder="Unit" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="year">Year</SelectItem>
      <SelectItem value="month">Month</SelectItem>
      <SelectItem value="day">Day</SelectItem>
      <SelectItem value="hour">Hour</SelectItem>
      <SelectItem value="minute">Minute</SelectItem>
    </SelectContent>
  </Select>

  <!-- For DATE_PART -->
  <Select 
    v-if="props.function === 'DATE_PART'"
    :model-value="params.part"
    @update:model-value="updateParam('part', $event)"
  >
    <SelectTrigger class="w-32">
      <SelectValue placeholder="Part" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="YEAR">Year</SelectItem>
      <SelectItem value="MONTH">Month</SelectItem>
      <SelectItem value="DAY">Day</SelectItem>
      <SelectItem value="DOW">Day of Week</SelectItem>
      <SelectItem value="HOUR">Hour</SelectItem>
      <SelectItem value="MINUTE">Minute</SelectItem>
      <SelectItem value="SECOND">Second</SelectItem>
    </SelectContent>
  </Select>

  <!-- For CAST -->
  <Select 
    v-if="props.function === 'CAST'"
    :model-value="params.type"
    @update:model-value="updateParam('type', $event)"
  >
    <SelectTrigger class="w-32">
      <SelectValue placeholder="Type" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="TEXT">Text</SelectItem>
      <SelectItem value="INTEGER">Integer</SelectItem>
      <SelectItem value="DECIMAL">Decimal</SelectItem>
      <SelectItem value="DATE">Date</SelectItem>
      <SelectItem value="TIMESTAMP">Timestamp</SelectItem>
    </SelectContent>
  </Select>
</template>

