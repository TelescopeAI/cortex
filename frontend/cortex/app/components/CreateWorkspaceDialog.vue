<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Plus class="w-4 h-4 mr-2" />
        Create Workspace
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Create New Workspace</DialogTitle>
        <DialogDescription>
          Create a new workspace to organize your data and environments.
        </DialogDescription>
      </DialogHeader>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="name">Workspace Name</Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="Enter workspace name"
            :disabled="isLoading"
            required
          />
        </div>
        <div class="space-y-2">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="form.description"
            placeholder="Enter workspace description"
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
            Create Workspace
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { toast } from 'vue-sonner'
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

const { createWorkspace } = useWorkspaces()

const open = ref(false)
const isLoading = ref(false)

const form = reactive({
  name: '',
  description: ''
})

async function handleSubmit() {
  if (!form.name.trim()) {
    toast.error('Workspace name is required')
    return
  }

  isLoading.value = true
  
  try {
    await createWorkspace({
      name: form.name.trim(),
      description: form.description.trim()
    })
    
    toast.success('Workspace created successfully')
    open.value = false
    
    // Reset form
    form.name = ''
    form.description = ''
  } catch (error) {
    console.error('Failed to create workspace:', error)
    toast.error('Failed to create workspace')
  } finally {
    isLoading.value = false
  }
}
</script> 