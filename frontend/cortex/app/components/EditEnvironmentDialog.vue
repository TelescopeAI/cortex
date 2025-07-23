<script setup lang="ts">
import { ref, computed } from 'vue';
import { useApi } from '~/composables/useApi';
import { useWorkspaces } from '~/composables/useWorkspaces';
import type { Environment } from '~/types';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { toast } from 'vue-sonner';

interface Props {
  environment: Environment;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  updated: [environment: Environment];
}>();

const { apiUrl } = useApi();
const { workspaces } = useWorkspaces();

const open = ref(false);
const loading = ref(false);

// Form data
const form = ref({
  name: props.environment.name,
  description: props.environment.description || '',
  workspace_id: props.environment.workspace_id
});

// Validation
const errors = ref<Record<string, string>>({});

const isValid = computed(() => {
  return form.value.name.trim() && form.value.workspace_id;
});

function validateForm() {
  errors.value = {};
  
  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required';
  }
  
  if (!form.value.workspace_id) {
    errors.value.workspace_id = 'Workspace is required';
  }
  
  return Object.keys(errors.value).length === 0;
}

async function handleSubmit() {
  if (!validateForm()) return;
  
  loading.value = true;
  
  try {
    const response = await $fetch<Environment>(apiUrl(`/api/v1/environments/${props.environment.id}`), {
      method: 'PUT',
      body: {
        name: form.value.name.trim(),
        description: form.value.description.trim() || null,
        workspace_id: form.value.workspace_id
      }
    });
    
    toast.success('Environment updated successfully');
    emit('updated', response);
    open.value = false;
  } catch (error: any) {
    console.error('Error updating environment:', error);
    toast.error(error?.data?.detail || 'Failed to update environment');
  } finally {
    loading.value = false;
  }
}

function handleOpenChange(newOpen: boolean) {
  if (!newOpen) {
    // Reset form when closing
    form.value = {
      name: props.environment.name,
      description: props.environment.description || '',
      workspace_id: props.environment.workspace_id
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
        <DialogTitle>Edit Environment</DialogTitle>
        <DialogDescription>
          Update the environment name, description, and workspace.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="name">Name *</Label>
          <Input
            id="name"
            v-model="form.name"
            placeholder="Enter environment name"
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
        
        <div class="space-y-2">
          <Label for="workspace_id">Workspace *</Label>
          <Select v-model="form.workspace_id">
            <SelectTrigger :class="{ 'border-red-500': errors.workspace_id }">
              <SelectValue placeholder="Select workspace" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem 
                v-for="ws in workspaces" 
                :key="ws.id" 
                :value="ws.id"
              >
                {{ ws.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          <p v-if="errors.workspace_id" class="text-sm text-red-500">{{ errors.workspace_id }}</p>
        </div>
      </form>
      
      <DialogFooter>
        <Button variant="outline" @click="open = false" :disabled="loading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isValid || loading">
          <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Update Environment
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template> 