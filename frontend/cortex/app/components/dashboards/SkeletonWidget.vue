<script setup lang="ts">
import { Plus, BarChart3, LineChart, PieChart, Gauge, Table2 } from 'lucide-vue-next'

interface Props {
  columns?: number
  rows?: number
}

interface Emits {
  (e: 'activate'): void
}

const props = withDefaults(defineProps<Props>(), {
  columns: 3,
  rows: 1
})

const emit = defineEmits<Emits>()

function handleClick() {
  emit('activate')
}
</script>

<template>
  <div
    class="skeleton-widget group relative flex flex-col items-center justify-center
           border-2 border-dashed border-muted-foreground/30 rounded-lg
           bg-muted/20 hover:bg-muted/40 hover:border-primary/50
           transition-all duration-300 ease-out cursor-pointer
           min-h-[120px] p-6"
    :style="{
      gridColumn: `span ${Math.min(columns, 12)}`,
      gridRow: `span ${rows}`
    }"
    @click="handleClick"
  >
    <!-- Decorative chart icons (faded in background) -->
    <div class="absolute inset-0 flex items-center justify-center gap-6 opacity-10 group-hover:opacity-20 transition-opacity pointer-events-none">
      <BarChart3 class="w-8 h-8 text-muted-foreground" />
      <LineChart class="w-8 h-8 text-muted-foreground" />
      <PieChart class="w-8 h-8 text-muted-foreground" />
      <Gauge class="w-8 h-8 text-muted-foreground" />
      <Table2 class="w-8 h-8 text-muted-foreground" />
    </div>

    <!-- Main content -->
    <div class="relative z-10 flex flex-col items-center gap-3">
      <!-- Plus icon with animated ring -->
      <div class="relative">
        <div class="absolute inset-0 rounded-full bg-primary/10 scale-0 group-hover:scale-150 transition-transform duration-300" />
        <div class="relative flex items-center justify-center w-12 h-12 rounded-full bg-background border-2 border-muted-foreground/30 group-hover:border-primary/60 transition-colors">
          <Plus class="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
      </div>

      <!-- Text -->
      <div class="text-center">
        <p class="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
          Add Widget
        </p>
        <p class="text-xs text-muted-foreground/60 mt-0.5">
          Click to configure
        </p>
      </div>
    </div>

    <!-- Skeleton preview bars (decorative) -->
    <div class="absolute bottom-4 left-4 right-4 flex gap-2 opacity-30 group-hover:opacity-50 transition-opacity">
      <div class="h-1 flex-1 bg-muted-foreground/20 rounded-full" />
      <div class="h-1 w-8 bg-muted-foreground/20 rounded-full" />
      <div class="h-1 w-12 bg-muted-foreground/20 rounded-full" />
    </div>
  </div>
</template>

<style scoped>
.skeleton-widget {
  backdrop-filter: blur(4px);
}
</style>

