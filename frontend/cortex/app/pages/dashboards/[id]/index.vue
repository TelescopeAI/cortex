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
  ArrowLeft, Settings, Play, MoreHorizontal, Edit, Trash2, 
  Plus, RefreshCw, Clock, Eye, Layout, GripVertical 
} from 'lucide-vue-next'
import type { Dashboard, DashboardView, DashboardWidget, DashboardSection, VisualizationConfig } from '~/types/dashboards'
import { useAliasGenerator } from '~/composables/useAliasGenerator'
import DashboardContainer from '~/components/dashboards/DashboardContainer.vue'
import WidgetUpsertDialog from '~/components/dashboards/WidgetUpsertDialog.vue'
import WidgetEditSheet from '~/components/dashboards/WidgetEditSheet.vue'
import DashboardViewSelector from '~/components/dashboards/DashboardViewSelector.vue'

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
  executeDashboard,
  setDefaultView,
  getDefaultView,
  getViewById 
} = useDashboards()
const { generateAlias } = useAliasGenerator()

// Component state
const selectedViewId = ref<string>('')
const isExecuting = ref(false)
const executionResults = ref<any>(null)
const lastExecutionTime = ref<string>('')

// Dialogs
const showAddViewDialog = ref(false)
const showAddSectionDialog = ref(false)
const addViewForm = reactive({ title: '', description: '', alias: '' })
const addSectionForm = reactive({ title: '', description: '', alias: '' })
const showAddWidgetDialog = ref(false)
const showEditWidgetSheet = ref(false)
const editingWidget = ref<any>(null)
const addWidgetForm = reactive({
  sectionId: '' as string,
  title: '',
  metric_id: '',
  type: 'single_value' as string,
  columns: 3,
  rows: 1
})

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

