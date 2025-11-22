<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <slot name="trigger">
      <Button variant="outline" size="sm">
        <Plus class="w-4 h-4 mr-2" />
        Create Environment
      </Button>
      </slot>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Create New Environment</DialogTitle>
        <DialogDescription>
          Create a new environment for the selected workspace.
        </DialogDescription>
      </DialogHeader>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="name">Environment Name</Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="Enter environment name"
            :disabled="isLoading"
            required
          />
        </div>
        <div class="space-y-2">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="form.description"
            placeholder="Enter environment description"
            :disabled="isLoading"
            rows="3"
          />
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" @click="open = false" :disabled="isLoading">
            Cancel
          </Button>
          <Button type="submit" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            Create Environment
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { toast } from 'vue-sonner'
import { useEnvironments } from '~/composables/useEnvironments'
import { useWorkspaces } from '~/composables/useWorkspaces'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Plus, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  workspaceId?: string
}>()

const { createEnvironment, selectEnvironment } = useEnvironments()
const { selectedWorkspaceId, selectWorkspace } = useWorkspaces()

// Use provided workspaceId or fall back to selected workspace
const targetWorkspaceId = computed(() => props.workspaceId || selectedWorkspaceId.value)

const open = ref(false)
const isLoading = ref(false)

const form = reactive({
  name: '',
  description: ''
})

async function handleSubmit() {
  if (!form.name.trim()) {
    toast.error('Environment name is required')
    return
  }

  if (!targetWorkspaceId.value) {
    toast.error('Please select a workspace first')
    return
  }

  isLoading.value = true
  
  try {
    const createdEnvironment = await createEnvironment({
      name: form.name.trim(),
      description: form.description.trim(),
      workspace_id: targetWorkspaceId.value
    })
    
    // Automatically select the workspace and newly created environment
    if (targetWorkspaceId.value) {
      selectWorkspace(targetWorkspaceId.value)
    }
    if (createdEnvironment?.id) {
      selectEnvironment(createdEnvironment.id)
    }
    
    toast.success('Environment created successfully')
    open.value = false
    
    // Reset form
    form.name = ''
    form.description = ''
  } catch (error) {
    console.error('Failed to create environment:', error)
    toast.error('Failed to create environment')
  } finally {
    isLoading.value = false
  }
}
</script> 