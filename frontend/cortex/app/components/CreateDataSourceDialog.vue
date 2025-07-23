<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Plus class="w-4 h-4 mr-2" />
        Create Data Source
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[500px]">
      <DialogHeader>
        <DialogTitle>Create New Data Source</DialogTitle>
        <DialogDescription>
          Create a new data source to connect to external data systems.
        </DialogDescription>
      </DialogHeader>
      <form @submit.prevent="handleSubmit" class="space-y-4">
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
            placeholder="Enter alias (e.g., main_db, api_endpoint)"
            :disabled="isLoading"
            required
          />
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
        
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label for="source_catalog">Source Catalog</Label>
            <Select v-model="form.source_catalog" :disabled="isLoading">
              <SelectTrigger>
                <SelectValue placeholder="Select catalog" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="DATABASE">Database</SelectItem>
                <SelectItem value="API">API</SelectItem>
                <SelectItem value="FILE">File</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div class="space-y-2">
            <Label for="source_type">Source Type</Label>
            <Select v-model="form.source_type" :disabled="isLoading">
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
                <SelectItem value="mongodb">MongoDB</SelectItem>
                <SelectItem value="dynamodb">DynamoDB</SelectItem>
                <SelectItem value="couchbase">Couchbase</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div class="space-y-2">
          <Label for="config">Configuration (JSON)</Label>
          <Textarea
            id="config"
            v-model="form.configJson"
            placeholder='{"host": "localhost", "port": 5432, "database": "mydb"}'
            :disabled="isLoading"
            rows="4"
          />
          <p class="text-xs text-gray-500">
            Enter the configuration as JSON. This will vary based on your data source type.
          </p>
        </div>
        
        <DialogFooter>
          <Button type="button" variant="outline" @click="open = false" :disabled="isLoading">
            Cancel
          </Button>
          <Button type="submit" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="w-4 h-4 mr-2 animate-spin" />
            Create Data Source
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { toast } from 'vue-sonner'
import { useDataSources } from '~/composables/useDataSources'
import { useEnvironments } from '~/composables/useEnvironments'
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

const { createDataSource } = useDataSources()
const { selectedEnvironmentId } = useEnvironments()

const open = ref(false)
const isLoading = ref(false)

const form = reactive({
  name: '',
  alias: '',
  description: '',
  source_catalog: '' as 'DATABASE' | 'API' | 'FILE',
  source_type: '' as 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift' | 'mongodb' | 'dynamodb' | 'couchbase',
  configJson: '{}'
})

async function handleSubmit() {
  if (!form.name.trim()) {
    toast.error('Data source name is required')
    return
  }

  if (!form.alias.trim()) {
    toast.error('Alias is required')
    return
  }

  if (!form.source_catalog) {
    toast.error('Source catalog is required')
    return
  }

  if (!form.source_type) {
    toast.error('Source type is required')
    return
  }

  if (!selectedEnvironmentId.value) {
    toast.error('Please select an environment first')
    return
  }

  let config: Record<string, any>
  try {
    config = JSON.parse(form.configJson)
  } catch (error) {
    toast.error('Invalid JSON configuration')
    return
  }

  isLoading.value = true
  
  try {
    await createDataSource({
      environment_id: selectedEnvironmentId.value,
      name: form.name.trim(),
      alias: form.alias.trim(),
      description: form.description.trim(),
      source_catalog: form.source_catalog,
      source_type: form.source_type,
      config
    })
    
    toast.success('Data source created successfully')
    open.value = false
    
    // Reset form
    form.name = ''
    form.alias = ''
    form.description = ''
    form.source_catalog = '' as 'DATABASE' | 'API' | 'FILE'
    form.source_type = '' as 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'snowflake' | 'redshift' | 'mongodb' | 'dynamodb' | 'couchbase'
    form.configJson = '{}'
  } catch (error) {
    console.error('Failed to create data source:', error)
    toast.error('Failed to create data source')
  } finally {
    isLoading.value = false
  }
}
</script> 