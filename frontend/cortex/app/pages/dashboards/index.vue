<script setup lang="ts">
import { computed, ref, reactive, watch, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '~/components/ui/dialog'
import { TagsInput, TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText } from '~/components/ui/tags-input'
import { Search, Filter, Plus, MoreHorizontal, Eye, Edit, Trash2, BarChart3, Gauge, TrendingUp, Calendar, Clock } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useDateFormat, useTimeAgo } from '@vueuse/core'
import type { Dashboard, DashboardType } from '~/types/dashboards'
import { useAliasGenerator } from '~/composables/useAliasGenerator'
// Initialize alias generator
const {
  generateAlias,
  validateAlias,
  getAliasError,
  aliasManuallyEdited,
  markAsManuallyEdited,
  resetManualEditFlag
} = useAliasGenerator()

// Page metadata
definePageMeta({
  title: 'Dashboards',
  layout: 'default'
})

// Composables
const { dashboards, loading, error, fetchDashboards, deleteDashboard, createDashboard: createDashboardApi } = useDashboards()
const { selectedEnvironmentId } = useEnvironments()
const router = useRouter()

// Component state
const searchQuery = ref('')
const selectedType = ref<string>('')
const sortBy = ref<string>('updated')
const sortOrder = ref<'asc' | 'desc'>('desc')
const showDeleteDialog = ref(false)
const dashboardToDelete = ref<Dashboard | null>(null)

// Create dialog state
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = reactive({
  name: '',
  alias: '',
  description: '',
  type: 'executive' as string,
  tags: [] as string[]
})

// Auto-generate alias from name unless manually edited
watch(() => createForm.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    createForm.alias = generateAlias(newName)
  }
})

watch(() => createForm.alias, (val) => {
  // If user types in alias field, consider it manual
  if (val && val !== generateAlias(createForm.name)) {
    markAsManuallyEdited()
  }
})

// Computed
const filteredDashboards = computed<Dashboard[]>(() => {
  const list = dashboards.value as unknown as Dashboard[]
  let filtered = [...list]

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((dashboard: Dashboard) => 
      dashboard.name.toLowerCase().includes(query) ||
      (dashboard.description?.toLowerCase().includes(query) ?? false) ||
      (dashboard.tags?.some(tag => tag.toLowerCase().includes(query)) ?? false)
    )
  }

  if (selectedType.value && selectedType.value !== 'all') {
    filtered = filtered.filter((dashboard: Dashboard) => dashboard.type === selectedType.value)
  }

  // Sort
  filtered.sort((a: Dashboard, b: Dashboard) => {
    let compareValue = 0
    
    switch (sortBy.value) {
      case 'name':
        compareValue = a.name.localeCompare(b.name)
        break
      case 'type':
        compareValue = a.type.localeCompare(b.type)
        break
      case 'created':
        compareValue = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        break
      case 'updated':
      default:
        compareValue = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
        break
    }
    
    return sortOrder.value === 'asc' ? compareValue : -compareValue
  })

  return filtered
})

const dashboardTypeOptions = [
  { value: 'executive', label: 'Executive', icon: TrendingUp },
  { value: 'operational', label: 'Operational', icon: Gauge },
  { value: 'analytical', label: 'Analytical', icon: BarChart3 },
  { value: 'tactical', label: 'Tactical', icon: Calendar }
]

const sortOptions = [
  { value: 'updated', label: 'Last Updated' },
  { value: 'created', label: 'Created Date' },
  { value: 'name', label: 'Name' },
  { value: 'type', label: 'Type' }
]

// Methods
async function loadDashboards() {
  if (!selectedEnvironmentId.value) {
    router.push('/config/workspaces')
    return
  }

  try {
    await fetchDashboards(selectedEnvironmentId.value, {
      search: searchQuery.value || undefined,
      type: (selectedType.value && selectedType.value !== 'all') ? selectedType.value : undefined,
      sortBy: sortBy.value as any,
      sortOrder: sortOrder.value
    })
  } catch (err) {
    toast.error('Failed to load dashboards')
  }
}

function getDashboardTypeInfo(type: string) {
  return dashboardTypeOptions.find(option => option.value === type) || dashboardTypeOptions[0]
}

