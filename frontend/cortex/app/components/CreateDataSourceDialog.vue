<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Plus class="w-4 h-4 mr-2" />
        Create Data Source
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Create New Data Source</DialogTitle>
        <DialogDescription>
          Create a new data source to connect to external data systems.
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
              :disabled="isLoading"
              required
            />
          </div>
          
          <div class="space-y-2">
            <Label for="alias">Alias</Label>
            <Input
              id="alias"
              v-model="form.alias"
              placeholder="Auto-generated from name"
              :disabled="isLoading"
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
              :disabled="isLoading"
              rows="3"
            />
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="source_catalog">Source Catalog</Label>
            <Select v-model="form.source_catalog" :disabled="isLoading">
              <SelectTrigger>
                <SelectValue placeholder="Select catalog" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DATABASE">Database</SelectItem>
                <SelectItem value="API" disabled>API (Coming Soon)</SelectItem>
                <SelectItem value="FILE" disabled>File (Coming Soon)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div class="space-y-2">
            <Label for="source_type">Source Type</Label>
            <Select v-model="form.source_type" :disabled="isLoading || form.source_catalog !== 'DATABASE'">
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
        
        <!-- Dynamic Configuration Section -->
        <div v-if="form.source_type" class="space-y-2">
          <Label class="text-base font-medium">Database Configuration</Label>
          <div class="border rounded-lg p-4 bg-muted/50">
            <PostgreSQLConfig 
              v-if="form.source_type === 'postgresql'"
              v-model="form.config"
              :disabled="isLoading"
            />
            <MySQLConfig 
              v-else-if="form.source_type === 'mysql'"
              v-model="form.config"
              :disabled="isLoading"
            />
            <SQLiteConfig 
              v-else-if="form.source_type === 'sqlite'"
              v-model="form.config"
              :disabled="isLoading"
            />
            <BigQueryConfig
              v-else-if="form.source_type === 'bigquery'"
              v-model="form.config"
              :disabled="isLoading"
            />
            <CommonSQLConfig 
              v-else-if="['oracle', 'snowflake', 'redshift'].includes(form.source_type)"
              v-model="form.config"
              :database-type="form.source_type as 'oracle' | 'snowflake' | 'redshift'"
              :disabled="isLoading"
            />
            <div v-else class="text-center py-4 text-muted-foreground">
              <p>Configuration form will appear when you select a supported database type.</p>
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button type="button" variant="outline" @click="resetAndClose" :disabled="isLoading">
            Cancel
          </Button>
          <Button type="submit" :disabled="isLoading || !isFormValid">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            Create Data Source
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { toast } from 'vue-sonner'
import { useDataSources } from '~/composables/useDataSources'
import { useEnvironments } from '~/composables/useEnvironments'
import { useAliasGenerator } from '~/composables/useAliasGenerator'
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Plus, Loader2 } from 'lucide-vue-next'

// Import database configuration components
import PostgreSQLConfig from '~/components/data-sources/PostgreSQLConfig.vue'
import MySQLConfig from '~/components/data-sources/MySQLConfig.vue'
import SQLiteConfig from '~/components/data-sources/SQLiteConfig.vue'
import BigQueryConfig from '~/components/data-sources/BigQueryConfig.vue'
import CommonSQLConfig from '~/components/data-sources/CommonSQLConfig.vue'


const { createDataSource } = useDataSources()
const { selectedEnvironmentId } = useEnvironments()
const { 
  generateAlias, 
  validateAlias, 
  getAliasError, 
  aliasManuallyEdited, 
  markAsManuallyEdited,
  resetManualEditFlag
} = useAliasGenerator()

const open = ref(false)
const isLoading = ref(false)

const form = reactive({
  name: '',
  alias: '',
  description: '',
  source_catalog: '' as 'DATABASE' | 'API' | 'FILE',
  source_type: '' as 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift',
  config: {} as any
})

