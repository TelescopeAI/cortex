<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { 
  Plus, MoreHorizontal, GripVertical, Edit, Trash2, Move, 
  ChevronDown, ChevronUp, Eye, EyeOff 
} from 'lucide-vue-next'
import type { DashboardSection, DashboardWidget } from '~/types/dashboards'
import DashboardWidgetComponent from '~/components/dashboards/DashboardWidget.vue'
import ViewWidget from '~/components/dashboards/ViewWidget.vue'
import { toast } from 'vue-sonner'
import { twMerge } from 'tailwind-merge'
// @ts-ignore - types not included by package
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'

interface Props {
  section: DashboardSection
  executionResults?: any
  draggable?: boolean
  collapsible?: boolean
  defaultCollapsed?: boolean
  dashboardId?: string
  viewAlias?: string
}

interface Emits {
  (e: 'execute-widget', widgetId: string): void
  (e: 'widget-updated'): void
  (e: 'section-updated'): void
  (e: 'add-widget', sectionId: string): void
  (e: 'drag-start'): void
  (e: 'drag-end'): void
  (e: 'drop'): void
  (e: 'edit-widget', widget: DashboardWidget): void
}

const props = withDefaults(defineProps<Props>(), {
  draggable: false,
  collapsible: true,
  defaultCollapsed: false
})

const emit = defineEmits<Emits>()

// State
const isCollapsed = ref(props.defaultCollapsed)
const isDragging = ref(false)

// Computed
const sortedWidgets = computed(() => {
  return [...props.section.widgets].sort((a, b) => a.position - b.position)
})

const hasTitle = computed(() => {
  return props.section.title || props.section.description
})

// Grid helpers
const gridClass = computed(() => twMerge('grid grid-cols-12 gap-4'))

const getWidgetGridStyle = (widget: DashboardWidget) => {
  return {
    gridColumn: `span ${Math.min(widget.grid_config.columns, 12)}`,
    gridRow: `span ${widget.grid_config.rows}`
  }
}

// Drag & Drop
// Keep a local reactive list for DnD that mirrors the section widgets order
const localWidgets = ref<DashboardWidget[]>([...props.section.widgets].sort((a,b) => a.position - b.position))

watch(() => props.section.widgets, (val) => {
  localWidgets.value = [...val].sort((a,b) => a.position - b.position)
}, { deep: true })

// Type helper so template has correct types
const dndState = useDragAndDrop<DashboardWidget>(localWidgets.value, { sortable: true })
const gridRef = dndState[0]
const dndWidgets = dndState[1]

// When DnD list changes order, update widget positions and notify parent
watch(dndWidgets, (arr: DashboardWidget[]) => {
  // Update positions based on the new order
  arr.forEach((w, idx) => { w.position = idx })
  // Reflect change back to localWidgets (already refers to dndWidgets)
  localWidgets.value = [...arr]
  emit('section-updated')
})

// Keep DnD list in sync when parent updates widgets (e.g., on edit)
watch(() => props.section.widgets, (val) => {
  const sorted = [...val].sort((a,b) => a.position - b.position)
  // mutate the dndWidgets array in-place to preserve ref
  if (Array.isArray(dndWidgets.value)) {
    dndWidgets.value.splice(0, dndWidgets.value.length, ...sorted)
  } else {
    dndWidgets.value = [...sorted]
  }
  localWidgets.value = [...sorted]
}, { deep: true })

// Helper to get the underlying array from the DnD reactive value
const dndArray = computed<DashboardWidget[]>(() => {
  return dndWidgets.value
})

// Keep dndArray's items up to date with latest widget objects (title, grid_config, etc.)
watch(() => props.section.widgets, (val) => {
  const latest = [...val]
  const arr = dndArray.value
  // add or update
  latest.forEach((w) => {
    const idx = arr.findIndex(x => x.alias === w.alias)
    if (idx >= 0) {
      const target = arr[idx]
      if (target) Object.assign(target as any, w)
    } else {
      arr.push({ ...(w as any) })
    }
  })
  // remove stale
  for (let i = arr.length - 1; i >= 0; i--) {
    const item = arr[i]
    if (!item) continue
    if (!latest.find(w => w.alias === item.alias)) arr.splice(i, 1)
  }
}, { deep: true })

// Default DnD: no handle, drag anywhere on the draggable item

// Methods
function toggleCollapse() {
  if (props.collapsible) {
    isCollapsed.value = !isCollapsed.value
  }
}

function addWidget() {
  emit('add-widget', props.section.alias)
}

function editSection() {
  // TODO: Implement edit section functionality
  toast.info('Edit section functionality coming soon')
}

function deleteSection() {
  // TODO: Implement delete section functionality
  toast.info('Delete section functionality coming soon')
}

function reorderWidgets() {
  // TODO: Implement widget reordering
  toast.info('Widget reordering functionality coming soon')
}

function onDragStart(event: DragEvent) {
  if (!props.draggable) return
  isDragging.value = true
  emit('drag-start')
  
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', props.section.alias)
  }
}

