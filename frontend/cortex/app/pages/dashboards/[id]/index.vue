<script setup lang="ts">
import { computed, ref, watch, onMounted, nextTick, reactive } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { toast } from 'vue-sonner'
import { 
  ArrowLeft, Settings, MoreHorizontal, Edit, Trash2, 
  Plus, RefreshCw, Clock, Eye, Layout, GripVertical 
} from 'lucide-vue-next'
import type { Dashboard, DashboardView, DashboardWidget, DashboardSection, VisualizationConfig } from '~/types/dashboards'
import { useAliasGenerator } from '~/composables/useAliasGenerator'
import DashboardContainer from '~/components/dashboards/DashboardContainer.vue'
import WidgetEditSheet from '~/components/dashboards/WidgetEditSheet.vue'
import DashboardViewSelector from '~/components/dashboards/DashboardViewSelector.vue'
import DashboardViewUpsert from '~/components/dashboards/DashboardViewUpsert.vue'

// Page metadata
definePageMeta({
  title: 'Dashboard',
  layout: 'default'
})

// Route params
const route = useRoute()
const router = useRouter()
const dashboardId = route.params.id as string

// Composables
const { 
  currentDashboard, 
  loading, 
  error, 
  fetchDashboard, 
  updateDashboard,
  setDefaultView,
  getDefaultView,
  getViewById 
} = useDashboards()
const { generateAlias } = useAliasGenerator()
const { metrics, fetchMetrics } = useMetrics()
const { selectedEnvironmentId } = useEnvironments()

// Metrics count for dynamic tab ordering in inline widget editor
const metricsCount = computed(() => metrics.value?.length || 0)

// Component state
const selectedViewId = ref<string>('')
const isExecuting = ref(false)
const executionResults = ref<any>(null)
const lastExecutionTime = ref<string>('')
const refreshKey = ref(0)

// Dialogs
const showAddViewDialog = ref(false)
const showEditViewDialog = ref(false)
const showAddSectionDialog = ref(false)
const editingView = ref<DashboardView | null>(null)
const addSectionForm = reactive({ title: '', description: '', alias: '' })
// Note: Widget creation is now handled inline in DashboardSection via InlineWidgetEditor
const showEditWidgetSheet = ref(false)
const editingWidget = ref<any>(null)

// Computed
const dashboard = computed(() => currentDashboard.value)
const currentView = computed(() => {
  if (!dashboard.value || !selectedViewId.value) return null
  return getViewById((dashboard.value as unknown) as Dashboard, selectedViewId.value)
})

const defaultView = computed(() => {
  if (!dashboard.value) return null
  return getDefaultView((dashboard.value as unknown) as Dashboard)
})

const dashboardForUi = computed(() => (dashboard.value as unknown) as Dashboard | null)
const hasNoCurrentView = computed(() => !!dashboard.value && !currentView.value)

const pageTitle = computed(() => {
  return dashboard.value?.name || 'Dashboard'
})

// Auto-generate alias from section title
watch(() => addSectionForm.title, (newTitle) => {
  if (newTitle) {
    addSectionForm.alias = generateAlias(newTitle)
  }
})

