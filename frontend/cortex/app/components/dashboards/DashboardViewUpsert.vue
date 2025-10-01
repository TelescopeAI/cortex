<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { useDashboards } from '~/composables/useDashboards'
import { useAliasGenerator } from '~/composables/useAliasGenerator'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Loader2, Plus, Edit } from 'lucide-vue-next'
import type { Dashboard, DashboardView } from '~/types/dashboards'

interface Props {
  open: boolean
  mode?: 'create' | 'edit'
  dashboard: Dashboard
  viewToEdit?: DashboardView
}

interface Emits {
  (e: 'update:open', value: boolean): void
  (e: 'view-created', view: DashboardView): void
  (e: 'view-updated', view: DashboardView): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create'
})

const emit = defineEmits<Emits>()

const { updateDashboard } = useDashboards()
const { generateAlias, aliasManuallyEdited, markAsManuallyEdited, getAliasError } = useAliasGenerator()

// State
const isLoading = ref(false)
const form = reactive({
  title: '',
  alias: '',
  description: '',
  context_id: ''
})

// Computed
const isEditing = computed(() => props.mode === 'edit')
const dialogTitle = computed(() => isEditing.value ? 'Edit View' : 'Add View')
const dialogDescription = computed(() => 
  isEditing.value 
    ? 'Update view information and settings.' 
    : 'Create a new view in this dashboard.'
)

const isFormValid = computed(() => {
  return form.title.trim() && form.alias.trim()
})

const aliasError = computed(() => {
  if (!form.alias) return 'Alias is required'
  return getAliasError(form.alias)
})

// Methods
function resetForm() {
  form.title = ''
  form.alias = ''
  form.description = ''
  form.context_id = ''
}

function loadViewData(view: DashboardView) {
  form.title = view.title || ''
  form.alias = view.alias || ''
  form.description = view.description || ''
  form.context_id = view.context_id || ''
}

function handleAliasChange(value: string) {
  form.alias = value
  if (!aliasManuallyEdited.value) {
    markAsManuallyEdited()
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return

  isLoading.value = true
  
  try {
    const mutable = JSON.parse(JSON.stringify(props.dashboard)) as Dashboard
    
    if (isEditing.value && props.viewToEdit) {
      // Update existing view
      const viewIndex = mutable.views.findIndex(v => v.alias === props.viewToEdit!.alias)
      if (viewIndex >= 0) {
        const existingView = mutable.views[viewIndex]
        if (existingView) {
          mutable.views[viewIndex] = {
            ...existingView,
            title: form.title.trim(),
            alias: form.alias.trim(),
            description: form.description.trim() || undefined,
            context_id: form.context_id.trim() || undefined,
            sections: existingView.sections || [],
            created_at: existingView.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        }
      }
    } else {
      // Create new view
      const newView: DashboardView = {
        alias: form.alias.trim(),
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        context_id: form.context_id.trim() || undefined,
        sections: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as any
      
      mutable.views.push(newView)
    }

    // Update dashboard
    await updateDashboard(mutable.id, mutable as any)
    
    // Show success message
    toast.success(isEditing.value ? 'View updated successfully' : 'View created successfully')
    
    // Emit events
    if (isEditing.value && props.viewToEdit) {
      const updatedView = mutable.views.find(v => v.alias === form.alias.trim())
      if (updatedView) {
        emit('view-updated', updatedView)
      }
    } else {
      const newView = mutable.views[mutable.views.length - 1]
      if (newView) {
        emit('view-created', newView)
      }
    }
    
    // Close dialog
    emit('update:open', false)
    resetForm()
    
  } catch (error: any) {
    console.error('Failed to save view:', error)
    toast.error(error?.message || `Failed to ${isEditing.value ? 'update' : 'create'} view`)
  } finally {
    isLoading.value = false
  }
}

function closeDialog() {
  emit('update:open', false)
  resetForm()
}

// Auto-generate alias from title
watch(() => form.title, (newTitle) => {
  if (newTitle && !aliasManuallyEdited.value) {
    form.alias = generateAlias(newTitle)
  }
})

// Load view data when editing
watch(() => props.viewToEdit, (view) => {
  if (view && isEditing.value) {
    loadViewData(view)
  }
}, { immediate: true })

// Reset form when dialog opens/closes
watch(() => props.open, (isOpen) => {
  if (isOpen && isEditing.value && props.viewToEdit) {
    loadViewData(props.viewToEdit)
  } else if (isOpen && !isEditing.value) {
    resetForm()
  }
})
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2">
          <component :is="isEditing ? Edit : Plus" class="w-5 h-5" />
          {{ dialogTitle }}
        </DialogTitle>
        <DialogDescription>
          {{ dialogDescription }}
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4 py-4">
        <div class="space-y-2">
          <Label for="view-title">View Title *</Label>
          <Input
            id="view-title"
            v-model="form.title"
            placeholder="Enter view title"
            :disabled="isLoading"
            required
          />
        </div>
        
        <div class="space-y-2">
          <Label for="view-alias">Alias *</Label>
          <Input
            id="view-alias"
            :model-value="form.alias"
            @update:model-value="(value) => handleAliasChange(String(value))"
            placeholder="Auto-generated from title"
            :disabled="isLoading"
            required
          />
          <p class="text-xs text-muted-foreground">
            {{ aliasError || 'Used for referencing this view. Auto-generated from title.' }}
          </p>
        </div>
        
        <div class="space-y-2">
          <Label for="view-description">Description</Label>
          <Textarea
            id="view-description"
            v-model="form.description"
            placeholder="Optional description"
            rows="3"
            :disabled="isLoading"
          />
        </div>
        
        <div class="space-y-2">
          <Label for="view-context">Context ID</Label>
          <Input
            id="view-context"
            v-model="form.context_id"
            placeholder="Optional context identifier"
            :disabled="isLoading"
          />
          <p class="text-xs text-muted-foreground">
            Optional context identifier for this view
          </p>
        </div>
      </form>
      
      <DialogFooter>
        <Button
          variant="outline"
          @click="closeDialog"
          :disabled="isLoading"
        >
          Cancel
        </Button>
        <Button
          @click="handleSubmit"
          :disabled="!isFormValid || isLoading"
        >
          <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
          {{ isEditing ? 'Update View' : 'Create View' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
