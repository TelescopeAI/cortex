<template>
  <div class="min-h-screen bg-background">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p class="text-muted-foreground">Loading model...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <Alert class="max-w-md" variant="destructive">
        <AlertCircle class="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{{ error }}</AlertDescription>
      </Alert>
    </div>

    <!-- Main Content -->
    <div v-else-if="model" class="flex h-screen">
      <!-- Sidebar -->
      <div class="w-64 border-r bg-muted/10">
        <div class="p-4 border-b">
          <div class="flex items-center space-x-2">
            <Button variant="ghost" size="sm" @click="$router.back()">
              <ArrowLeft class="h-4 w-4" />
            </Button>
            <div>
              <h1 class="font-semibold">{{ model.name }}</h1>
              <p class="text-sm text-muted-foreground">{{ model.alias || 'No alias' }}</p>
            </div>
          </div>
        </div>

        <nav class="p-2">
          <div class="space-y-1">
            <Button
              variant="ghost"
              class="w-full justify-start"
              :class="{ 'bg-muted': activeTab === 'overview' }"
              @click="activeTab = 'overview'"
            >
              <BarChart class="h-4 w-4 mr-2" />
              Overview
            </Button>
            <Button
              variant="ghost"
              class="w-full justify-start"
              :class="{ 'bg-muted': activeTab === 'metrics' }"
              @click="activeTab = 'metrics'"
            >
              <Target class="h-4 w-4 mr-2" />
              Metrics
            </Button>
            <Button
              variant="ghost"
              class="w-full justify-start"
              :class="{ 'bg-muted': activeTab === 'schema' }"
              @click="activeTab = 'schema'"
            >
              <Code class="h-4 w-4 mr-2" />
              Schema
            </Button>
            <Button
              variant="ghost"
              class="w-full justify-start"
              :class="{ 'bg-muted': activeTab === 'settings' }"
              @click="activeTab = 'settings'"
            >
              <Settings class="h-4 w-4 mr-2" />
              Settings
            </Button>
          </div>
        </nav>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col">
        <!-- Header -->
        <div class="border-b p-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-2xl font-bold">{{ getTabTitle(activeTab) }}</h2>
              <p class="text-muted-foreground">{{ getTabDescription(activeTab) }}</p>
            </div>
            <div class="flex items-center space-x-2">
              <Badge v-if="model.is_active" variant="default">Active</Badge>
              <Badge v-else variant="secondary">Inactive</Badge>
              <Badge v-if="model.is_valid" variant="default">Valid</Badge>
              <Badge v-else variant="destructive">Invalid</Badge>
              <Button v-if="hasUnsavedChanges" @click="saveChanges" size="sm">
                <Save class="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>
        </div>

        <!-- Tab Content -->
        <div class="flex-1 overflow-auto">
          <!-- Overview Tab -->
          <div v-show="activeTab === 'overview'" class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader class="pb-2">
                  <CardTitle class="text-sm font-medium">Version</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="text-2xl font-bold">v{{ model.version }}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader class="pb-2">
                  <CardTitle class="text-sm font-medium">Last Updated</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="text-2xl font-bold">{{ formatDate(model.updated_at) }}</div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Model Information</CardTitle>
              </CardHeader>
              <CardContent class="space-y-4">
                <div>
                  <Label>Description</Label>
                  <p class="text-sm text-muted-foreground mt-1">
                    {{ model.description || 'No description provided' }}
                  </p>
                </div>
                <div>
                  <Label>Created</Label>
                  <p class="text-sm text-muted-foreground mt-1">
                    {{ formatDate(model.created_at) }}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- Metrics Tab -->
          <div v-show="activeTab === 'metrics'" class="p-6">
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold">Available Metrics</h3>
                <Button size="sm">
                  <Plus class="h-4 w-4 mr-2" />
                  Add Metric
                </Button>
              </div>
              
              <div v-if="metrics.length === 0" class="text-center py-8">
                <Target class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-semibold mb-2">No metrics defined</h3>
                <p class="text-muted-foreground mb-4">
                  Add metrics to your semantic model to start analyzing data.
                </p>
                <Button>
                  <Plus class="h-4 w-4 mr-2" />
                  Create your first metric
                </Button>
              </div>

              <div v-else class="grid gap-4">
                <Card v-for="metric in metrics" :key="metric.id">
                  <CardHeader>
                    <div class="flex items-center justify-between">
                      <div>
                        <CardTitle class="text-base">{{ metric.name }}</CardTitle>
                        <p class="text-sm text-muted-foreground">{{ metric.description }}</p>
                      </div>
                      <div class="flex items-center space-x-2">
                        <Badge v-if="metric.public" variant="default">Public</Badge>
                        <Badge v-else variant="secondary">Private</Badge>
                        <Button variant="ghost" size="sm" @click="editMetric(metric)">
                          <Edit class="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div class="text-sm text-muted-foreground">
                      <p v-if="metric.alias"><strong>Alias:</strong> {{ metric.alias }}</p>
                      <p v-if="metric.table"><strong>Table:</strong> {{ metric.table }}</p>
                      <p v-if="metric.measures"><strong>Measures:</strong> {{ metric.measures.length }}</p>
                      <p v-if="metric.dimensions"><strong>Dimensions:</strong> {{ metric.dimensions.length }}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>

          <!-- Schema Tab -->
          <div v-show="activeTab === 'schema'" class="p-6 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold">Semantic Model Schema</h3>
              <div class="flex items-center space-x-2">
                <Button variant="outline" size="sm" @click="formatSchema">
                  <Code class="h-4 w-4 mr-2" />
                  Format
                </Button>
                <Button variant="outline" size="sm" @click="validateSchema">
                  <CheckCircle class="h-4 w-4 mr-2" />
                  Validate
                </Button>
              </div>
            </div>

            <div class="space-y-4">
              <div>
                <Label>JSON Schema Definition</Label>
                <Textarea
                  v-model="schemaJson"
                  class="mt-2 font-mono text-sm"
                  rows="20"
                  placeholder="Enter your semantic model JSON schema..."
                />
              </div>

              <div v-if="validationErrors.length > 0" class="space-y-2">
                <Label class="text-destructive">Validation Errors</Label>
                <Alert variant="destructive">
                  <AlertTriangle class="h-4 w-4" />
                  <AlertTitle>Schema Validation Failed</AlertTitle>
                  <AlertDescription>
                    <ul class="list-disc list-inside space-y-1">
                      <li v-for="error in validationErrors" :key="error">{{ error }}</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              </div>
            </div>
          </div>

          <!-- Settings Tab -->
          <div v-show="activeTab === 'settings'" class="p-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Model Settings</CardTitle>
                <CardDescription>Configure your data model settings</CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <Label>Active Status</Label>
                    <p class="text-sm text-muted-foreground">
                      Controls whether this model can be used for queries
                    </p>
                  </div>
                  <Switch v-model:checked="editableModel.is_active" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Advanced Configuration</CardTitle>
                <CardDescription>Additional model configuration as JSON</CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  v-model="configJson"
                  class="font-mono text-sm"
                  rows="10"
                  placeholder="Enter additional configuration as JSON..."
                />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, BarChart, Target, Code, Settings, Save, Plus, 
  Edit, CheckCircle, AlertCircle, AlertTriangle
} from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Switch } from '~/components/ui/switch'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { useDataModels } from '~/composables/useDataModels'