// Utility function to clean dashboard data for API requests
function cleanDashboardForUpdate(dashboard: any): any {
  console.log('Dashboard before cleaning:', dashboard)
  
  const cleaned = {
    ...dashboard,
    views: dashboard.views?.map((view: any) => {
      console.log('Processing view:', view)
      // Generate view alias if missing
      const viewAlias = view.alias || generateAlias(view.title || view.name || `view_${Date.now()}`)
      
      const cleanedView = {
        alias: viewAlias,
        title: view.title || view.name,
        description: view.description,
        context_id: view.context_id,
        layout: view.layout,
        sections: view.sections?.map((section: any) => {
          console.log('Processing section:', section)
          // Handle both old (id) and new (alias) section structures
          const sectionAlias = section.alias || generateAlias(section.title || `section_${Date.now()}`)
          
          const cleanedSection = {
            alias: sectionAlias,
            title: section.title,
            description: section.description,
            position: section.position,
            widgets: section.widgets?.map((widget: any) => {
              const vz = widget.visualization || {}
              const dm = vz.data_mapping || {}
              const cleanedDM = {
                x_axis: dm.x_axis ? {
                  field: dm.x_axis.field,
                  data_type: dm.x_axis.data_type ?? dm.x_axis.type ?? null,
                  label: dm.x_axis.label ?? null,
                  required: dm.x_axis.required ?? false
                } : null,
                y_axes: Array.isArray(dm.y_axes)
                  ? dm.y_axes.map((m:any) => ({
                      field: m.field,
                      data_type: m.data_type ?? m.type ?? 'numerical',
                      label: m.label ?? null,
                      required: m.required ?? true
                    }))
                  : null,
                value_field: dm.value_field ? {
                  field: dm.value_field.field,
                  data_type: dm.value_field.data_type ?? dm.value_field.type ?? 'numerical',
                  label: dm.value_field.label ?? null,
                  required: dm.value_field.required ?? true
                } : null,
                category_field: dm.category_field ? {
                  field: dm.category_field.field,
                  data_type: dm.category_field.data_type ?? dm.category_field.type ?? 'categorical',
                  label: dm.category_field.label ?? null,
                  required: dm.category_field.required ?? true
                } : null,
                series_field: dm.series_field ? {
                  field: dm.series_field.field,
                  data_type: dm.series_field.data_type ?? dm.series_field.type ?? 'categorical',
                  label: dm.series_field.label ?? null,
                  required: dm.series_field.required ?? false
                } : null,
                columns: dm.columns ?? null
              }

              // Build widget object - include either metric_id or metric (for embedded)
              const cleanedWidget: any = {
                alias: widget.alias || `widget_${Date.now()}`,
                section_alias: widget.section_alias || widget.section_id || sectionAlias,
                position: widget.position,
                grid_config: widget.grid_config,
                title: widget.title || 'Widget',
                description: widget.description,
                visualization: {
                  ...vz,
                  data_mapping: cleanedDM
                },
                metric_overrides: widget.metric_overrides
              }
              
              // Include either metric_id or embedded metric
              if (widget.metric_id) {
                cleanedWidget.metric_id = widget.metric_id
              } else if (widget.metric) {
                cleanedWidget.metric = widget.metric
              }
              
              return cleanedWidget
            }) || []
          }
          
          console.log('Cleaned section:', cleanedSection)
          return cleanedSection
        }) || []
      }
      
      console.log('Cleaned view:', cleanedView)
      return cleanedView
    }) || []
  }
  
  console.log('Dashboard after cleaning:', cleaned)
  return cleaned
}

// Methods
async function loadDashboard() {
  try {
    await fetchDashboard(dashboardId)
    
    const d = (dashboard.value as unknown) as Dashboard | null
    if (!d) return
    
    // Only set view if not already selected or if current selection is invalid
    const views = Array.isArray(d.views) ? d.views : []
    const currentViewStillExists = selectedViewId.value && views.some(v => v.alias === selectedViewId.value)
    
    // If current view still exists, keep it selected
    if (currentViewStillExists) {
      return
    }
    
    // Otherwise, set to default view or first available view
    const def = getDefaultView(d)
    if (def) {
      selectedViewId.value = def.alias
      return
    }
    if (views.length > 0 && views[0] && views[0].alias) {
      selectedViewId.value = views[0].alias
    }
  } catch (err) {
    toast.error('Failed to load dashboard')
    router.push('/dashboards')
  }
}

