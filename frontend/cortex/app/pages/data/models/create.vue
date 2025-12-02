<template>
  <div class="flex-1 space-y-6 p-4 pt-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Create Data Model</h1>
        <p class="text-muted-foreground">
          Define a new semantic data model for analytics
        </p>
      </div>
      <Button variant="outline" @click="router.back()">
        Cancel
      </Button>
    </div>

    <!-- Form -->
    <Card class="max-w-4xl">
      <CardHeader>
        <CardTitle>Basic Information</CardTitle>
        <CardDescription>
          Provide basic details about your data model
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- Basic Fields -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="name">Name *</Label>
              <Input
                id="name"
                v-model="form.name"
                placeholder="e.g., Sales Analytics"
                required
                :class="{ 'border-destructive': errors.name }"
              />
              <p v-if="errors.name" class="text-sm text-destructive">
                {{ errors.name }}
              </p>
            </div>

            <div class="space-y-2">
              <Label for="alias">Alias</Label>
              <Input
                id="alias"
                v-model="form.alias"
                placeholder="e.g., sales_analytics"
                :class="{ 'border-destructive': errors.alias }"
              />
              <p v-if="errors.alias" class="text-sm text-destructive">
                {{ errors.alias }}
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <Label for="description">Description</Label>
            <Textarea
              id="description"
              v-model="form.description"
              placeholder="Describe what this data model is used for..."
              rows="3"
            />
          </div>


          <!-- Semantic Model Configuration -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-medium">Semantic Model</h3>
                <p class="text-sm text-muted-foreground">
                  Define the semantic structure of your data model
                </p>
              </div>
              <div class="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  @click="loadTemplate"
                >
                  Load Template
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  @click="validateSemanticModel"
                  :disabled="!form.semantic_model.trim()"
                >
                  Validate
                </Button>
              </div>
            </div>

            <!-- JSON Editor -->
            <div class="space-y-2">
              <Textarea
                v-model="form.semantic_model"
                placeholder="Enter semantic model JSON..."
                rows="20"
                class="font-mono text-sm"
                :class="{ 'border-destructive': errors.semantic_model || validationErrors.length > 0 }"
              />
              <p v-if="errors.semantic_model" class="text-sm text-destructive">
                {{ errors.semantic_model }}
              </p>
            </div>

            <!-- Validation Results -->
            <div v-if="validationErrors.length > 0" class="space-y-2">
              <Alert variant="destructive">
                <AlertCircle class="h-4 w-4" />
                <AlertTitle>Validation Errors</AlertTitle>
                <AlertDescription>
                  <ul class="list-disc list-inside space-y-1 mt-2">
                    <li v-for="error in validationErrors" :key="error">
                      {{ error }}
                    </li>
                  </ul>
                </AlertDescription>
              </Alert>
            </div>

            <div v-if="validationWarnings.length > 0" class="space-y-2">
              <Alert>
                <AlertCircle class="h-4 w-4" />
                <AlertTitle>Validation Warnings</AlertTitle>
                <AlertDescription>
                  <ul class="list-disc list-inside space-y-1 mt-2">
                    <li v-for="warning in validationWarnings" :key="warning">
                      {{ warning }}
                    </li>
                  </ul>
                </AlertDescription>
              </Alert>
            </div>

            <div v-if="isValidJson && validationErrors.length === 0" class="space-y-2">
              <Alert>
                <CheckCircle class="h-4 w-4" />
                <AlertTitle>Valid JSON</AlertTitle>
                <AlertDescription>
                  The semantic model JSON is valid and ready to use.
                </AlertDescription>
              </Alert>
            </div>
          </div>

          <!-- Advanced Configuration (Expandable) -->
          <Accordion type="single" collapsible>
            <AccordionItem value="advanced">
              <AccordionTrigger>Advanced Configuration</AccordionTrigger>
              <AccordionContent class="space-y-4">
                <div class="space-y-2">
                  <Label for="config">Additional Configuration (JSON)</Label>
                  <Textarea
                    id="config"
                    v-model="form.config"
                    placeholder='{"key": "value"}'
                    rows="4"
                    class="font-mono text-sm"
                  />
                  <p class="text-sm text-muted-foreground">
                    Optional JSON configuration for advanced settings
                  </p>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-6 border-t">
            <Button
              type="button"
              variant="outline"
              @click="router.back()"
              :disabled="isSubmitting"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              :disabled="isSubmitting || !isFormValid"
              class="gap-2"
            >
              <Loader2 v-if="isSubmitting" class="h-4 w-4 animate-spin" />
              Create Data Model
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDataModels } from '~/composables/useDataModels'
import { useDataSources } from '~/composables/useDataSources'
import { useEnvironments } from '~/composables/useEnvironments'
import { Database, AlertCircle, CheckCircle, Loader2 } from 'lucide-vue-next'

import { Button } from '~/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '~/components/ui/select'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { 
  Accordion, AccordionContent, AccordionItem, AccordionTrigger 
} from '~/components/ui/accordion'