// Auto-generate alias from view title
watch(() => addViewForm.title, (newTitle) => {
  if (newTitle) {
    addViewForm.alias = generateAlias(newTitle)
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

              return {
                alias: widget.alias || `widget_${Date.now()}`,
                section_alias: widget.section_alias || widget.section_id || sectionAlias,
                metric_id: widget.metric_id,
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
    
    // Set initial view to default view
    const d = (dashboard.value as unknown) as Dashboard | null
    if (!d) return
    const def = getDefaultView(d)
    if (def) {
      selectedViewId.value = def.alias
      return
    }
    const views = Array.isArray(d.views) ? d.views : []
    if (views.length > 0 && views[0] && views[0].alias) {
      selectedViewId.value = views[0].alias
    }
  } catch (err) {
    toast.error('Failed to load dashboard')
    router.push('/dashboards')
  }
}

async function executeDashboardView() {
  if (!dashboard.value || !selectedViewId.value) return
  
  isExecuting.value = true
  try {
    const result = await executeDashboard((dashboard.value!).id, selectedViewId.value)
    executionResults.value = result
    lastExecutionTime.value = new Date().toLocaleTimeString()
    toast.success('Dashboard executed successfully')
  } catch (err) {
    toast.error('Failed to execute dashboard')
  } finally {
    isExecuting.value = false
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

async function addView() {
  if (!dashboard.value) return
  const title = addViewForm.title.trim()
  const alias = addViewForm.alias.trim()
  
  if (!title) {
    toast.error('View title is required')
    return
  }
  
  if (!alias) {
    toast.error('View alias is required')
    return
  }
  
  const mutable = JSON.parse(JSON.stringify(dashboard.value!)) as Dashboard
  
  // Check if alias already exists
  if (mutable.views.some(v => v.alias === alias)) {
    toast.error('View alias already exists')
    return
  }
  
  const newView: DashboardView = {
    alias,
    title,
    description: addViewForm.description || undefined,
    sections: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  } as any
  const updated = { ...mutable, views: [...mutable.views, newView] } as Dashboard
  try {
    await updateDashboard(mutable.id, updated as any)
    toast.success('View added')
    showAddViewDialog.value = false
    addViewForm.title = ''
    addViewForm.description = ''
    addViewForm.alias = ''
    await loadDashboard()
    selectedViewId.value = newView.alias
  } catch (e) {
    toast.error('Failed to add view')
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

function onRequestAddWidget(sectionId: string) {
  console.log('onRequestAddWidget called with sectionId:', sectionId)
  addWidgetForm.sectionId = sectionId
  console.log('Set addWidgetForm.sectionId to:', addWidgetForm.sectionId)
  showAddWidgetDialog.value = true
}

function onWidgetSubmit(partial: any) {
  console.log('onWidgetSubmit called with:', partial)
  
  // Update form with submitted data (preserve sectionId)
  addWidgetForm.title = partial.title || ''
  addWidgetForm.metric_id = partial.metric_id || ''
  addWidgetForm.type = partial.visualization?.type || 'single_value'
  addWidgetForm.columns = partial.grid_config?.columns || 3
  addWidgetForm.rows = partial.grid_config?.rows || 1
  // Note: sectionId is already set from onRequestAddWidget, don't overwrite it
  
  console.log('Updated addWidgetForm:', addWidgetForm)
  
  // Call the add widget function with the full partial to preserve mapping/config
  addWidget(partial)
}

async function addWidget(partial?: any) {
  console.log('addWidget called')
  console.log('Dashboard:', dashboard.value)
  console.log('Current view:', currentView.value)
  console.log('addWidgetForm:', addWidgetForm)
  
  if (!dashboard.value || !currentView.value) {
    console.log('Missing dashboard or current view, returning early')
    return
  }
  
  const mutable = JSON.parse(JSON.stringify(dashboard.value)) as Dashboard
  const vIdx = Array.isArray(mutable.views) ? mutable.views.findIndex(v => v.alias === (currentView.value as any).alias) : -1
  console.log('View index:', vIdx)
  
  if (vIdx < 0 || !mutable.views[vIdx]) {
    console.log('View not found, returning early')
    return
  }
  
  const sectionList = mutable.views[vIdx].sections || []
  const sIdx = sectionList.findIndex(s => s.alias === addWidgetForm.sectionId)
  console.log('Section index:', sIdx, 'Looking for section:', addWidgetForm.sectionId)
  
  if (sIdx < 0 || !sectionList[sIdx]) {
    console.log('Section not found, returning early')
    return
  }
  const incomingViz = partial?.visualization || {}
  const incomingDM = incomingViz.data_mapping || {}
  // Normalize mapping: default x as categorical, y as numerical
  const normalizedDM = {
    x_axis: incomingDM.x_axis ? {
      field: incomingDM.x_axis.field,
      data_type: incomingDM.x_axis.data_type ?? incomingDM.x_axis.type ?? 'categorical',
      label: incomingDM.x_axis.label ?? null,
      required: incomingDM.x_axis.required ?? true
    } : null,
    y_axes: Array.isArray(incomingDM.y_axes) ? incomingDM.y_axes.map((m:any) => ({
      field: m.field,
      data_type: m.data_type ?? m.type ?? 'numerical',
      label: m.label ?? null,
      required: m.required ?? true
    })) : null,
    value_field: incomingDM.value_field ? {
      field: incomingDM.value_field.field,
      data_type: incomingDM.value_field.data_type ?? incomingDM.value_field.type ?? 'numerical',
      label: incomingDM.value_field.label ?? null,
      required: incomingDM.value_field.required ?? true
    } : null,
    category_field: incomingDM.category_field ? {
      field: incomingDM.category_field.field,
      data_type: incomingDM.category_field.data_type ?? incomingDM.category_field.type ?? 'categorical',
      label: incomingDM.category_field.label ?? null,
      required: incomingDM.category_field.required ?? true
    } : null,
    series_field: incomingDM.series_field ? {
      field: incomingDM.series_field.field,
      data_type: incomingDM.series_field.data_type ?? incomingDM.series_field.type ?? 'categorical',
      label: incomingDM.series_field.label ?? null,
      required: incomingDM.series_field.required ?? false
    } : null,
    columns: incomingDM.columns ?? null,
  }

  const newWidget: DashboardWidget = {
    alias: `widget_${Date.now()}`, // Generate a temporary alias
    section_alias: addWidgetForm.sectionId,
    metric_id: addWidgetForm.metric_id || crypto.randomUUID(),
    position: (sectionList[sIdx].widgets?.length ?? 0),
    grid_config: { columns: addWidgetForm.columns, rows: addWidgetForm.rows },
    title: addWidgetForm.title || 'New Widget',
    description: undefined,
    visualization: {
      type: addWidgetForm.type as any,
      data_mapping: normalizedDM,
      single_value_config: (incomingViz.type === 'single_value') ? incomingViz.single_value_config : undefined,
      gauge_config: (incomingViz.type === 'gauge') ? incomingViz.gauge_config : undefined,
    } as any
  }
  const widgets = sectionList[sIdx].widgets || []
  sectionList[sIdx] = { ...sectionList[sIdx], widgets: [...widgets, newWidget] }
  mutable.views[vIdx].sections = sectionList
  try {
    const cleanedDashboard = cleanDashboardForUpdate(mutable)
    await updateDashboard(mutable.id, cleanedDashboard)
    toast.success('Widget added')
    showAddWidgetDialog.value = false
    addWidgetForm.title = ''
    addWidgetForm.metric_id = ''
    await loadDashboard()
  } catch (e) {
    toast.error('Failed to add widget')
  }
}

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
        />

        <!-- Add View -->
        <Button variant="outline" size="sm" @click="showAddViewDialog = true">
          <Plus class="w-4 h-4 mr-1" />
          Add View
        </Button>
        
        <!-- Execute Button -->
        <Button 
          @click="executeDashboardView" 
          :disabled="isExecuting || !currentView"
          class="gap-2"
        >
          <RefreshCw :class="{ 'animate-spin': isExecuting, 'w-4 h-4': true }" />
          {{ isExecuting ? 'Executing...' : 'Execute' }}
        </Button>
        
        <!-- Actions -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button variant="outline" size="icon">
              <MoreHorizontal class="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem @click="editDashboard">
              <Edit class="w-4 h-4 mr-2" />
              Edit Dashboard
            </DropdownMenuItem>
            <DropdownMenuItem @click="setAsDefaultView" :disabled="!currentView || currentView.alias === (dashboardForUi as any)?.default_view">
              <Eye class="w-4 h-4 mr-2" />
              Set as Default View
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- Dashboard Info -->
    <Card v-if="dashboard">
      <CardContent class="p-4 card-content-bg">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <Badge>{{ dashboard.type }}</Badge>
            <Badge variant="outline">{{ dashboard.views.length }} views</Badge>
            <div v-if="dashboard.tags?.length" class="flex gap-1">
              <Badge 
                v-for="tag in dashboard.tags" 
                :key="tag" 
                variant="secondary"
                class="text-xs"
              >
                {{ tag }}
              </Badge>
            </div>
          </div>
          <div v-if="lastExecutionTime" class="flex items-center text-sm text-muted-foreground">
            <Clock class="w-4 h-4 mr-1" />
            Last executed: {{ lastExecutionTime }}
          </div>
        </div>
      </CardContent>
    </Card>

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

    <!-- Dashboard Content -->
    <div class="flex items-center justify-between" v-if="dashboard && currentView">
      <div class="text-sm text-muted-foreground">View: {{ currentView.title }}</div>
      <Button variant="outline" size="sm" @click="showAddSectionDialog = true">
        <Plus class="w-4 h-4 mr-1" />
        Add Section
      </Button>
    </div>

    <DashboardContainer
      v-if="dashboardForUi && currentView"
      :dashboard="dashboardForUi as unknown as Dashboard"
      :view="currentView"
      :execution-results="executionResults"
      @execute-widget="(widgetId) => { toast.info('Widget execution coming soon') }"
      @widget-updated="() => { loadDashboard() }"
      @add-section="() => { showAddSectionDialog = true }"
      @add-widget="onRequestAddWidget"
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

    <!-- Add View Dialog -->
    <Dialog v-model:open="showAddViewDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add View</DialogTitle>
          <DialogDescription>Create a new view in this dashboard.</DialogDescription>
        </DialogHeader>
        <div class="space-y-3 py-2">
          <div class="space-y-2">
            <Label>View Title</Label>
            <Input v-model="addViewForm.title" placeholder="View title" />
          </div>
          <div class="space-y-2">
            <Label>Alias</Label>
            <Input v-model="addViewForm.alias" placeholder="Auto-generated from title" />
            <p class="text-xs text-muted-foreground">Used for referencing this view. Auto-generated from title.</p>
          </div>
          <div class="space-y-2">
            <Label>Description (Optional)</Label>
            <Input v-model="addViewForm.description" placeholder="Optional description" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showAddViewDialog = false">Cancel</Button>
          <Button :disabled="!addViewForm.title.trim()" @click="addView">Add</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

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

    <!-- Widget Dialogs -->
    <WidgetUpsertDialog
      v-model:open="showAddWidgetDialog"
      mode="create"
      :initial="{ title: addWidgetForm.title, metric_id: addWidgetForm.metric_id, grid_config: { columns: addWidgetForm.columns, rows: addWidgetForm.rows }, visualization: { type: addWidgetForm.type } }"
      @submit="onWidgetSubmit"
    />
    <WidgetEditSheet
      v-model:open="showEditWidgetSheet"
      :widget="editingWidget"
      :dashboard-id="dashboardId"
      @save="updateWidget"
    />
  </div>
</template>