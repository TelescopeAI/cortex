<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Plus, MoreHorizontal, GripVertical, Edit, Trash2, Move, RefreshCw } from 'lucide-vue-next'
import type { Dashboard, DashboardView, DashboardSection, DashboardWidget } from '~/types/dashboards'
import DashboardSectionComponent from '~/components/dashboards/DashboardSection.vue'
import { toast } from 'vue-sonner'

interface Props {
  dashboard: Dashboard
  view: DashboardView
  executionResults?: any
}

interface Emits {
  (e: 'execute-widget', widgetId: string): void
  (e: 'widget-updated'): void
  (e: 'section-updated'): void
  (e: 'add-section'): void
  (e: 'add-widget', sectionId: string): void
  (e: 'edit-widget', widget: DashboardWidget): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const isDragging = ref(false)
const draggedSection = ref<DashboardSection | null>(null)

// Computed
const sortedSections = computed(() => {
  return [...props.view.sections].sort((a, b) => a.position - b.position)
})

const totalWidgets = computed(() => {
  return props.view.sections.reduce((total, section) => total + section.widgets.length, 0)
})

// Methods
function addSection() {
  emit('section-updated')
  // Notify parent to add a new section to this view
  // Parent will construct and persist the change
  // Use a distinct event for clarity
  emit('add-section')
}

function editView() {
  // TODO: Implement edit view functionality
  toast.info('Edit view functionality coming soon')
}

function onSectionDragStart(section: DashboardSection) {
  isDragging.value = true
  draggedSection.value = section
}

function onSectionDragEnd() {
  isDragging.value = false
  draggedSection.value = null
}

function onSectionDrop(targetSection: DashboardSection) {
  if (!draggedSection.value || draggedSection.value.id === targetSection.id) {
    return
  }

  // TODO: Implement section reordering
  toast.info('Section reordering coming soon')
  
  onSectionDragEnd()
}

function handleWidgetUpdate() {
  emit('widget-updated')
}

function handleSectionUpdate() {
  emit('section-updated')
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
  <div class="space-y-6">
    <!-- View Header -->
    <Card>
      <CardHeader class="pb-4">
        <div class="flex items-center justify-between">
          <div>
            <CardTitle class="flex items-center gap-2">
              {{ view.name }}
              <Badge v-if="view.context_id" variant="outline" class="text-xs">
                Context: {{ view.context_id }}
              </Badge>
            </CardTitle>
            <p v-if="view.description" class="text-sm text-muted-foreground mt-1">
              {{ view.description }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <Badge variant="secondary">
              {{ sortedSections.length }} section{{ sortedSections.length !== 1 ? 's' : '' }}
            </Badge>
            <Badge variant="secondary">
              {{ totalWidgets }} widget{{ totalWidgets !== 1 ? 's' : '' }}
            </Badge>
            <Button variant="outline" size="sm" @click="addSection">
              <Plus class="w-4 h-4 mr-1" />
              Add Section
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal class="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click="editView">
                  <Edit class="w-4 h-4 mr-2" />
                  Edit View
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Move class="w-4 h-4 mr-2" />
                  Reorder Sections
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
    </Card>

    <!-- Sections -->
    <div v-if="sortedSections.length === 0" class="text-center py-12">
      <div class="w-12 h-12 mx-auto bg-muted rounded-lg flex items-center justify-center mb-4">
        <Plus class="w-6 h-6 text-muted-foreground" />
      </div>
      <h3 class="text-lg font-semibold mb-2">No sections in this view</h3>
      <p class="text-muted-foreground mb-4">
        Add sections to organize your widgets and start building your dashboard.
      </p>
      <Button @click="addSection">
        <Plus class="w-4 h-4 mr-2" />
        Add First Section
      </Button>
    </div>

    <div v-else class="space-y-6">
      <DashboardSectionComponent
        v-for="section in sortedSections"
        :key="section.id"
        :section="section"
        :execution-results="executionResults"
        :draggable="true"
        @execute-widget="executeWidget"
        @widget-updated="handleWidgetUpdate"
        @section-updated="handleSectionUpdate"
        @drag-start="onSectionDragStart(section)"
        @drag-end="onSectionDragEnd"
        @drop="onSectionDrop(section)"
        @add-widget="(sectionId) => emit('add-widget', sectionId)"
        @edit-widget="(widget) => emit('edit-widget', widget)"
      />
    </div>

    <!-- Execution Results Summary -->
    <Card v-if="executionResults" class="border-green-200 bg-green-50/50">
      <CardContent class="p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <RefreshCw class="w-4 h-4 text-green-600" />
            <span class="text-sm font-medium text-green-800">
              Dashboard executed successfully
            </span>
          </div>
          <div class="text-xs text-green-600">
            {{ executionResults.total_execution_time_ms?.toFixed(0) }}ms
          </div>
        </div>
        <div v-if="executionResults.view_execution?.errors?.length" class="mt-2">
          <p class="text-xs text-amber-700">
            {{ executionResults.view_execution.errors.length }} widget{{ executionResults.view_execution.errors.length !== 1 ? 's' : '' }} had errors
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<style scoped>
.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
}
</style>