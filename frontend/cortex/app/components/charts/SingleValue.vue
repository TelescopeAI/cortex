<script setup lang="ts">
import { computed } from 'vue'

interface SingleValueConfig {
  number_format?: 'integer' | 'decimal' | 'percentage' | 'currency' | 'abbreviated' | 'scientific'
  prefix?: string
  suffix?: string
  show_title?: boolean
  show_description?: boolean
  compact_mode?: boolean
}

const props = withDefaults(defineProps<{
  title?: string
  description?: string
  value: number | string | null | undefined
  config?: SingleValueConfig
}>(), {
  title: 'Value',
  description: '',
  config: () => ({ number_format: 'decimal' })
})

const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) return 'N/A'
  const cfg = props.config || {}
  const num = typeof props.value === 'number' ? props.value : Number(props.value)
  let out = ''
  if (cfg.prefix) out += cfg.prefix
  switch (cfg.number_format) {
    case 'integer': out += Math.round(num).toLocaleString(); break
    case 'decimal': out += num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); break
    case 'percentage': out += (num * 100).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%'; break
    case 'currency': out += new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(num); break
    case 'abbreviated': out += abbreviateNumber(num); break
    case 'scientific': out += num.toExponential(2); break
    default: out += num.toLocaleString();
  }
  if (cfg.suffix) out += cfg.suffix
  return out
})

function abbreviateNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B'
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M'
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K'
  return num.toString()
}
</script>

<template>
  <div class="w-full h-full flex items-center justify-center p-4">
    <div class="text-center w-full space-y-3">
      <div v-if="config?.show_title !== false" class="text-sm text-muted-foreground font-medium">{{ title }}</div>
      <div class="text-4xl lg:text-5xl font-bold">{{ formattedValue }}</div>
      <div v-if="config?.show_description !== false && description" class="text-sm text-muted-foreground">{{ description }}</div>
    </div>
  </div>
</template>