async function executeDashboardView() {
  // Repurposed as Refresh: trigger all widgets to reload
  if (!currentView.value) return
  isExecuting.value = true
  try {
    refreshKey.value++
    executionResults.value = null
    lastExecutionTime.value = new Date().toLocaleTimeString()
    toast.success('Refreshed all widgets')
  } catch (err) {
    toast.error('Failed to refresh widgets')
  } finally {
    // small delay for UX so spinner is visible
    setTimeout(() => { isExecuting.value = false }, 300)
  }
}

function onViewChanged(viewId: string) {
  selectedViewId.value = viewId
  // Clear previous execution results when switching views
  executionResults.value = null
}

async function setAsDefaultView() {
  if (!dashboard.value || !selectedViewId.value) return
  
  try {
    await setDefaultView(dashboard.value.id, selectedViewId.value)
    toast.success('Default view updated')
  } catch (err) {
    toast.error('Failed to update default view')
  }
}

// View management handlers
function handleAddView() {
  showAddViewDialog.value = true
}

function handleEditView(view: DashboardView) {
  editingView.value = view
  showEditViewDialog.value = true
}

async function handleViewCreated(view: DashboardView) {
  await loadDashboard()
  // Set the selected view after dashboard is reloaded to ensure the view exists
  selectedViewId.value = view.alias
}

function handleViewUpdated(view: DashboardView) {
  loadDashboard()
}

async function handleDeleteView(view: DashboardView) {
  if (!dashboard.value) return
  
  try {
    const mutable = JSON.parse(JSON.stringify(dashboard.value)) as Dashboard
    
    // Find and remove the view
    const viewIndex = mutable.views.findIndex(v => v.alias === view.alias)
    if (viewIndex < 0) {
      toast.error('View not found')
      return
    }
    
    // Remove the view
    mutable.views.splice(viewIndex, 1)
    
    // If we deleted the current view, switch to another view
    if (selectedViewId.value === view.alias) {
      // Try to select the default view, or the first available view
      const defaultViewAlias = (mutable as any).default_view
      if (defaultViewAlias && mutable.views.some(v => v.alias === defaultViewAlias)) {
        selectedViewId.value = defaultViewAlias
      } else if (mutable.views.length > 0 && mutable.views[0]) {
        selectedViewId.value = mutable.views[0].alias
      }
    }
    
    // If we deleted the default view, set a new default
    if ((mutable as any).default_view === view.alias && mutable.views.length > 0 && mutable.views[0]) {
      (mutable as any).default_view = mutable.views[0].alias
    }
    
    // Clean and update the dashboard
    const cleanedDashboard = cleanDashboardForUpdate(mutable)
    await updateDashboard(mutable.id, cleanedDashboard)
    
    toast.success('View deleted successfully')
    await loadDashboard()
  } catch (err: any) {
    console.error('Failed to delete view:', err)
    toast.error(err?.message || 'Failed to delete view')
  }
}

