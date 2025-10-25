<script setup lang="ts">
import { computed } from 'vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Badge } from '~/components/ui/badge'
import { 
  Monitor, Tablet, Smartphone
} from 'lucide-vue-next'

interface Props {
  columns: number
  rows: number
  disabled?: boolean
}

interface Emits {
  (e: 'update:columns', value: number): void
  (e: 'update:rows', value: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Grid size presets
const sizeOptions = [
  { 
    label: 'Small', 
    value: 3, 
    icon: Smartphone,
    color: 'bg-blue-100 text-blue-800'
  },
  { 
    label: 'Medium', 
    value: 6, 
    icon: Tablet,
    color: 'bg-green-100 text-green-800'
  },
  { 
    label: 'Large', 
    value: 12, 
    icon: Monitor,
    color: 'bg-purple-100 text-purple-800'
  }
]

const selectedColumns = computed(() => {
  return sizeOptions.find(option => option.value === props.columns) || sizeOptions[1]!
})

const selectedRows = computed(() => {
  return sizeOptions.find(option => option.value === props.rows) || sizeOptions[1]!
})

function selectColumns(value: string | number) {
  emit('update:columns', Number(value))
}

function selectRows(value: string | number) {
  emit('update:rows', Number(value))
}
</script>

<template>
  <div class="grid grid-cols-2 gap-4">
    <!-- Width (Columns) -->
    <div class="space-y-2">
      <div class="text-sm font-medium">Width</div>
      <Tabs :model-value="selectedColumns.value" @update:model-value="selectColumns" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger 
            v-for="option in sizeOptions"
            :key="option.value"
            :value="option.value"
            class="flex items-center gap-1 h-auto"
            :disabled="disabled"
          >
            <component :is="option.icon" class="w-3 h-3" />
            <span class="text-xs">{{ option.label }}</span>
            <Badge :class="option.color" class="text-xs px-1 py-0">
              {{ option.value }}
            </Badge>
          </TabsTrigger>
        </TabsList>
      </Tabs>
    </div>

    <!-- Length (Rows) -->
    <div class="space-y-2">
      <div class="text-sm font-medium">Length</div>
      <Tabs :model-value="selectedRows.value" @update:model-value="selectRows" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger 
            v-for="option in sizeOptions"
            :key="option.value"
            :value="option.value"
            class="flex items-center gap-1 h-auto"
            :disabled="disabled"
          >
            <component :is="option.icon" class="w-3 h-3" />
            <span class="text-xs">{{ option.label }}</span>
            <Badge :class="option.color" class="text-xs px-1 py-0">
              {{ option.value }}
            </Badge>
          </TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  </div>
</template>
