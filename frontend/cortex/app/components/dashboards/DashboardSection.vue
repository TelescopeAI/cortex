<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { 
  Plus, MoreHorizontal, Edit, Trash2, 
  ChevronDown, ChevronUp, EyeOff 
} from 'lucide-vue-next'
import type { DashboardSection, DashboardWidget } from '~/types/dashboards'
import ViewWidget from '~/components/dashboards/ViewWidget.vue'
import SkeletonWidget from '~/components/dashboards/SkeletonWidget.vue'
import InlineWidgetEditor from '~/components/dashboards/InlineWidgetEditor.vue'
import { toast } from 'vue-sonner'
import { twMerge } from 'tailwind-merge'
import { useDashboards } from '~/composables/useDashboards'
import { useAliasGenerator } from '~/composables/useAliasGenerator'

interface Props {
  section: DashboardSection
  executionResults?: any
  collapsible?: boolean
  defaultCollapsed?: boolean
  dashboardId?: string
  viewAlias?: string
  refreshKey?: number
  metricsCount?: number
  dashboard?: any  // Pass the full dashboard object
}

interface Emits {
  (e: 'execute-widget', widgetId: string): void
  (e: 'widget-updated'): void
  (e: 'section-updated'): void
  (e: 'add-widget', sectionId: string): void
  (e: 'edit-widget', widget: DashboardWidget): void
}

const props = withDefaults(defineProps<Props>(), {
  collapsible: true,
  defaultCollapsed: false,
  metricsCount: 0
})

const emit = defineEmits<Emits>()

// Composables
const { updateDashboard } = useDashboards()
const { generateAlias } = useAliasGenerator()

// State
const isCollapsed = ref(props.defaultCollapsed)

// Inline editor state
const isAddingWidget = ref(false)
const editingWidgetAlias = ref<string | null>(null)

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

// Methods
function toggleCollapse() {
  if (props.collapsible) {
    isCollapsed.value = !isCollapsed.value
  }
}

function addWidget() {
  // Use inline editor instead of emitting event
  isAddingWidget.value = true
  editingWidgetAlias.value = null
}

function editSection() {
  // TODO: Implement edit section functionality
  toast.info('Edit section functionality coming soon')
}

