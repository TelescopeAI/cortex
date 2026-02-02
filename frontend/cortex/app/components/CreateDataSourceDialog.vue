<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm" class="cursor-pointer">
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
                <SelectValue :placeholder="form.source_type ? DATA_SOURCE_TYPES[form.source_type]?.label : 'Select database type'" />
                <SelectIcon v-if="form.source_type" as-child>
                  <DataSourceIcon :source-type="form.source_type" size="sm" />
                </SelectIcon>
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="sourceType in getOrderedSourceTypes()"
                  :key="sourceType.type"
                  :value="sourceType.type"
                >
                  <div class="flex items-center gap-2">
                    <DataSourceIcon :source-type="sourceType.type" size="sm" />
                    <span>{{ sourceType.label }}</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <!-- Dynamic Configuration Section -->
        <div v-if="form.source_type" class="space-y-2">
          <Label class="text-base font-medium">
            {{ form.source_type === 'spreadsheet' ? 'Spreadsheet Configuration' : 'Database Configuration' }}
          </Label>
          <div class="border rounded-lg p-4 bg-muted/50">
            <div v-if="form.source_type === 'spreadsheet'" class="space-y-4">
              <div class="space-y-2">
                <Label for="file-select">Select File</Label>
                <Select v-model="(form.config as any).file_id" :disabled="loadingFiles">
                  <SelectTrigger id="file-select">
                    <SelectValue :placeholder="loadingFiles ? 'Loading files...' : 'Choose a file'">
                      {{ getSelectedFileName() || (loadingFiles ? 'Loading files...' : 'Choose a file') }}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="file in uploadedFiles" :key="file.id" :value="file.id">
                      <div class="flex items-center justify-between w-full gap-3">
                        <span class="font-medium">{{ file.name }}.{{ file.extension }}</span>
                        <span class="text-xs text-muted-foreground">{{ formatRelativeTime(file.updated_at) }}</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p v-if="uploadedFiles.length === 0 && !loadingFiles" class="text-xs text-muted-foreground">
                  No files uploaded yet. Please upload files first using the "Manage Files" option.
                </p>
              </div>
            </div>

            <PostgreSQLConfig 
              v-else-if="form.source_type === 'postgresql'"
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
          <Button
            type="submit"
            :disabled="isLoading || !isFormValid"
            :class="[
              'cursor-pointer transition-all',
              isLoading
            ]"
          >
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            {{ isLoading ? 'Connecting...' : 'Connect' }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { useDark, useTimeAgo } from '@vueuse/core'
import { ChevronDown } from 'lucide-vue-next'
import { DATA_SOURCE_TYPES, getOrderedSourceTypes } from '~/config/dataSourceTypes'
import DataSourceIcon from '~/components/data-sources/DataSourceIcon.vue'
import type { DatabaseConfig } from '~/types'

// Define props
const props = defineProps<{
  initialSourceType?: string
  initialFileId?: string
  initialFileName?: string
  autoOpen?: boolean
}>()

// Define emits
const emit = defineEmits<{
  dataSourceCreated: [dataSource: import('~/types').DataSource]
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
import { useSpreadsheets } from '~/composables/useSpreadsheets'

const { createDataSource } = useDataSources()
const { selectedEnvironmentId } = useEnvironments()
const { discoverSheets, listUploadedFiles } = useSpreadsheets()
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
const uploadedFiles = ref<Array<{ id: string; name: string; extension: string; size: number; mime_type: string; hash: string; created_at: string; updated_at: string }>>([])
const loadingFiles = ref(false)

const form = reactive({
  name: '',
  alias: '',
  description: '',
  source_catalog: 'DATABASE' as 'DATABASE' | 'API' | 'FILE',
  source_type: '' as keyof typeof DATA_SOURCE_TYPES | '',
  config: {} as DatabaseConfig,
  discoveredSheets: [] as import('~/types').SheetMetadata[],
})


// Capitalize first letter of each word
function capitalizeWords(str: string): string {
  return str
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

// Convert UTC date to local timezone
const convertUTCToLocal = (dateString: string): Date => {
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

// Format relative time
const formatRelativeTime = (date: string | Date) => {
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, {
    updateInterval: 1000
  })
}

// Get selected file name for display
function getSelectedFileName(): string {
  const config = form.config as any
  if (!config.file_id || uploadedFiles.value.length === 0) {
    return ''
  }
  const selectedFile = uploadedFiles.value.find(f => f.id === config.file_id)
  return selectedFile ? `${selectedFile.name}.${selectedFile.extension}` : ''
}

// Auto-generate name from database configuration
function generateNameFromConfig(): string {
  if (!form.source_type || !form.config) {
    return ''
  }

  const metadata = DATA_SOURCE_TYPES[form.source_type]
  if (!metadata || !metadata.generateName) {
    return metadata?.label || ''
  }

  return metadata.generateName(form.config as any) || metadata.label
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
    form.config = getDefaultConfig(newType) as any
    nameManuallyEdited.value = false
    // Generate name after config is set
    setTimeout(() => {
      const generatedName = generateNameFromConfig()
      if (generatedName && !nameManuallyEdited.value) {
        form.name = generatedName
      }
    }, 0)
  } else {
    form.config = {} as any
    form.name = ''
    nameManuallyEdited.value = false
  }
})

// Ensure dialect is always set correctly in config
watch(() => form.config, (newConfig) => {
  if (form.source_type && newConfig && typeof newConfig === 'object') {
    // For SQL databases, ensure dialect matches the current source type
    if (['postgresql', 'mysql', 'sqlite'].includes(form.source_type)) {
      (newConfig as any).dialect = form.source_type
    }
  }
}, { deep: true })

// Update dialect when source type changes
watch(() => form.source_type, (newSourceType, oldSourceType) => {
  if (newSourceType && newSourceType !== oldSourceType && form.config && typeof form.config === 'object') {
    const config = form.config as any
    // For SQL databases, update dialect to match new source type
    if (['postgresql', 'mysql', 'sqlite'].includes(newSourceType)) {
      config.dialect = newSourceType
    } else if (newSourceType === 'spreadsheet') {
      // For spreadsheet, remove dialect
      delete config.dialect
    } else {
      // For non-SQL databases (like BigQuery), remove dialect if it exists
      delete config.dialect
    }
  }
})

// Load uploaded files when CSV provider is selected
watch(() => (form.config as any).provider_type, async (newProviderType) => {
  if (newProviderType === 'csv' && selectedEnvironmentId.value) {
    loadingFiles.value = true
    try {
      const files = await listUploadedFiles(selectedEnvironmentId.value)
      uploadedFiles.value = files
      // Clear the file_id if no files available
      if (files.length === 0) {
        (form.config as any).file_id = ''
      }
    } catch (error) {
      console.error('Failed to load uploaded files:', error)
      uploadedFiles.value = []
    } finally {
      loadingFiles.value = false
    }
  }
})

// Watch for file selection changes and update name/alias
watch(() => (form.config as any).file_id, (newFileId) => {
  if (newFileId && form.source_type === 'spreadsheet' && uploadedFiles.value.length > 0) {
    const selectedFile = uploadedFiles.value.find(f => f.id === newFileId)
    if (selectedFile && !nameManuallyEdited.value) {
      // Generate name from file name
      const titleCaseName = capitalizeWords(selectedFile.name)
      form.name = titleCaseName
      // Alias will be auto-generated by the watch on form.name
    }
  }
})

// Handle initial props for auto-opening with prefilled data
watch(() => props.autoOpen, async (shouldAutoOpen) => {
  if (shouldAutoOpen && props.initialSourceType === 'spreadsheet' && selectedEnvironmentId.value) {
    open.value = true

    // Set source type to spreadsheet
    form.source_type = 'spreadsheet' as any
    form.source_catalog = 'FILE'

    // Load files first, then set the config with file_id
    if (props.initialFileId) {
      loadingFiles.value = true
      try {
        const files = await listUploadedFiles(selectedEnvironmentId.value)
        uploadedFiles.value = files

        // Now set the config with file_id after files are loaded
        // This ensures the file_id watcher can find the file in uploadedFiles
        await nextTick()
        form.config = {
          provider_type: 'csv',
          file_id: props.initialFileId
        }

        // Name and alias will be set by the file_id watcher above
      } catch (error) {
        console.error('Failed to load uploaded files:', error)
        uploadedFiles.value = []
        form.config = {
          provider_type: 'csv',
          file_id: ''
        }
      } finally {
        loadingFiles.value = false
      }
    } else {
      // Set provider type to CSV without file_id
      form.config = {
        provider_type: 'csv',
        file_id: ''
      }

      if (props.initialFileName) {
        // Fallback: if no file_id but fileName provided, use fileName for name
        const decodedFileName = decodeURIComponent(props.initialFileName.replace(/\+/g, ' '))
        const titleCaseName = capitalizeWords(decodedFileName)
        form.name = titleCaseName
      }
    }
  }
}, { immediate: true })

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

  const metadata = DATA_SOURCE_TYPES[form.source_type]
  if (!metadata) return false

  return metadata.validateConfig(form.config as any)
})

function getDefaultConfig(sourceType: string): any {
  const metadata = DATA_SOURCE_TYPES[sourceType]
  return metadata ? { ...metadata.defaultConfig } : {}
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
      source_type: form.source_type as any,
      config: cleanConfig
    })
    
    toast.success('Data source created successfully')
    
    // Emit event to notify parent component with the created data source
    emit('dataSourceCreated', result)
    
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
  form.source_type = ''
  form.config = {} as any

  // Reset flags
  nameManuallyEdited.value = false
  resetManualEditFlag()
}
</script>

<style scoped>
.gradient-ring {
  position: relative;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1),
              0 0 0 4px transparent;
  animation: gradient-ring-animation 2s ease-in-out infinite;
}

.gradient-ring::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: inherit;
  padding: 3px;
  background: linear-gradient(45deg,
    rgb(59, 130, 246),
    rgb(147, 51, 234),
    rgb(236, 72, 153),
    rgb(59, 130, 246)
  );
  background-size: 300% 300%;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  pointer-events: none;
  animation: gradient-animation 3s ease infinite;
}

@keyframes gradient-animation {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

@keyframes gradient-ring-animation {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}
</style>
