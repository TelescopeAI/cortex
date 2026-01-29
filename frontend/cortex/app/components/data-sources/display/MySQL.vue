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

// MySQL diagonal checkered pattern styling
const cardStyle = {
  '--color1': 'rgb(0, 3, 49)',
  '--color2': 'rgb(248, 255, 182)',
  opacity: '0.8',
  backgroundImage: 'linear-gradient(45deg, var(--color2) 25%, transparent 25%, transparent 75%, var(--color2) 75%, var(--color2)), linear-gradient(135deg, var(--color2) 25%, var(--color1) 25%, var(--color1) 75%, var(--color2) 75%, var(--color2))',
  backgroundSize: '90px 90px',
  backgroundPosition: '0 0, 135px 135px'
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
    class="cursor-pointer p-0 hover:shadow-md transition-all duration-200
           inset-shadow-xl dot-pattern-display gap-y-0 h-64"
    role="button"
    tabindex="0"
    :aria-label="`View ${dataSource.name} data source, ${sourceTypeLabel}, updated ${relativeTime}`"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >

    <CardContent class="pt-0 pb-2 h-full flex items-center justify-center">
      <span class="inline-block max-w-full rounded-md text-orange-600 dark:text-white
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
.dot-pattern-display.dark,
.dark .dot-pattern-display {
  --color1: rgb(0, 3, 49);
  --color2: rgb(248, 255, 182);
  background-image: linear-gradient(45deg, var(--color2) 25%, transparent 25%, transparent 75%, var(--color2) 75%, var(--color2)), linear-gradient(135deg, var(--color2) 25%, var(--color1) 25%, var(--color1) 75%, var(--color2) 75%, var(--color2)) !important;
  background-size: 90px 90px !important;
  background-position: 0 0, 135px 135px !important;
}
</style>
