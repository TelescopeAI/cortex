<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <Label for="project_id">Project ID</Label>
      <Input
        id="project_id"
        v-model="localConfig.project_id"
        placeholder="my-gcp-project"
        :disabled="disabled"
        required
        @update:model-value="updateConfig"
      />
    </div>
    
    <div class="space-y-2">
      <Label for="dataset_id">Dataset ID (Optional)</Label>
      <Input
        id="dataset_id"
        v-model="localConfig.dataset_id"
        placeholder="mydataset"
        :disabled="disabled"
        @update:model-value="updateConfig"
      />
    </div>
    
    <div v-if="!disabled" class="space-y-2">
      <Label for="service_account">Service Account JSON</Label>
      <Textarea
        id="service_account"
        v-model="localConfig.serviceAccountJson"
        placeholder='{"type": "service_account", "project_id": "...", "private_key_id": "...", ...}'
        :disabled="disabled"
        rows="6"
        required
        @update:model-value="updateServiceAccount"
      />
      <p class="text-xs text-muted-foreground">
        Paste your service account JSON key here. This should include the private key and other credentials.
      </p>
    </div>
    <div v-else class="space-y-2">
      <Label>Service Account</Label>
      <div class="p-3 bg-gray-50 rounded border text-sm">
        <p class="text-gray-600">
          <strong>Project ID:</strong> {{ localConfig.project_id }}
        </p>
        <p class="text-gray-600">
          <strong>Service Account:</strong> Configured ✓
        </p>
        <p class="text-xs text-gray-500 mt-1">
          Service account JSON is configured and secured.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'

interface BigQueryConfig {
  project_id: string
  dataset_id?: string
  service_account_details: Record<string, any>
  serviceAccountJson?: string  // Helper field for UI
}

interface Props {
  modelValue: any
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  modelValue: () => ({
    project_id: '',
    dataset_id: '',
    service_account_details: {},
    serviceAccountJson: ''
  })
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const localConfig = reactive<BigQueryConfig>({ ...props.modelValue })

watch(() => props.modelValue, (newValue) => {
  Object.assign(localConfig, newValue)
}, { deep: true })

const updateConfig = () => {
  const { serviceAccountJson, ...config } = localConfig
  emit('update:modelValue', config)
}

const updateServiceAccount = () => {
  try {
    if (localConfig.serviceAccountJson) {
      localConfig.service_account_details = JSON.parse(localConfig.serviceAccountJson)
    } else {
      localConfig.service_account_details = {}
    }
    updateConfig()
  } catch (error) {
    // Invalid JSON - keep the string for user to fix
    updateConfig()
  }
}
</script>
