<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Plus class="w-4 h-4 mr-2" />
        Add
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Connect your Data Source</DialogTitle>
      </DialogHeader>
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div class="space-y-4">
          <div class="space-y-2">
            <Select v-model="form.source_type" :disabled="isLoading">
              <SelectTrigger class="flex items-center gap-2">
                <SelectValue :placeholder="form.source_type ? getSourceTypeLabel(form.source_type) : 'Select database type'" />
                <SelectIcon v-if="form.source_type" as-child>
                  <NuxtImg 
                    :src="getIconPath(form.source_type)" 
                    :alt="form.source_type"
                    class="w-4 h-4"
                  />
                </SelectIcon>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="postgresql">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('postgresql')" 
                      alt="PostgreSQL"
                      class="w-4 h-4"
                    />
                    <span>PostgreSQL</span>
                  </div>
                </SelectItem>
                <SelectItem value="mysql">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('mysql')" 
                      alt="MySQL"
                      class="w-4 h-4"
                    />
                    <span>MySQL</span>
                  </div>
                </SelectItem>
                <SelectItem value="sqlite">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('sqlite')" 
                      alt="SQLite"
                      class="w-4 h-4"
                    />
                    <span>SQLite</span>
                  </div>
                </SelectItem>
                <SelectItem value="oracle">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('oracle')" 
                      alt="Oracle"
                      class="w-4 h-4"
                    />
                    <span>Oracle</span>
                  </div>
                </SelectItem>
                <SelectItem value="bigquery">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('bigquery')" 
                      alt="BigQuery"
                      class="w-4 h-4"
                    />
                    <span>BigQuery</span>
                  </div>
                </SelectItem>
                <SelectItem value="snowflake">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('snowflake')" 
                      alt="Snowflake"
                      class="w-4 h-4"
                    />
                    <span>Snowflake</span>
                  </div>
                </SelectItem>
                <SelectItem value="redshift">
                  <div class="flex items-center gap-2">
                    <NuxtImg 
                      :src="getIconPath('redshift')" 
                      alt="Redshift"
                      class="w-4 h-4"
                    />
                    <span>Redshift</span>
                  </div>
                </SelectItem>
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

        <!-- Advanced Options Collapsible -->
        <Collapsible v-slot="{ open: isAdvancedOpen }">
          <CollapsibleTrigger class="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors w-full">
            <ChevronDown :class="['w-4 h-4 transition-transform duration-200', { 'rotate-180': isAdvancedOpen }]" />
            <span>Advanced</span>
          </CollapsibleTrigger>
          <CollapsibleContent class="space-y-4 pt-4">
            <div class="space-y-2">
              <Label for="name">Name</Label>
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
          </CollapsibleContent>
        </Collapsible>
        
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
import { useDark } from '@vueuse/core'
import { ChevronDown } from 'lucide-vue-next'

// Define emits
const emit = defineEmits<{
  dataSourceCreated: []
}>()
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
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '~/components/ui/collapsible'
import { SelectIcon } from 'reka-ui'
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

// Dark mode detection
const isDark = useDark({
  valueDark: 'dark',
  valueLight: 'light',
  selector: 'html',
  attribute: 'class',
  storageKey: 'cortex-color-scheme'
})

const open = ref(false)
const isLoading = ref(false)
const nameManuallyEdited = ref(false)

const form = reactive({
  name: '',
  alias: '',
  description: '',
  source_catalog: 'DATABASE' as 'DATABASE' | 'API' | 'FILE',
  source_type: '' as 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift',
  config: {} as any
})

// Map source types to icon names
function getIconName(sourceType: string): string {
  const iconMap: Record<string, string> = {
    postgresql: 'postgres',
    mysql: 'mysql',
    sqlite: 'sqlite',
    oracle: 'oracle',
    bigquery: 'bigquery',
    snowflake: 'snowflake',
    redshift: 'redshift'
  }
  return iconMap[sourceType] || sourceType
}

