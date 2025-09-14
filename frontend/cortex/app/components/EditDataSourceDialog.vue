<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { useApi } from '~/composables/useApi';
import { useDataSources } from '~/composables/useDataSources';
import { useEnvironments } from '~/composables/useEnvironments';
import { useAliasGenerator } from '~/composables/useAliasGenerator';
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

// Import database configuration components
import PostgreSQLConfig from '~/components/data-sources/PostgreSQLConfig.vue'
import MySQLConfig from '~/components/data-sources/MySQLConfig.vue'
import SQLiteConfig from '~/components/data-sources/SQLiteConfig.vue'
import BigQueryConfig from '~/components/data-sources/BigQueryConfig.vue'
import CommonSQLConfig from '~/components/data-sources/CommonSQLConfig.vue'

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
const {
  generateAlias,
  validateAlias,
  getAliasError,
  aliasManuallyEdited,
  markAsManuallyEdited,
  resetManualEditFlag
} = useAliasGenerator();

const open = ref(false);
const loading = ref(false);

// Form data
const form = reactive({
  name: props.dataSource.name,
  alias: props.dataSource.alias || '',
  description: props.dataSource.description || '',
  source_catalog: props.dataSource.source_catalog,
  source_type: props.dataSource.source_type,
  config: props.dataSource.config || {},
  environment_id: props.dataSource.environment_id
});

// Auto-generate alias from name unless manually edited
watch(() => form.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    form.alias = generateAlias(newName);
  }
});

// Ensure dialect is always set correctly in config
watch(() => form.config, (newConfig) => {
  if (form.source_type && newConfig && typeof newConfig === 'object') {
    // For SQL databases, ensure dialect matches the current source type
    if (['postgresql', 'mysql', 'sqlite', 'oracle', 'snowflake', 'redshift'].includes(form.source_type)) {
      newConfig.dialect = form.source_type
    }
  }
}, { deep: true })

// Update dialect when source type changes
watch(() => form.source_type, (newSourceType, oldSourceType) => {
  if (newSourceType && newSourceType !== oldSourceType && form.config && typeof form.config === 'object') {
    // For SQL databases, update dialect to match new source type
    if (['postgresql', 'mysql', 'sqlite', 'oracle', 'snowflake', 'redshift'].includes(newSourceType)) {
      form.config.dialect = newSourceType
    } else {
      // For non-SQL databases (like BigQuery), remove dialect if it exists
      delete form.config.dialect
    }
  }
})

const aliasError = computed(() => getAliasError(form.alias));

const isFormValid = computed(() => {
  return form.name.trim() &&
         form.alias.trim() &&
         validateAlias(form.alias) &&
         form.source_catalog &&
         form.source_type &&
         form.environment_id &&
         isConfigValid.value;
});

const isConfigValid = computed(() => {
  if (!form.source_type) return false;

  const config = form.config;

  switch (form.source_type) {
    case 'postgresql':
    case 'mysql':
      return config.host && config.port && config.username && config.password && config.database && config.dialect;
    case 'sqlite':
      return config.database && config.dialect;
    case 'bigquery':
      return config.project_id && config.service_account_details &&
             Object.keys(config.service_account_details).length > 0;
    case 'oracle':
    case 'snowflake':
    case 'redshift':
      return config.host && config.port && config.username && config.password && config.database && config.dialect;
    default:
      return false;
  }
});

