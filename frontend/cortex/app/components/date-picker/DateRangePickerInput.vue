<script setup lang="ts">
import { computed } from 'vue'
import { useDateFormat } from '@vueuse/core'
import { CalendarIcon } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { RangeCalendar } from '~/components/ui/range-calendar'
import { Popover, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { cn } from '~/lib/utils'
import type { DateRange } from 'reka-ui'

interface Props {
  modelValue?: DateRange
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Pick a date range'
})

const emit = defineEmits<{
  'update:modelValue': [value: DateRange | undefined]
}>()

const dateRange = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Format helper for display
const formatDateRange = computed(() => {
  if (!props.modelValue?.start) return props.placeholder
  
  const startDate = props.modelValue.start.toDate('UTC')
  const startFormatted = useDateFormat(startDate, 'MMM D, YYYY').value
  
  if (!props.modelValue.end) return startFormatted
  
  const endDate = props.modelValue.end.toDate('UTC')
  const endFormatted = useDateFormat(endDate, 'MMM D, YYYY').value
  return `${startFormatted} - ${endFormatted}`
})
</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        :class="cn(
          'w-full justify-start text-left font-normal',
          !dateRange && 'text-muted-foreground'
        )"
      >
        <CalendarIcon class="mr-2 h-4 w-4" />
        <span>{{ formatDateRange }}</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0">
      <RangeCalendar v-model="dateRange" />
    </PopoverContent>
  </Popover>
</template>