// Composables
const router = useRouter()
const { createModel } = useDataModels()
const { dataSources } = useDataSources()
const { selectedEnvironmentId } = useEnvironments()

// Form state
const form = ref({
  name: '',
  alias: '',
  description: '',
  semantic_model: '',
  config: ''
})

// Validation state
const errors = ref<Record<string, string>>({})
const validationErrors = ref<string[]>([])
const validationWarnings = ref<string[]>([])
const isSubmitting = ref(false)

// Computed
const isValidJson = computed(() => {
  if (!form.value.semantic_model.trim()) return false
  
  try {
    JSON.parse(form.value.semantic_model)
    return true
  } catch {
    return false
  }
})

const isFormValid = computed(() => {
  return form.value.name.trim() && 
         isValidJson.value && 
         validationErrors.value.length === 0 &&
         Object.keys(errors.value).length === 0
})

// Template for semantic model
const getSemanticModelTemplate = () => {
  return JSON.stringify({
    "version": "1.0",
    "description": "Sample semantic model",
    "metrics": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "sample_metric",
        "alias": "sample",
        "description": "A sample metric for demonstration",
        "table": "your_table_name",
        "measures": [
          {
            "name": "count",
            "description": "Count of all records",
            "type": "count",
            "query": "*",
            "alias": "total_count"
          }
        ],
        "dimensions": [
          {
            "name": "category",
            "description": "Category dimension for grouping",
            "query": "category",
            "alias": "category"
          }
        ],
        "public": true,
        "model_version": 1
      }
    ]
  }, null, 2)
}

// Methods
const validateForm = () => {
  const newErrors: Record<string, string> = {}

  if (!form.value.name.trim()) {
    newErrors.name = 'Name is required'
  }

  if (!form.value.semantic_model.trim()) {
    newErrors.semantic_model = 'Semantic model is required'
  } else if (!isValidJson.value) {
    newErrors.semantic_model = 'Invalid JSON format'
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

const validateSemanticModel = () => {
  validationErrors.value = []
  validationWarnings.value = []

  if (!form.value.semantic_model.trim()) {
    validationErrors.value.push('Semantic model cannot be empty')
    return
  }

  try {
    const model = JSON.parse(form.value.semantic_model)
    
    // Basic validation
    if (!model.metrics || !Array.isArray(model.metrics)) {
      validationErrors.value.push('Semantic model must contain a "metrics" array')
    }

    if (model.metrics && model.metrics.length === 0) {
      validationWarnings.value.push('No metrics defined in the semantic model')
    }

    // Validate each metric
    if (model.metrics && Array.isArray(model.metrics)) {
      model.metrics.forEach((metric: any, index: number) => {
        if (!metric.name) {
          validationErrors.value.push(`Metric ${index + 1}: name is required`)
        }
        
        if (!metric.table && !metric.query) {
          validationErrors.value.push(`Metric ${index + 1}: either table or query must be specified`)
        }

        if (!metric.measures && !metric.dimensions && !metric.aggregations) {
          validationWarnings.value.push(`Metric ${index + 1}: no measures, dimensions, or aggregations defined - will use SELECT *`)
        }
      })
    }

  } catch (err) {
    validationErrors.value.push('Invalid JSON format')
  }
}

const loadTemplate = () => {
  form.value.semantic_model = getSemanticModelTemplate()
  validateSemanticModel()
}

const handleSubmit = async () => {
  if (!validateForm()) return

  try {
    isSubmitting.value = true

    // Parse JSON fields
    let semanticModel: any
    let config: any = {}

    try {
      semanticModel = JSON.parse(form.value.semantic_model)
    } catch {
      errors.value.semantic_model = 'Invalid JSON format'
      return
    }

    if (form.value.config.trim()) {
      try {
        config = JSON.parse(form.value.config)
      } catch {
        errors.value.config = 'Invalid JSON format'
        return
      }
    }

    // Create the data model
    const newModel = await createModel({
      environment_id: selectedEnvironmentId.value,
      name: form.value.name,
      alias: form.value.alias || undefined,
      description: form.value.description || undefined,
      config
    })

    // Navigate to the new model
    if (newModel) {
      router.push(`/data/models/${newModel.id}`)
    }

  } catch (err: any) {
    console.error('Failed to create data model:', err)
    // Handle specific error cases
    if (err.message.includes('validation')) {
      validationErrors.value = [err.message]
    } else {
      errors.value.submit = err.message || 'Failed to create data model'
    }
  } finally {
    isSubmitting.value = false
  }
}

// Watch for changes in semantic model to auto-validate
let debounceTimer: NodeJS.Timeout | null = null
watch(
  () => form.value.semantic_model,
  () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      if (form.value.semantic_model.trim()) {
        validateSemanticModel()
      } else {
        validationErrors.value = []
        validationWarnings.value = []
      }
    }, 500)
  }
)

// Lifecycle
onMounted(async () => {
  // Auto-load template if no semantic model
  if (!form.value.semantic_model.trim()) {
    loadTemplate()
  }
})
</script> 