async function addSection() {
  if (!dashboard.value || !currentView.value) return
  const mutable = JSON.parse(JSON.stringify(dashboard.value)) as Dashboard
  const cv = currentView.value as unknown as DashboardView
  const viewIndex = mutable.views.findIndex(v => v.alias === cv.alias)
  if (viewIndex < 0) {
    toast.error('Current view not found')
    return
  }
  const title = addSectionForm.title.trim()
  const alias = addSectionForm.alias.trim()
  
  if (!title) {
    toast.error('Section title is required')
    return
  }
  
  if (!alias) {
    toast.error('Section alias is required')
    return
  }
  
  // Check if alias already exists in current view
  const existingSections = mutable.views[viewIndex]?.sections ?? []
  console.log('Existing sections before adding:', existingSections)
  
  // Check for alias conflicts (handle both old id and new alias structures)
  if (existingSections.some(s => (s.alias && s.alias === alias) || (s.title && generateAlias(s.title) === alias))) {
    toast.error('Section alias already exists in this view')
    return
  }
  
  const section: DashboardSection = {
    alias,
    title: title || undefined,
    description: addSectionForm.description || undefined,
    position: existingSections.length,
    widgets: []
  } as any
  
  // Clean existing sections and add the new one
  const cleanedExistingSections = existingSections.map((s: any) => {
    const sectionAlias = s.alias || generateAlias(s.title || `section_${Date.now()}`)
    return {
      alias: sectionAlias,
      title: s.title,
      description: s.description,
      position: s.position,
      widgets: s.widgets?.map((w: any) => ({
        alias: w.alias || `widget_${Date.now()}`,
        section_alias: w.section_alias || w.section_id || sectionAlias,
        metric_id: w.metric_id,
        position: w.position,
        grid_config: w.grid_config,
        title: w.title || 'Widget',
        description: w.description,
        visualization: w.visualization,
        metric_overrides: w.metric_overrides
      })) || []
    }
  })
  
  mutable.views[viewIndex] = {
    ...mutable.views[viewIndex],
    sections: [...cleanedExistingSections, section]
  } as any
  
  try {
    // Clean the dashboard data before sending to API
    const cleanedDashboard = cleanDashboardForUpdate(mutable)
    await updateDashboard(mutable.id, cleanedDashboard)
    toast.success('Section added')
    showAddSectionDialog.value = false
    addSectionForm.title = ''
    addSectionForm.description = ''
    addSectionForm.alias = ''
    await loadDashboard()
  } catch (e) {
    toast.error('Failed to add section')
  }
}

function editDashboard() {
  toast.info('Edit functionality coming soon')
}

function goBack() {
  router.push('/dashboards')
}

// Note: Widget creation is now handled inline via InlineWidgetEditor in DashboardSection

function onEditWidget(widget: any) {
  editingWidget.value = widget
  showEditWidgetSheet.value = true
}

async function updateWidget(updatedPartial: any) {
  if (!dashboard.value) return
  const mutable = JSON.parse(JSON.stringify(dashboard.value)) as Dashboard
  for (const view of mutable.views || []) {
    for (const section of view.sections || []) {
      const widgetsArr = section.widgets || []
      const idx = widgetsArr.findIndex(w => w.alias === editingWidget.value?.alias)
      if (idx >= 0) {
        const currentWidget = widgetsArr[idx]
        if (!currentWidget) continue
        widgetsArr[idx] = {
          ...currentWidget,
          ...updatedPartial,
          grid_config: updatedPartial.grid_config ?? currentWidget.grid_config,
          visualization: { ...currentWidget.visualization, ...updatedPartial.visualization }
        } as any
        try {
          const cleanedDashboard = cleanDashboardForUpdate(mutable)
          await updateDashboard(mutable.id, cleanedDashboard)
          toast.success('Widget updated')
          showEditWidgetSheet.value = false
          await loadDashboard()
        } catch (e) {
          toast.error('Failed to update widget')
        }
        return
      }
    }
  }
}

// Watch for route changes
watch(() => route.params.id, (newId) => {
  if (newId && newId !== dashboardId) {
    router.replace(`/dashboards/${newId}`)
  }
})

onMounted(() => {
  loadDashboard()
  // Fetch metrics count for dynamic tab ordering in inline widget editor
  if (selectedEnvironmentId.value) {
    fetchMetrics(selectedEnvironmentId.value)
  }
})

// Watch for environment changes to refetch metrics
watch(selectedEnvironmentId, (newEnvId) => {
  if (newEnvId) {
    fetchMetrics(newEnvId)
  }
})

