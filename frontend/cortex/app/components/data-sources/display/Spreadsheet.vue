<script setup lang="ts">
import { computed } from 'vue'
import { useTimeAgo } from '@vueuse/core'
import {
  Card,
  CardContent,
  CardFooter
} from '~/components/ui/card'
import DataSourceIcon from '~/components/data-sources/DataSourceIcon.vue'
import { DATA_SOURCE_TYPES } from '~/config/dataSourceTypes'
import type { DataSource } from '~/types'

interface Props {
  dataSource: DataSource
  showDescription?: boolean
  schemaTables: Array<{
    name: string
    columns: Array<{
      name: string
      type: string
      nullable?: boolean
      primary_key?: boolean
    }>
  }>
  schemaLoading: boolean
}

interface Emits {
  (e: 'click', dataSource: DataSource): void
}

const props = withDefaults(defineProps<Props>(), {
  showDescription: true
})

const emit = defineEmits<Emits>()

// Spreadsheet hexagonal pattern styling
const cardStyle = {
  '--s': '194px',
  '--c1': '#f6edb3',
  '--c2': '#acc4a3',
  '--_l': '#0000 calc(25% / 3), var(--c1) 0 25%, #0000 0',
  '--_g': 'conic-gradient(from 120deg at 50% 87.5%, var(--c1) 120deg, #0000 0)',
  background: 'var(--_g), var(--_g) 0 calc(var(--s) / 2), conic-gradient(from 180deg at 75%, var(--c2) 60deg, #0000 0), conic-gradient(from 60deg at 75% 75%, var(--c1) 0 60deg, #0000 0), linear-gradient(150deg, var(--_l)) 0 calc(var(--s) / 2), conic-gradient(at 25% 25%, #0000 50%, var(--c2) 0 240deg, var(--c1) 0 300deg, var(--c2) 0), linear-gradient(-150deg, var(--_l)) #55897c',
  backgroundSize: 'calc(0.866 * var(--s)) var(--s)',
  opacity: '0.8'
}

// Convert UTC to local timezone
const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

// Format relative time
const relativeTime = computed(() => {
  const localDate = convertUTCToLocal(props.dataSource.updated_at)
  const timeAgo = useTimeAgo(localDate, {
    updateInterval: 60000 // Update every minute
  })
  return timeAgo.value
})

// Check if data source has been updated (difference > 2 seconds)
const isUpdated = computed(() => {
  const createdAt = new Date(props.dataSource.created_at).getTime()
  const updatedAt = new Date(props.dataSource.updated_at).getTime()
  const diffInSeconds = Math.abs(updatedAt - createdAt) / 1000
  return diffInSeconds >= 2
})

// Get timestamp label
const timestampLabel = computed(() => {
  return isUpdated.value ? 'Updated' : 'Created'
})

// Get source type label
const sourceTypeLabel = computed(() => {
  const metadata = DATA_SOURCE_TYPES[props.dataSource.source_type]
  return metadata?.label || props.dataSource.source_type
})

const handleClick = () => {
  emit('click', props.dataSource)
}
</script>

<template>
  <Card
    :style="cardStyle"
    :class="[
      'cursor-pointer p-0 hover:shadow-md transition-all duration-200 inset-shadow-xl checkered-pattern-display gap-y-0'
    ]"
    role="button"
    tabindex="0"
    :aria-label="`View ${dataSource.name} data source, ${sourceTypeLabel}, updated ${relativeTime}`"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >

    <CardContent class="pt-0 pb-2 h-full flex items-center justify-center">
      <span class="inline-block max-w-full rounded-md text-green-600 dark:text-white
                   text-3xl drop-shadow bg-white dark:bg-slate-800 py-1 px-4
                   font-display font-thin tracking-wide

                   truncate">
              {{ dataSource.name }}
            </span>
    </CardContent>

    <CardFooter class="rounded-b-lg justify-between bg-white h-28">
      <div class="w-full flex justify-between">
        <div class="flex items-center backdrop-blur justify-start gap-2">
          <DataSourceIcon
            :source-type="dataSource.source_type"
            size="sm"
            class="text-muted-foreground"
          />
          <span class="text-xs font-medium text-muted-foreground">
            {{ sourceTypeLabel }}
          </span>
        </div>
        <div class="text-xs backdrop-blur text-muted-foreground flex justify-end">
          {{ timestampLabel }} {{ relativeTime }}
        </div>
      </div>
    </CardFooter>
  </Card>
</template>

<style scoped>
.checkered-pattern-display.dark,
.dark .checkered-pattern-display {
  --s: 194px;
  --c1: #4d5e3f !important;
  --c2: #3a4a2e !important;
  --_l: #0000 calc(25% / 3), var(--c1) 0 25%, #0000 0 !important;
  --_g: conic-gradient(from 120deg at 50% 87.5%, var(--c1) 120deg, #0000 0) !important;
  background: var(--_g), var(--_g) 0 calc(var(--s) / 2), conic-gradient(from 180deg at 75%, var(--c2) 60deg, #0000 0), conic-gradient(from 60deg at 75% 75%, var(--c1) 0 60deg, #0000 0), linear-gradient(150deg, var(--_l)) 0 calc(var(--s) / 2), conic-gradient(at 25% 25%, #0000 50%, var(--c2) 0 240deg, var(--c1) 0 300deg, var(--c2) 0), linear-gradient(-150deg, var(--_l)) #2d3a27 !important;
  background-size: calc(0.866 * var(--s)) var(--s) !important;
}
</style>