async function handleSubmit() {
  if (!isFormValid.value) {
    toast.error('Please fill in all required fields correctly');
    return;
  }

  loading.value = true;

  try {
    // Clean up config by removing UI-only fields
    const cleanConfig = { ...form.config };
    if ('serviceAccountJson' in cleanConfig) {
      delete cleanConfig.serviceAccountJson;
    }

    const response = await $fetch<DataSource>(apiUrl(`/api/v1/data/sources/${props.dataSource.id}`), {
      method: 'PUT',
      body: {
        name: form.name.trim(),
        description: form.description.trim() || null,
        alias: form.alias.trim() || null,
        source_catalog: form.source_catalog,
        source_type: form.source_type,
        config: cleanConfig,
        environment_id: form.environment_id
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

function resetAndClose() {
  open.value = false;

  // Reset form to original data source values
  form.name = props.dataSource.name;
  form.alias = props.dataSource.alias || '';
  form.description = props.dataSource.description || '';
  form.source_catalog = props.dataSource.source_catalog;
  form.source_type = props.dataSource.source_type;
  form.config = { ...props.dataSource.config };
  form.environment_id = props.dataSource.environment_id;

  // Ensure dialect is set correctly
  if (form.source_type && form.config && typeof form.config === 'object') {
    if (['postgresql', 'mysql', 'sqlite', 'oracle', 'snowflake', 'redshift'].includes(form.source_type)) {
      form.config.dialect = form.source_type;
    } else {
      // For non-SQL databases, remove dialect if it exists
      delete form.config.dialect;
    }
  }

  // Reset alias generator state
  resetManualEditFlag();
}

function handleOpenChange(newOpen: boolean) {
  if (!newOpen) {
    resetAndClose();
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
    <DialogContent class="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Edit Data Source</DialogTitle>
        <DialogDescription>
          Update the data source configuration and settings.
        </DialogDescription>
      </DialogHeader>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div class="space-y-4">
          <div class="space-y-2">
            <Label for="name">Data Source Name</Label>
            <Input
              id="name"
              v-model="form.name"
              placeholder="Enter data source name"
              :disabled="loading"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="alias">Alias</Label>
            <Input
              id="alias"
              v-model="form.alias"
              placeholder="Auto-generated from name"
              :disabled="loading"
              required
              @blur="markAsManuallyEdited"
            />
            <p v-if="aliasError" class="text-xs text-red-500">{{ aliasError }}</p>
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="form.description"
              placeholder="Enter data source description"
              :disabled="loading"
              rows="3"
            />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="source_catalog">Source Catalog</Label>
            <Select v-model="form.source_catalog" :disabled="loading">
              <SelectTrigger>
                <SelectValue placeholder="Select catalog" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DATABASE">Database</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="source_type">Source Type</Label>
            <Select v-model="form.source_type" :disabled="loading || form.source_catalog !== 'DATABASE'">
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="postgresql">PostgreSQL</SelectItem>
                <SelectItem value="mysql">MySQL</SelectItem>
                <SelectItem value="sqlite">SQLite</SelectItem>
                <SelectItem value="oracle">Oracle</SelectItem>
                <SelectItem value="bigquery">BigQuery</SelectItem>
                <SelectItem value="snowflake">Snowflake</SelectItem>
                <SelectItem value="redshift">Redshift</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="space-y-2">
          <Label for="environment_id">Environment</Label>
          <Select v-model="form.environment_id" :disabled="loading">
            <SelectTrigger>
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
        </div>

        <!-- Dynamic Configuration Section -->
        <div v-if="form.source_type" class="space-y-2">
          <Label class="text-base font-medium">Database Configuration</Label>
          <div class="border rounded-lg p-4 bg-muted/50">
            <PostgreSQLConfig
              v-if="form.source_type === 'postgresql'"
              v-model="form.config"
              :disabled="loading"
            />
            <MySQLConfig
              v-else-if="form.source_type === 'mysql'"
              v-model="form.config"
              :disabled="loading"
            />
            <SQLiteConfig
              v-else-if="form.source_type === 'sqlite'"
              v-model="form.config"
              :disabled="loading"
            />
            <BigQueryConfig
              v-else-if="form.source_type === 'bigquery'"
              v-model="form.config"
              :disabled="loading"
            />
            <CommonSQLConfig
              v-else-if="['oracle', 'snowflake', 'redshift'].includes(form.source_type)"
              v-model="form.config"
              :database-type="form.source_type as 'oracle' | 'snowflake' | 'redshift'"
              :disabled="loading"
            />
            <div v-else class="text-center py-4 text-muted-foreground">
              <p>Configuration form will appear when you select a supported database type.</p>
            </div>
          </div>
        </div>
      </form>

      <DialogFooter>
        <Button type="button" variant="outline" @click="resetAndClose" :disabled="loading">
          Cancel
        </Button>
        <Button @click="handleSubmit" :disabled="!isFormValid || loading">
          <div v-if="loading" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Update Data Source
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template> 