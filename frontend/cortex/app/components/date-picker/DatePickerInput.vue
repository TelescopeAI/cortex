<script setup lang="ts">
import { computed } from 'vue'
import { useDateFormat } from '@vueuse/core'
import { CalendarIcon } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Calendar } from '~/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { cn } from '~/lib/utils'
import type { DateValue } from 'reka-ui'
import { CalendarDate, toCalendarDate, fromDate } from '@internationalized/date'

interface Props {
  modelValue?: any // Can be Date, DateValue, or string
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Pick a date'
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

// Convert to DateValue for Calendar component
const dateValue = computed<DateValue | undefined>({
  get: () => {
    if (!props.modelValue) return undefined
    if (props.modelValue instanceof Date) {
      return fromDate(props.modelValue, 'UTC')
    }
    return props.modelValue
  },
  set: (val) => {
    if (!val) {
      emit('update:modelValue', undefined)
      return
    }
    // Convert DateValue to Date for parent
    const date = val.toDate('UTC')
    emit('update:modelValue', date)
  }
})

const formattedDate = computed(() => {
  if (!props.modelValue) return props.placeholder
  const date = props.modelValue instanceof Date ? props.modelValue : props.modelValue.toDate?.('UTC')
  return date ? useDateFormat(date, 'MMM D, YYYY').value : props.placeholder
})
</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <Button
        variant="outline"
        :class="cn(
          'w-full justify-start text-left font-normal',
          !dateValue && 'text-muted-foreground'
        )"
      >
        <CalendarIcon class="mr-2 h-4 w-4" />
        <span>{{ formattedDate }}</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent class="w-auto p-0">
      <Calendar v-model="dateValue" />
    </PopoverContent>
  </Popover>
</template>
