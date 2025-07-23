<script setup lang="ts">
import { ref, computed } from 'vue';
import { useApi } from '~/composables/useApi';
import { useDataSources } from '~/composables/useDataSources';
import { useEnvironments } from '~/composables/useEnvironments';
import type { DataSource } from '~/types';
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
  dataSource: DataSource;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  updated: [dataSource: DataSource];
}>();

const { apiUrl } = useApi();
const { dataSources } = useDataSources();
const { environments } = useEnvironments();

const open = ref(false);
const loading = ref(false);

// Form data
const form = ref({
  name: props.dataSource.name,
  description: props.dataSource.description || '',
  alias: props.dataSource.alias || '',
  source_catalog: props.dataSource.source_catalog,
  source_type: props.dataSource.source_type,
  config: JSON.stringify(props.dataSource.config, null, 2),
  environment_id: props.dataSource.environment_id
});

// Validation
const errors = ref<Record<string, string>>({});

const isValid = computed(() => {
  return form.value.name.trim() && 
         form.value.source_catalog && 
         form.value.source_type &&
         form.value.environment_id;
});

function validateForm() {
  errors.value = {};
  
  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required';
  }
  
  if (!form.value.source_catalog) {
    errors.value.source_catalog = 'Source catalog is required';
  }
  
  if (!form.value.source_type) {
    errors.value.source_type = 'Source type is required';
  }
  
  if (!form.value.environment_id) {
    errors.value.environment_id = 'Environment is required';
  }
  
  return Object.keys(errors.value).length === 0;
}

async function handleSubmit() {
  if (!validateForm()) return;
  
  loading.value = true;
  
  try {
    const response = await $fetch<DataSource>(apiUrl(`/api/v1/data/sources/${props.dataSource.id}`), {
      method: 'PUT',
      body: {
        name: form.value.name.trim(),
        description: form.value.description.trim() || null,
        alias: form.value.alias.trim() || null,
        source_catalog: form.value.source_catalog,
        source_type: form.value.source_type,
        config: JSON.parse(form.value.config),
        environment_id: form.value.environment_id
      }
    });
    
    toast.success('Data source updated successfully');
    emit('updated', response);
    open.value = false;
  } catch (error: any) {
    console.error('Error updating data source:', error);
    toast.error(error?.data?.detail || 'Failed to update data source');
  } finally {
    loading.value = false;
  }
}

function handleOpenChange(newOpen: boolean) {
  if (!newOpen) {
    // Reset form when closing
    form.value = {
      name: props.dataSource.name,
      description: props.dataSource.description || '',
      alias: props.dataSource.alias || '',
      source_catalog: props.dataSource.source_catalog,
      source_type: props.dataSource.source_type,
      config: JSON.stringify(props.dataSource.config, null, 2),
      environment_id: props.dataSource.environment_id
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
    <DialogContent class="sm:max-w-[600px]">
      <DialogHeader>
        <DialogTitle>Edit Data Source</DialogTitle>
        <DialogDescription>
          Update the data source configuration and settings.
        </DialogDescription>
      </DialogHeader>
      
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="name">Name *</Label>
            <Input
              id="name"
              v-model="form.name"
              placeholder="Enter data source name"
              :class="{ 'border-red-500': errors.name }"
            />
            <p v-if="errors.name" class="text-sm text-red-500">{{ errors.name }}</p>
          </div>
          
          <div class="space-y-2">
            <Label for="alias">Alias</Label>
            <Input
              id="alias"
              v-model="form.alias"
              placeholder="Enter alias (optional)"
            />
          </div>
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
        
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="source_catalog">Source Catalog *</Label>
            <Select v-model="form.source_catalog">
              <SelectTrigger :class="{ 'border-red-500': errors.source_catalog }">
                <SelectValue placeholder="Select catalog" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DATABASE">Database</SelectItem>
                <SelectItem value="API">API</SelectItem>
                <SelectItem value="FILE">File</SelectItem>
              </SelectContent>
            </Select>
            <p v-if="errors.source_catalog" class="text-sm text-red-500">{{ errors.source_catalog }}</p>
          </div>
          
          <div class="space-y-2">
            <Label for="source_type">Source Type *</Label>
            <Select v-model="form.source_type">
              <SelectTrigger :class="{ 'border-red-500': errors.source_type }">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="postgresql">PostgreSQL</SelectItem>
                <SelectItem value="mysql">MySQL</SelectItem>
                <SelectItem value="mongodb">MongoDB</SelectItem>
                <SelectItem value="rest">REST API</SelectItem>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
              </SelectContent>
            </Select>
            <p v-if="errors.source_type" class="text-sm text-red-500">{{ errors.source_type }}</p>
          </div>
        </div>
        
        <div class="space-y-2">
          <Label for="environment_id">Environment *</Label>
          <Select v-model="form.environment_id">
            <SelectTrigger :class="{ 'border-red-500': errors.environment_id }">
              <SelectValue placeholder="Select environment" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem 
                v-for="env in environments" 
                :key="env.id" 
                :value="env.id"
              >
                {{ env.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          <p v-if="errors.environment_id" class="text-sm text-red-500">{{ errors.environment_id }}</p>
        </div>
        
        <div class="space-y-2">
          <Label for="config">Configuration (JSON)</Label>
          <Textarea
            id="config"
            v-model="form.config"
            placeholder='{"host": "localhost", "port": "5432", ...}'
            rows="6"
            class="font-mono text-sm"
          />
        </div>
      </form>
      
      <DialogFooter>
        <Button variant="outline" @click="open = false" :disabled="loading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isValid || loading">
          <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Update Data Source
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template> 