function getBadgeVariant(type: string) {
  switch (type) {
    case 'executive': return 'default'
    case 'operational': return 'secondary'
    case 'analytical': return 'outline'
    case 'tactical': return 'destructive'
    default: return 'default'
  }
}

function viewDashboard(dashboard: Dashboard) {
  router.push(`/dashboards/${dashboard.id}`)
}

const formatUpdatedAt = (iso?: string) => {
  if (!iso) return '-'
  try {
    return useTimeAgo(iso).value
  } catch {
    return '-'
  }
}

function editDashboard(dashboard: Dashboard) {
  // TODO: Implement edit functionality
  toast.info('Edit functionality coming soon')
}

function confirmDeleteDashboard(dashboard: Dashboard) {
  dashboardToDelete.value = dashboard
  showDeleteDialog.value = true
}

async function handleDeleteDashboard() {
  if (!dashboardToDelete.value) return

  try {
    await deleteDashboard(dashboardToDelete.value.id)
    toast.success('Dashboard deleted successfully')
  } catch (err) {
    toast.error('Failed to delete dashboard')
  } finally {
    showDeleteDialog.value = false
    dashboardToDelete.value = null
  }
}

function createDashboard() {
  showCreateDialog.value = true
}

async function handleCreateDashboard() {
  if (!selectedEnvironmentId.value) {
    toast.error('Select an environment first')
    return
  }
  if (!createForm.name.trim()) {
    toast.error('Name is required')
    return
  }

  creating.value = true
  try {
    const dashboard = await createDashboardApi({
      environment_id: selectedEnvironmentId.value,
      alias: createForm.alias || undefined,
      name: createForm.name.trim(),
      description: createForm.description || undefined,
      type: createForm.type,
      views: [
        {
          name: 'Default',
          description: '',
          sections: [],
        }
      ],
      default_view_index: 0,
      tags: createForm.tags
    })

    toast.success('Dashboard created')
    showCreateDialog.value = false
    // reset form
    createForm.name = ''
    createForm.alias = ''
    createForm.description = ''
    createForm.type = 'executive'
    createForm.tags = []
    resetManualEditFlag()

    // Navigate to the new dashboard
    router.push(`/dashboards/${dashboard.id}`)
  } catch (err: any) {
    toast.error(err?.message || 'Failed to create dashboard')
  } finally {
    creating.value = false
  }
}

// Watch for filter changes
watch([searchQuery, selectedType, sortBy, sortOrder], () => {
  loadDashboards()
})

watch(selectedEnvironmentId, () => {
  if (selectedEnvironmentId.value) {
    loadDashboards()
  }
}, { immediate: true })