// Get icon path based on source type and dark mode
function getIconPath(sourceType: string): string {
  const iconName = getIconName(sourceType)
  const mode = isDark.value ? 'dark' : 'light'
  return `/icons/brands/${iconName}-${mode}.svg`
}

// Get source type display label
function getSourceTypeLabel(sourceType: string): string {
  const labels: Record<string, string> = {
    postgresql: 'PostgreSQL',
    mysql: 'MySQL',
    sqlite: 'SQLite',
    oracle: 'Oracle',
    bigquery: 'BigQuery',
    snowflake: 'Snowflake',
    redshift: 'Redshift'
  }
  return labels[sourceType] || sourceType
}

// Capitalize first letter of each word
function capitalizeWords(str: string): string {
  return str
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

// Auto-generate name from database configuration
function generateNameFromConfig(): string {
  if (!form.source_type || !form.config) {
    return ''
  }

  const config = form.config
  let hostName = ''

  // Get host name based on source type
  if (form.source_type === 'sqlite') {
    // For SQLite, use database path or filename
    hostName = config.database ? config.database.split('/').pop()?.split('\\').pop()?.replace(/\.[^/.]+$/, '') || 'SQLite' : 'SQLite'
  } else if (form.source_type === 'bigquery') {
    // For BigQuery, use project_id
    hostName = config.project_id || 'BigQuery'
  } else {
    // For other databases, use host
    hostName = config.host || 'Database'
  }

  // Capitalize host name
  const capitalizedHost = capitalizeWords(hostName)

  // Get source type display name
  const sourceTypeNames: Record<string, string> = {
    postgresql: 'PostgreSQL',
    mysql: 'MySQL',
    sqlite: 'SQLite',
    oracle: 'Oracle',
    bigquery: 'BigQuery',
    snowflake: 'Snowflake',
    redshift: 'Redshift'
  }

  const sourceTypeName = sourceTypeNames[form.source_type] || form.source_type

  return `${capitalizedHost} ${sourceTypeName} Dataset`
}

// Auto-generate name when config changes
watch(() => form.config, (newConfig) => {
  if (form.source_type && newConfig && typeof newConfig === 'object' && !nameManuallyEdited.value) {
    const generatedName = generateNameFromConfig()
    if (generatedName) {
      form.name = generatedName
    }
  }
}, { deep: true })

// Track manual name edits and auto-generate alias
watch(() => form.name, (newName) => {
  if (newName) {
    // Mark as manually edited if user types something different from generated name
    const generatedName = generateNameFromConfig()
    if (form.name !== generatedName) {
      nameManuallyEdited.value = true
    }
    
    // Auto-generate alias from name
    if (!aliasManuallyEdited.value) {
    form.alias = generateAlias(newName)
    }
  }
})

// Reset config when source type changes
watch(() => form.source_type, (newType) => {
  if (newType) {
    form.config = getDefaultConfig(newType)
    nameManuallyEdited.value = false
    // Generate name after config is set
    setTimeout(() => {
      const generatedName = generateNameFromConfig()
      if (generatedName && !nameManuallyEdited.value) {
        form.name = generatedName
      }
    }, 0)
  } else {
    form.config = {}
    form.name = ''
    nameManuallyEdited.value = false
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

    const result = await createDataSource({
      environment_id: selectedEnvironmentId.value!,
      name: form.name.trim(),
      alias: form.alias.trim(),
      description: form.description.trim(),
      source_catalog: form.source_catalog,
      source_type: form.source_type,
      config: cleanConfig
    })
    
    toast.success('Data source created successfully')
    
    // Emit event to notify parent component to refresh
    emit('dataSourceCreated')
    
    // Close dialog
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
  form.source_catalog = 'DATABASE' as 'DATABASE' | 'API' | 'FILE'
  form.source_type = '' as any
  form.config = {}
  
  // Reset flags
  nameManuallyEdited.value = false
  resetManualEditFlag()
}
</script> 