// Auto-generate alias from name
watch(() => form.name, (newName) => {
  if (newName && !aliasManuallyEdited.value) {
    form.alias = generateAlias(newName)
  }
})

// Reset config when source type changes
watch(() => form.source_type, (newType) => {
  if (newType) {
    form.config = getDefaultConfig(newType)
  } else {
    form.config = {}
  }
})

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

// Reset source type when catalog changes away from DATABASE
watch(() => form.source_catalog, (newCatalog) => {
  if (newCatalog !== 'DATABASE') {
    form.source_type = '' as any
    form.config = {}
  }
})

const aliasError = computed(() => getAliasError(form.alias))

const isFormValid = computed(() => {
  return form.name.trim() &&
         form.alias.trim() &&
         validateAlias(form.alias) &&
         form.source_catalog &&
         form.source_type &&
         selectedEnvironmentId.value &&
         isConfigValid.value
})

const isConfigValid = computed(() => {
  if (!form.source_type) return false
  
  const config = form.config
  
  switch (form.source_type) {
    case 'postgresql':
    case 'mysql':
      return config.host && config.port && config.username && config.password && config.database && config.dialect
    case 'sqlite':
      return config.database && config.dialect
    case 'bigquery':
      return config.project_id && config.service_account_details &&
             Object.keys(config.service_account_details).length > 0
    case 'oracle':
    case 'snowflake':
    case 'redshift':
      return config.host && config.port && config.username && config.password && config.database && config.dialect
    default:
      return false
  }
})

function getDefaultConfig(sourceType: string): any {
  switch (sourceType) {
    case 'postgresql':
      return {
        host: '',
        port: 5432,
        username: '',
        password: '',
        database: '',
        dialect: 'postgresql'
      }
    case 'mysql':
      return {
        host: '',
        port: 3306,
        username: '',
        password: '',
        database: '',
        dialect: 'mysql'
      }
    case 'sqlite':
      return {
        database: '',
        dialect: 'sqlite'
      }
    case 'bigquery':
      return {
        project_id: '',
        dataset_id: '',
        service_account_details: {},
        serviceAccountJson: ''
      }
      // Note: BigQuery doesn't need a dialect field
    case 'oracle':
      return {
        host: '',
        port: 1521,
        username: '',
        password: '',
        database: '',
        dialect: 'oracle'
      }
    case 'snowflake':
      return {
        host: '',
        port: 443,
        username: '',
        password: '',
        database: '',
        dialect: 'snowflake'
      }
    case 'redshift':
      return {
        host: '',
        port: 5439,
        username: '',
        password: '',
        database: '',
        dialect: 'redshift'
      }
    default:
      return {}
  }
}

async function handleSubmit() {
  if (!isFormValid.value) {
    toast.error('Please fill in all required fields correctly')
    return
  }

  isLoading.value = true
  
  try {
    // Clean up config by removing UI-only fields
    const cleanConfig = { ...form.config }
    if ('serviceAccountJson' in cleanConfig) {
      delete cleanConfig.serviceAccountJson
    }

    await createDataSource({
      environment_id: selectedEnvironmentId.value!,
      name: form.name.trim(),
      alias: form.alias.trim(),
      description: form.description.trim(),
      source_catalog: form.source_catalog,
      source_type: form.source_type,
      config: cleanConfig
    })
    
    toast.success('Data source created successfully')
    resetAndClose()
  } catch (error) {
    console.error('Failed to create data source:', error)
    toast.error('Failed to create data source')
  } finally {
    isLoading.value = false
  }
}

function resetAndClose() {
  open.value = false
  
  // Reset form
  form.name = ''
  form.alias = ''
  form.description = ''
  form.source_catalog = '' as 'DATABASE' | 'API' | 'FILE'
  form.source_type = '' as any
  form.config = {}
  
  // Reset alias generator state
  resetManualEditFlag()
}
</script> 