onMounted(() => {
  loadDashboards()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Dashboards</h1>
        <p class="text-muted-foreground">
          Manage and view your analytics dashboards
        </p>
      </div>
      <Button @click="createDashboard">
        <Plus class="w-4 h-4 mr-2" />
        Create Dashboard
      </Button>
    </div>

    <!-- Filters -->
    <Card>
      <CardContent class="p-6">
        <div class="flex flex-col gap-4 md:flex-row md:items-center">
          <!-- Search -->
          <div class="relative flex-1">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              v-model="searchQuery"
              placeholder="Search dashboards..."
              class="pl-10"
            />
          </div>

          <!-- Type Filter -->
          <Select v-model="selectedType">
            <SelectTrigger class="w-full md:w-48">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem
                v-for="option in dashboardTypeOptions"
                :key="option.value"
                :value="option.value"
              >
                <div class="flex items-center gap-2">
                  <component :is="option.icon" class="w-4 h-4" />
                  {{ option.label }}
                </div>
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- Sort -->
          <Select v-model="sortBy">
            <SelectTrigger class="w-full md:w-48">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="option in sortOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </SelectItem>
            </SelectContent>
          </Select>

          <!-- Sort Order -->
          <Select v-model="sortOrder">
            <SelectTrigger class="w-full md:w-32">
              <SelectValue placeholder="Order" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="desc">Newest</SelectItem>
              <SelectItem value="asc">Oldest</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <!-- Dashboard Grid -->
    <div v-if="loading" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card v-for="i in 6" :key="i" class="animate-pulse">
        <CardHeader>
          <div class="h-4 bg-muted rounded w-3/4"></div>
          <div class="h-3 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div class="space-y-2">
            <div class="h-3 bg-muted rounded"></div>
            <div class="h-3 bg-muted rounded w-2/3"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <div v-else-if="filteredDashboards.length === 0" class="text-center py-12">
      <BarChart3 class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No dashboards found</h3>
      <p class="text-muted-foreground mb-4">
        {{ searchQuery || selectedType ? 'Try adjusting your filters' : 'Create your first dashboard to get started' }}
      </p>
      <Button v-if="!searchQuery && !selectedType" @click="createDashboard">
        <Plus class="w-4 h-4 mr-2" />
        Create Dashboard
      </Button>
    </div>

    <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="dashboard in filteredDashboards"
        :key="dashboard.id"
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="viewDashboard(dashboard)"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <CardTitle class="text-lg mb-1">{{ dashboard.name }}</CardTitle>
              <p v-if="dashboard.description" class="text-sm text-muted-foreground line-clamp-2">
                {{ dashboard.description }}
              </p>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger as-child @click.stop>
                <Button variant="ghost" size="icon" class="h-8 w-8">
                  <MoreHorizontal class="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click.stop="viewDashboard(dashboard)">
                  <Eye class="w-4 h-4 mr-2" />
                  View
                </DropdownMenuItem>
                <DropdownMenuItem @click.stop="editDashboard(dashboard)">
                  <Edit class="w-4 h-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem 
                  @click.stop="confirmDeleteDashboard(dashboard)"
                  class="text-destructive"
                >
                  <Trash2 class="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent class="p-6">
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Badge :variant="getBadgeVariant(dashboard.type)">
                <component :is="getDashboardTypeInfo(dashboard.type)?.icon || TrendingUp" class="w-3 h-3 mr-1" />
                {{ getDashboardTypeInfo(dashboard.type)?.label || 'Executive' }}
              </Badge>
              <Badge v-if="dashboard.alias" variant="secondary">#{{ dashboard.alias }}</Badge>
              <Badge variant="outline">
                {{ dashboard.views.length }} view{{ dashboard.views.length !== 1 ? 's' : '' }}
              </Badge>
            </div>

            <div v-if="dashboard.tags?.length" class="flex flex-wrap gap-1">
              <Badge
                v-for="tag in dashboard.tags.slice(0, 3)"
                :key="tag"
                variant="secondary"
                class="text-xs"
              >
                {{ tag }}
              </Badge>
              <Badge
                v-if="dashboard.tags.length > 3"
                variant="secondary"
                class="text-xs"
              >
                +{{ dashboard.tags.length - 3 }}
              </Badge>
            </div>

            <div class="flex items-center text-xs text-muted-foreground">
              <Clock class="w-3 h-3 mr-1" />
              <span>{{ formatUpdatedAt(dashboard.updated_at) }}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Create Dashboard Dialog -->
    <Dialog v-model:open="showCreateDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Dashboard</DialogTitle>
          <DialogDescription>
            Provide basic details. You can add views and widgets later.
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-2">
            <label class="text-sm font-medium">Name</label>
            <Input v-model="createForm.name" placeholder="Sales Dashboard" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Alias</label>
            <Input v-model="createForm.alias" placeholder="Auto-generated from name" />
            <p class="text-xs text-muted-foreground">Only lowercase letters, numbers, and underscores allowed</p>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Description</label>
            <Input v-model="createForm.description" placeholder="Optional description" />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Type</label>
            <Select v-model="createForm.type">
              <SelectTrigger>
                <SelectValue placeholder="Select a type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem v-for="option in dashboardTypeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium">Tags</label>
            <TagsInput v-model="createForm.tags">
              <TagsInputItem v-for="tag in createForm.tags" :key="tag" :value="tag">
                <TagsInputItemText />
                <TagsInputItemDelete />
              </TagsInputItem>
              <TagsInputInput placeholder="Type and press enter" />
            </TagsInput>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showCreateDialog = false">Cancel</Button>
          <Button :disabled="creating" @click="handleCreateDashboard">
            <span v-if="creating">Creating...</span>
            <span v-else>Create</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog v-model:open="showDeleteDialog">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Dashboard</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{{ dashboardToDelete?.name }}"? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="showDeleteDialog = false">
            Cancel
          </Button>
          <Button variant="destructive" @click="handleDeleteDashboard">
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>