function deleteSection() {
  // TODO: Implement delete section functionality
  toast.info('Delete section functionality coming soon')
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

// Skeleton widget activation
function handleSkeletonActivate() {
  isAddingWidget.value = true
  editingWidgetAlias.value = null
}

// Handle inline edit from ViewWidget
function handleEditWidget(widget: DashboardWidget) {
  editingWidgetAlias.value = widget.alias
  isAddingWidget.value = false
}

// Cancel inline editor
function handleEditorCancel() {
  isAddingWidget.value = false
  editingWidgetAlias.value = null
}

// Save widget from inline editor
async function handleEditorSave(widgetData: Partial<DashboardWidget>) {
  if (!props.dashboardId || !props.viewAlias) {
    toast.error('Dashboard or view not found')
    return
  }

  try {
    const dashboard = props.dashboard
    if (!dashboard) {
      toast.error('Dashboard not loaded')
      return
    }

    // Find the view and section
    const view = dashboard.views.find((v: any) => v.alias === props.viewAlias)
    if (!view) {
      toast.error('View not found')
      return
    }

    const section = view.sections.find((s: any) => s.alias === props.section.alias)
    if (!section) {
      toast.error('Section not found')
      return
    }

    if (editingWidgetAlias.value) {
      // Editing existing widget
      const widgetIndex = section.widgets.findIndex((w: any) => w.alias === editingWidgetAlias.value)
      if (widgetIndex === -1) {
        toast.error('Widget not found')
        return
      }

      // Update the widget
      const updatedWidget = {
        ...section.widgets[widgetIndex],
        ...widgetData
      }
      section.widgets[widgetIndex] = updatedWidget as DashboardWidget

      // Update dashboard
      await updateDashboard(props.dashboardId, {
        views: dashboard.views
      })

      toast.success('Widget updated successfully')
    } else {
      // Creating new widget
      const newWidget: any = {
        alias: generateAlias(widgetData.title || 'widget'),
        section_alias: props.section.alias,
        metric_id: widgetData.metric_id || (widgetData as any).metric ? undefined : '',
        metric: (widgetData as any).metric || undefined,
        title: widgetData.title || 'New Widget',
        description: widgetData.description || '',
        position: section.widgets.length,
        grid_config: widgetData.grid_config || { columns: 12, rows: 3 },
        visualization: widgetData.visualization || { type: 'single_value' as const, data_mapping: {} }
      }

      section.widgets.push(newWidget)

      // Update dashboard
      await updateDashboard(props.dashboardId, {
        views: dashboard.views
      })

      toast.success('Widget created successfully')
    }

    // Close editor and refresh
    isAddingWidget.value = false
    editingWidgetAlias.value = null
    emit('widget-updated')
  } catch (err: any) {
    console.error('Failed to save widget:', err)
    toast.error(err?.data?.detail || err.message || 'Failed to save widget')
  }
}

// Check if a widget is being edited inline
function isWidgetBeingEdited(widgetAlias: string): boolean {
  return editingWidgetAlias.value === widgetAlias
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
      <!-- Empty State with Skeleton -->
      <div v-if="sortedWidgets.length === 0 && !isAddingWidget" class="text-center py-8">
        <SkeletonWidget 
          :columns="12" 
          :rows="6" 
          @activate="handleSkeletonActivate" 
        />
      </div>

      <!-- Inline Editor for New Widget (when section is empty) -->
      <div v-if="sortedWidgets.length === 0 && isAddingWidget" class="py-4">
        <InlineWidgetEditor
          :dashboard-id="dashboardId || ''"
          :section-alias="section.alias"
          :view-alias="viewAlias || ''"
          mode="create"
          :metrics-count="metricsCount"
          @cancel="handleEditorCancel"
          @save="handleEditorSave"
        />
      </div>

      <!-- Widgets Grid -->
      <div 
        v-if="sortedWidgets.length > 0"
        :class="gridClass"
        style="grid-auto-rows: minmax(6rem, auto)"
        class="relative z-0"
      >
        <template v-for="widget in sortedWidgets" :key="widget.alias">
          <!-- Show InlineWidgetEditor if this widget is being edited -->
          <div 
            v-if="isWidgetBeingEdited(widget.alias)"
            :style="{ gridColumn: 'span 12' }"
          >
            <InlineWidgetEditor
              :dashboard-id="dashboardId || ''"
              :section-alias="section.alias"
              :view-alias="viewAlias || ''"
              mode="edit"
              :widget="widget"
              :metrics-count="metricsCount"
              @cancel="handleEditorCancel"
              @save="handleEditorSave"
            />
          </div>
          
          <!-- Show ViewWidget otherwise -->
          <div
            v-else
            :style="getWidgetGridStyle(widget)"
          >
            <ViewWidget 
              :dashboard-id="dashboardId || ''" 
              :view-alias="viewAlias || ''" 
              :widget="widget"
              :refresh-key="refreshKey"
              @edit="handleEditWidget"
              @deleted="() => emit('widget-updated')"
            />
          </div>
        </template>

        <!-- Skeleton Widget at the end of the grid (when not adding) -->
        <SkeletonWidget 
          v-if="!isAddingWidget && !editingWidgetAlias"
          :columns="12" 
          :rows="3" 
          @activate="handleSkeletonActivate" 
        />

        <!-- Inline Editor for New Widget (at the end of grid) -->
        <div 
          v-if="isAddingWidget && sortedWidgets.length > 0"
          :style="{ gridColumn: 'span 12' }"
        >
          <InlineWidgetEditor
            :dashboard-id="dashboardId || ''"
            :section-alias="section.alias"
            :view-alias="viewAlias || ''"
            mode="create"
            :metrics-count="metricsCount"
            @cancel="handleEditorCancel"
            @save="handleEditorSave"
          />
        </div>
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
