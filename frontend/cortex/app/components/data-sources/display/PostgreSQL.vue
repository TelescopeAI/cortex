<script setup lang="ts">
import { computed } from 'vue'
import { useTimeAgo } from '@vueuse/core'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter
} from '~/components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Button } from '~/components/ui/button'
import { Skeleton } from '~/components/ui/skeleton'
import DataSourceIcon from '~/components/data-sources/DataSourceIcon.vue'
import { DATA_SOURCE_TYPES } from '~/config/dataSourceTypes'
import { Table } from 'lucide-vue-next'
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

// PostgreSQL geometric pattern styling
const cardStyle = {
  '--u': '10px',
  '--c1': '#fbf9fe',
  '--c2': '#02b6e7',
  '--c3': '#00699b',
  '--gp': '50% / calc(var(--u) * 16.8) calc(var(--u) * 12.9)',
  background: 'conic-gradient(from 122deg at 50% 85.15%, var(--c2) 0 58deg, var(--c3) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from 122deg at 50% 72.5%, var(--c1) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from 58deg at 82.85% 50%, var(--c3) 0 64deg, #fff0 0 100%) var(--gp), conic-gradient(from 58deg at 66.87% 50%, var(--c1) 0 64deg, var(--c2) 0 130deg, #fff0 0 100%) var(--gp), conic-gradient(from 238deg at 17.15% 50%, var(--c2) 0 64deg, #fff0 0 100%) var(--gp), conic-gradient(from 172deg at 33.13% 50%, var(--c3) 0 66deg, var(--c1) 0 130deg, #fff0 0 100%) var(--gp), linear-gradient(98deg, var(--c3) 0 15%, #fff0 calc(15% + 1px) 100%) var(--gp), linear-gradient(-98deg, var(--c2) 0 15%, #fff0 calc(15% + 1px) 100%) var(--gp), conic-gradient(from -58deg at 50.25% 14.85%, var(--c3) 0 58deg, var(--c2) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from -58deg at 50% 28.125%, var(--c1) 0 116deg, #fff0 0 100%) var(--gp), linear-gradient(90deg, var(--c2) 0 50%, var(--c3) 0 100%) var(--gp)',
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
    class="cursor-pointer p-0 hover:shadow-md transition-all duration-200
           inset-shadow-xl geometric-pattern-display gap-y-0 h-64"
    role="button"
    tabindex="0"
    :aria-label="`View ${dataSource.name} data source, ${sourceTypeLabel}, updated ${relativeTime}`"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
  >

    <CardContent class="pt-0 pb-2 h-full flex items-center justify-center grow">
      <!-- Loading skeletons -->
      <span class="inline-block max-w-full rounded-md text-blue-900 dark:text-white 
                   text-3xl drop-shadow bg-white dark:bg-slate-800 py-1 px-4
                   font-display tracking-wide

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
.geometric-pattern-display.dark,
.dark .geometric-pattern-display {
  --u: 10px;
  --c1: #334155 !important;
  --c2: #22d3ee !important;
  --c3: #06b6d4 !important;
  --gp: 50% / calc(var(--u) * 16.8) calc(var(--u) * 12.9) !important;
  background: conic-gradient(from 122deg at 50% 85.15%, var(--c2) 0 58deg, var(--c3) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from 122deg at 50% 72.5%, var(--c1) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from 58deg at 82.85% 50%, var(--c3) 0 64deg, #fff0 0 100%) var(--gp), conic-gradient(from 58deg at 66.87% 50%, var(--c1) 0 64deg, var(--c2) 0 130deg, #fff0 0 100%) var(--gp), conic-gradient(from 238deg at 17.15% 50%, var(--c2) 0 64deg, #fff0 0 100%) var(--gp), conic-gradient(from 172deg at 33.13% 50%, var(--c3) 0 66deg, var(--c1) 0 130deg, #fff0 0 100%) var(--gp), linear-gradient(98deg, var(--c3) 0 15%, #fff0 calc(15% + 1px) 100%) var(--gp), linear-gradient(-98deg, var(--c2) 0 15%, #fff0 calc(15% + 1px) 100%) var(--gp), conic-gradient(from -58deg at 50.25% 14.85%, var(--c3) 0 58deg, var(--c2) 0 116deg, #fff0 0 100%) var(--gp), conic-gradient(from -58deg at 50% 28.125%, var(--c1) 0 116deg, #fff0 0 100%) var(--gp), linear-gradient(90deg, var(--c2) 0 50%, var(--c3) 0 100%) var(--gp) !important;
}

.scrollbar-hide {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.scrollbar-hide::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}
</style>
