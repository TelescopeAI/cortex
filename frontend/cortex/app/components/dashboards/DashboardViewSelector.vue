<script setup lang="ts">
import { computed, ref } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '~/components/ui/dropdown-menu'
import { 
  AlertDialog, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle 
} from '~/components/ui/alert-dialog'
import { Star, Settings, Plus, Trash2, AlertTriangle } from 'lucide-vue-next'
import type { Dashboard, DashboardView } from '~/types/dashboards'

interface Props {
  dashboard: Dashboard
  selectedViewId: string
  defaultViewId: string
}

interface Emits {
  (e: 'view-changed', viewId: string): void
  (e: 'set-default'): void
  (e: 'edit-view', view: DashboardView): void
  (e: 'add-view'): void
  (e: 'delete-view', view: DashboardView): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// State
const showDeleteDialog = ref(false)
const viewToDelete = ref<DashboardView | null>(null)

// Computed
const selectedView = computed(() => {
  return props.dashboard.views.find(view => view.alias === props.selectedViewId)
})

const isDefaultView = computed(() => {
  return props.selectedViewId === props.defaultViewId
})

const canDeleteView = computed(() => {
  // Can't delete if it's the only view
  return props.dashboard.views.length > 1
})

// Count total widgets in the view to be deleted
const widgetsToDeleteCount = computed(() => {
  if (!viewToDelete.value) return 0
  return viewToDelete.value.sections.reduce((total, section) => {
    return total + (section.widgets?.length || 0)
  }, 0)
})

const sectionsCount = computed(() => {
  if (!viewToDelete.value) return 0
  return viewToDelete.value.sections.length
})

// Methods
function handleViewChange(value: any) {
  const viewId = String(value)
  emit('view-changed', viewId)
}

function setAsDefault() {
  emit('set-default')
}

function editView(view: DashboardView) {
  emit('edit-view', view)
}

function addView() {
  emit('add-view')
}

function confirmDeleteView(view: DashboardView) {
  viewToDelete.value = view
  showDeleteDialog.value = true
}

async function handleDeleteConfirm() {
  if (viewToDelete.value) {
    const viewToEmit = viewToDelete.value
    showDeleteDialog.value = false
    viewToDelete.value = null
    emit('delete-view', viewToEmit)
  } else {
    showDeleteDialog.value = false
    viewToDelete.value = null
  }
}

function handleDeleteCancel() {
  showDeleteDialog.value = false
  viewToDelete.value = null
}
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- View Selector -->
    <Select :model-value="selectedViewId" @update:model-value="handleViewChange">
      <SelectTrigger class="w-64">
        <SelectValue>
          <div v-if="selectedView" class="flex items-center gap-2">
            <Star v-if="isDefaultView" class="w-3 h-3 text-yellow-500" />
            <span>{{ selectedView.title }}</span>
            <Badge v-if="isDefaultView" variant="secondary" class="text-xs">
              Default
            </Badge>
          </div>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="view in dashboard.views"
          :key="view.alias"
          :value="view.alias"
        >
          <div class="flex items-center gap-2 w-full">
            <Star 
              v-if="view.alias === defaultViewId" 
              class="w-3 h-3 text-yellow-500" 
            />
            <div class="flex-1">
              <div class="font-medium">{{ view.title }}</div>
              <div v-if="view.description" class="text-xs text-muted-foreground">
                {{ view.description }}
              </div>
            </div>
            <div class="flex items-center gap-1">
              <Badge variant="outline" class="text-xs">
                {{ view.sections.length }} section{{ view.sections.length !== 1 ? 's' : '' }}
              </Badge>
              <Badge 
                v-if="view.alias === defaultViewId" 
                variant="secondary" 
                class="text-xs"
              >
                Default
              </Badge>
            </div>
          </div>
        </SelectItem>
      </SelectContent>
    </Select>

    <!-- View Actions -->
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="icon">
          <Settings class="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem @click="addView">
          <Plus class="w-4 h-4 mr-2" />
          Add View
        </DropdownMenuItem>
        <DropdownMenuItem 
          v-if="selectedView"
          @click="setAsDefault"
          :disabled="isDefaultView"
        >
          <Star class="w-4 h-4 mr-2" />
          Set as Default
        </DropdownMenuItem>
        <DropdownMenuItem 
          v-if="selectedView"
          @click="editView(selectedView)"
        >
          <Settings class="w-4 h-4 mr-2" />
          Edit View
        </DropdownMenuItem>
        <DropdownMenuSeparator v-if="selectedView && canDeleteView" />
        <DropdownMenuItem 
          v-if="selectedView && canDeleteView"
          @click="confirmDeleteView(selectedView)"
          class="text-destructive focus:text-destructive"
        >
          <Trash2 class="w-4 h-4 mr-2" />
          Delete View
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>

    <!-- Delete Confirmation Dialog -->
    <AlertDialog :open="showDeleteDialog" @update:open="(val) => !val && handleDeleteCancel()">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle class="flex items-center gap-2">
            <AlertTriangle class="w-5 h-5 text-destructive" />
            Delete View
          </AlertDialogTitle>
          <AlertDialogDescription class="space-y-2">
            <p>
              Are you sure you want to delete the view "<strong>{{ viewToDelete?.title }}</strong>"?
            </p>
            <div v-if="widgetsToDeleteCount > 0" class="p-3 bg-destructive/10 border border-destructive/30 rounded-md">
              <p class="text-destructive font-medium">
                ⚠️ This will permanently delete:
              </p>
              <ul class="mt-2 text-sm text-destructive list-disc list-inside">
                <li>{{ sectionsCount }} section{{ sectionsCount !== 1 ? 's' : '' }}</li>
                <li>{{ widgetsToDeleteCount }} widget{{ widgetsToDeleteCount !== 1 ? 's' : '' }}</li>
              </ul>
            </div>
            <p v-else class="text-muted-foreground">
              This view has no widgets and can be safely deleted.
            </p>
            <p class="text-sm text-muted-foreground">
              This action cannot be undone.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <Button 
            variant="destructive"
            @click="handleDeleteConfirm"
          >
            Delete View
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>