function onDragEnd() {
  isDragging.value = false
  emit('drag-end')
}

function onDrop(event: DragEvent) {
  event.preventDefault()
  emit('drop')
}

function onDragOver(event: DragEvent) {
  if (props.draggable) {
    event.preventDefault()
    event.dataTransfer!.dropEffect = 'move'
  }
}

function handleWidgetUpdate() {
  emit('widget-updated')
}

function executeWidget(widgetId: string) {
  emit('execute-widget', widgetId)
}

function getWidgetExecutionResult(widgetId: string) {
  if (!props.executionResults?.view_execution?.widgets) return null
  return props.executionResults.view_execution.widgets.find((w: any) => w.widget_id === widgetId)
}
</script>

<template>
  <Card>
    <!-- Section Header -->
    <CardHeader 
      v-if="hasTitle"
      class="pb-4"
      :class="{ 'cursor-pointer': collapsible }"
      @click="toggleCollapse"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <GripVertical 
            v-if="draggable" 
            class="w-4 h-4 text-muted-foreground cursor-move" 
          />
          <div class="flex-1">
            <CardTitle v-if="section.title" class="text-lg">
              {{ section.title }}
            </CardTitle>
            <p v-if="section.description" class="text-sm text-muted-foreground mt-1">
              {{ section.description }}
            </p>
          </div>
        </div>
        
        <div class="flex items-center gap-2">
          <Badge variant="secondary" class="text-xs">
            {{ sortedWidgets.length }} widget{{ sortedWidgets.length !== 1 ? 's' : '' }}
          </Badge>
          
          <div class="flex items-center gap-1">
            <Button 
              v-if="collapsible"
              variant="ghost" 
              size="icon"
              class="h-6 w-6"
              @click.stop="toggleCollapse"
            >
              <ChevronUp v-if="isCollapsed" class="w-3 h-3" />
              <ChevronDown v-else class="w-3 h-3" />
            </Button>
            
            <Button variant="ghost" size="icon" class="h-6 w-6" @click.stop="addWidget">
              <Plus class="w-3 h-3" />
            </Button>
            
            <DropdownMenu>
              <DropdownMenuTrigger as-child @click.stop>
                <Button variant="ghost" size="icon" class="h-6 w-6">
                  <MoreHorizontal class="w-3 h-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click="editSection">
                  <Edit class="w-4 h-4 mr-2" />
                  Edit Section
                </DropdownMenuItem>
                <DropdownMenuItem @click="reorderWidgets">
                  <Move class="w-4 h-4 mr-2" />
                  Reorder Widgets
                </DropdownMenuItem>
                <DropdownMenuItem @click="deleteSection" class="text-destructive">
                  <Trash2 class="w-4 h-4 mr-2" />
                  Delete Section
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </CardHeader>

    <!-- Section Content -->
    <CardContent 
      v-show="!isCollapsed"
      :class="{ 'pt-6': !hasTitle }"
    >
      <!-- Empty State -->
      <div v-if="sortedWidgets.length === 0" class="text-center py-8">
        <div class="w-10 h-10 mx-auto bg-muted rounded-lg flex items-center justify-center mb-3">
          <Plus class="w-5 h-5 text-muted-foreground" />
        </div>
        <h4 class="font-medium mb-1">No widgets in this section</h4>
        <p class="text-sm text-muted-foreground mb-3">
          Add widgets to visualize your metrics and data.
        </p>
        <Button size="sm" @click="addWidget">
          <Plus class="w-4 h-4 mr-1" />
          Add Widget
        </Button>
      </div>

      <!-- Widgets Grid -->
      <div 
        v-else
        ref="gridRef"
        :class="gridClass"
        style="grid-auto-rows: minmax(6rem, auto)"
        class="relative z-0"
      >
        <div
          v-for="widget in dndArray"
          :key="widget.alias"
          :style="getWidgetGridStyle(widget)"
        >
          <ViewWidget 
            :dashboard-id="(props as any).dashboardId" 
            :view-alias="(props as any).viewAlias" 
            :widget="widget"
            @edit="(widget) => emit('edit-widget', widget)"
          />
        </div>
      </div>

      <!-- Add Widget Button (when widgets exist) -->
      <div v-if="sortedWidgets.length > 0" class="mt-4 pt-4 border-t border-dashed">
        <Button variant="outline" size="sm" @click="addWidget" class="w-full">
          <Plus class="w-4 h-4 mr-2" />
          Add Widget
        </Button>
      </div>
    </CardContent>

    <!-- Collapsed State Indicator -->
    <CardContent v-show="isCollapsed" class="py-2">
      <div class="flex items-center justify-center text-sm text-muted-foreground">
        <EyeOff class="w-4 h-4 mr-2" />
        {{ sortedWidgets.length }} widget{{ sortedWidgets.length !== 1 ? 's' : '' }} hidden
      </div>
    </CardContent>
  </Card>
</template>

<style scoped>
/* Ensure grid items don't overflow */
.grid > div {
  min-width: 0;
}
</style>