// Route and Router
const route = useRoute()
const router = useRouter()
const modelId = computed(() => route.params.id as string)

// Composables
const {
  getModel, loading: isLoading, error, 
  updateModel: updateDataModel, validateModel: validateModelAction
} = useDataModels()

// State
const model = ref<any>(null)
const activeTab = ref('overview')
const editableModel = ref<any>({})
const schemaJson = ref('')
const configJson = ref('')
const hasUnsavedChanges = ref(false)
const validationErrors = ref<string[]>([])
const metrics = ref<any[]>([])

// Computed

const getTabTitle = (tab: string) => {
  switch (tab) {
    case 'overview': return 'Overview'
    case 'metrics': return 'Metrics'
    case 'schema': return 'Schema'
    case 'settings': return 'Settings'
    default: return ''
  }
}

const getTabDescription = (tab: string) => {
  switch (tab) {
    case 'overview': return 'Model information and statistics'
    case 'metrics': return 'Manage semantic metrics and measurements'
    case 'schema': return 'Edit the raw semantic model JSON schema'
    case 'settings': return 'Configure model settings and advanced options'
    default: return ''
  }
}

// Methods
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const loadModelData = async () => {
  try {
    model.value = await getModel(modelId.value)
    if (model.value) {
      editableModel.value = { ...model.value }
      schemaJson.value = JSON.stringify(model.value.semantic_model || {}, null, 2)
      configJson.value = JSON.stringify(model.value.config || {}, null, 2)
      
      // Extract metrics from semantic model
      const semanticModel = model.value.semantic_model || {}
      metrics.value = semanticModel.metrics || []
    }
  } catch (err) {
    console.error('Failed to load model:', err)
  }
}

const formatSchema = () => {
  try {
    const parsed = JSON.parse(schemaJson.value)
    schemaJson.value = JSON.stringify(parsed, null, 2)
  } catch (error) {
    console.error('Invalid JSON:', error)
  }
}

const validateSchema = async () => {
  validationErrors.value = []
  
  try {
    // Basic JSON validation
    JSON.parse(schemaJson.value)
    
    // Call API validation if needed
    if (model.value) {
      const result = await validateModelAction(model.value.id) as any
      if (!result.is_valid) {
        validationErrors.value = result.errors || []
      }
    }
  } catch (error) {
    validationErrors.value = ['Invalid JSON format']
  }
}

const saveChanges = async () => {
  if (!model.value) return

  try {
    // Parse JSON fields
    let semanticModel = {}
    let config = {}
    
    try {
      semanticModel = JSON.parse(schemaJson.value)
    } catch (error) {
      throw new Error('Invalid semantic model JSON')
    }
    
    try {
      config = JSON.parse(configJson.value)
    } catch (error) {
      throw new Error('Invalid config JSON')
    }

    // Update model
    await updateDataModel(model.value.id, {
      name: editableModel.value.name,
      alias: editableModel.value.alias,
      description: editableModel.value.description,
      is_active: editableModel.value.is_active,
      config: config
    } as any)

    hasUnsavedChanges.value = false
  } catch (error) {
    console.error('Failed to save changes:', error)
  }
}

const editMetric = (metric: any) => {
  // TODO: Implement edit metric
  console.log('Edit metric:', metric)
}

// Watch for changes
watch([editableModel, schemaJson, configJson], () => {
  hasUnsavedChanges.value = true
}, { deep: true })

// Lifecycle
onMounted(async () => {
  await loadModelData()
})

// Watch model changes
watch(model, () => {
  if (model.value) {
    loadModelData()
  }
}, { immediate: true })
</script> 
 