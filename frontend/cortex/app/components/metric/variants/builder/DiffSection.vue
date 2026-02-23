<template>
  <div class="space-y-1">
    <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2 font-geist">{{ label }}</p>

    <div class="space-y-0.5">
      <!-- Source items (kept or removed) -->
      <div
        v-for="name in sourceNames"
        :key="`src-${name}`"
        :class="[
          'px-2 py-1 rounded text-sm flex items-center gap-2 font-geist',
          isRemoved(name)
            ? 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300'
            : 'text-foreground'
        ]"
      >
        <Minus v-if="isRemoved(name)" class="h-3.5 w-3.5 shrink-0" />
        <span>{{ name }}</span>
      </div>

      <!-- Added items -->
      <div
        v-for="name in added"
        :key="`add-${name}`"
        class="px-2 py-1 rounded bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300 text-sm flex items-center gap-2 font-geist"
      >
        <Plus class="h-3.5 w-3.5 shrink-0" />
        <span>{{ name }}</span>
      </div>

      <!-- Replaced items -->
      <div
        v-for="name in replaced"
        :key="`rep-${name}`"
        class="px-2 py-1 rounded bg-orange-50 dark:bg-orange-950/30 text-orange-700 dark:text-orange-300 text-sm flex items-center gap-2 font-geist"
      >
        <ArrowLeftRight class="h-3.5 w-3.5 shrink-0" />
        <span>{{ name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Minus, Plus, ArrowLeftRight } from 'lucide-vue-next'

interface Props {
  label: string
  sourceNames: string[]
  added: string[]
  removed: string[]
  replaced: string[]
  included: string[] | null
}

const props = defineProps<Props>()

// Check if an item is removed (either explicitly removed or not in inclusion list)
const isRemoved = (name: string) => {
  if (props.included) {
    return !props.included.includes(name)
  }
  return props.removed.includes(name)
}
</script>
