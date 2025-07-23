<script setup lang="ts">
import { ref, computed } from 'vue';
import { useApi } from '~/composables/useApi';
import type { Workspace } from '~/types';
import { Edit } from 'lucide-vue-next';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { Label } from '~/components/ui/label';
import { Textarea } from '~/components/ui/textarea';
import { toast } from 'vue-sonner';

interface Props {
  workspace: Workspace;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  updated: [workspace: Workspace];
}>();

const { apiUrl } = useApi();

const open = ref(false);
const loading = ref(false);

// Form data
const form = ref({
  name: props.workspace.name,
  description: props.workspace.description || ''
});

// Validation
const errors = ref<Record<string, string>>({});

const isValid = computed(() => {
  return form.value.name.trim();
});

function validateForm() {
  errors.value = {};
  
  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required';
  }
  
  return Object.keys(errors.value).length === 0;
}

async function handleSubmit() {
  if (!validateForm()) return;
  
  loading.value = true;
  
  try {
    const response = await $fetch<Workspace>(apiUrl(`/api/v1/workspaces/${props.workspace.id}`), {
      method: 'PUT',
      body: {
        name: form.value.name.trim(),
        description: form.value.description.trim() || null
      }
    });
    
    toast.success('Workspace updated successfully');
    emit('updated', response);
    open.value = false;
  } catch (error: any) {
    console.error('Error updating workspace:', error);
    toast.error(error?.data?.detail || 'Failed to update workspace');
  } finally {
    loading.value = false;
  }
}

function handleOpenChange(newOpen: boolean) {
  if (!newOpen) {
    // Reset form when closing
    form.value = {
      name: props.workspace.name,
      description: props.workspace.description || ''
    };
    errors.value = {};
  }
  open.value = newOpen;
}
</script>

<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Edit class="w-4 h-4 mr-2" />
        Edit
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Edit Workspace</DialogTitle>
        <DialogDescription>
          Update the workspace name and description.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="name">Name *</Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="Enter workspace name"
            :class="{ 'border-red-500': errors.name }"
          />
          <p v-if="errors.name" class="text-sm text-red-500">{{ errors.name }}</p>
        </div>
        
        <div class="space-y-2">
          <Label for="description">Description</Label>
          <Textarea
            id="description"
            v-model="form.description"
            placeholder="Enter description (optional)"
            rows="3"
          />
        </div>
      </form>
      
      <DialogFooter>
        <Button variant="outline" @click="open = false" :disabled="loading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isValid || loading">
          <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Update Workspace
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template> 