// Update page title
useHead({
  title: pageTitle
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" @click="goBack">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div>
          <h1 class="text-3xl font-bold tracking-tight">{{ dashboard?.name || 'Loading...' }}</h1>
          <p v-if="dashboard?.description" class="text-muted-foreground">
            {{ dashboard.description }}
          </p>
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <!-- View Selector -->
        <DashboardViewSelector
          v-if="dashboardForUi"
          :dashboard="dashboardForUi as unknown as Dashboard"
          :selected-view-id="selectedViewId"
          :default-view-id="(dashboardForUi as any)?.default_view"
          @view-changed="onViewChanged"
          @set-default="setAsDefaultView"
          @add-view="handleAddView"
          @edit-view="handleEditView"
          @delete-view="handleDeleteView"
        />

        
        <!-- Execute Button -->
        <Button 
          @click="executeDashboardView" 
          :disabled="isExecuting || !currentView"
          class="gap-2"
        >
          <RefreshCw :class="{ 'animate-spin': isExecuting, 'w-4 h-4': true }" />
          {{ isExecuting ? 'Refreshing...' : 'Refresh' }}
        </Button>
      </div>
    </div>


    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <RefreshCw class="w-6 h-6 animate-spin mr-2" />
      Loading dashboard...
    </div>

    <!-- Error State -->
    <Card v-else-if="error" class="border-destructive">
      <CardContent class="p-6 text-center card-content-bg">
        <h3 class="text-lg font-semibold text-destructive mb-2">Error Loading Dashboard</h3>
        <p class="text-muted-foreground mb-4">{{ error }}</p>
        <Button @click="loadDashboard" variant="outline">
          <RefreshCw class="w-4 h-4 mr-2" />
          Retry
        </Button>
      </CardContent>
    </Card>


    <DashboardContainer
      v-if="dashboardForUi && currentView"
      :dashboard="dashboardForUi as unknown as Dashboard"
      :view="currentView"
      :execution-results="executionResults"
      :last-execution-time="lastExecutionTime"
      :refresh-key="refreshKey"
      :metrics-count="metricsCount"
      @execute-widget="(widgetId) => { toast.info('Widget execution coming soon') }"
      @widget-updated="() => { loadDashboard() }"
      @add-section="() => { showAddSectionDialog = true }"
      @edit-widget="onEditWidget"
    />

    <!-- No View Selected -->
    <Card v-else-if="dashboardForUi && !currentView">
      <CardContent class="p-12 text-center card-content-bg">
        <Layout class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <h3 class="text-lg font-semibold mb-2">No View Selected</h3>
        <p class="text-muted-foreground">
          This dashboard doesn't have any views or the selected view couldn't be found.
        </p>
      </CardContent>
    </Card>

    <!-- View Management Dialogs -->
    <DashboardViewUpsert
      v-model:open="showAddViewDialog"
      mode="create"
      :dashboard="dashboardForUi as unknown as Dashboard"
      @view-created="handleViewCreated"
    />
    
    <DashboardViewUpsert
      v-model:open="showEditViewDialog"
      mode="edit"
      :dashboard="dashboardForUi as unknown as Dashboard"
      :view-to-edit="editingView || undefined"
      @view-updated="handleViewUpdated"
    />

    <!-- Add Section Dialog -->
    <Dialog v-model:open="showAddSectionDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Section</DialogTitle>
          <DialogDescription>Create a new section in the current view.</DialogDescription>
        </DialogHeader>
        <div class="space-y-3 py-2">
          <div class="space-y-2">
            <Label>Section Title</Label>
            <Input v-model="addSectionForm.title" placeholder="Section title" />
          </div>
          <div class="space-y-2">
            <Label>Alias</Label>
            <Input v-model="addSectionForm.alias" placeholder="Auto-generated from title" />
            <p class="text-xs text-muted-foreground">Used for referencing this section. Auto-generated from title.</p>
          </div>
          <div class="space-y-2">
            <Label>Description (Optional)</Label>
            <Input v-model="addSectionForm.description" placeholder="Optional description" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showAddSectionDialog = false">Cancel</Button>
          <Button :disabled="!currentView || !addSectionForm.title.trim()" @click="addSection">Add</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Widget Edit Sheet (for backward compatibility with ViewWidget edit button) -->
    <WidgetEditSheet
      v-model:open="showEditWidgetSheet"
      :widget="editingWidget"
      :dashboard-id="dashboardId"
      @save="updateWidget"
    />
  </div>
</template>