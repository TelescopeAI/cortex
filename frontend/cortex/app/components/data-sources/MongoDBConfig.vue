<template>
  <div class="space-y-4">
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <Label>Host</Label>
        <Input
          v-if="!disabled"
          id="host"
          v-model="localConfig.host"
          placeholder="localhost"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
        <div v-else class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.host || 'Not configured' }}</div>
      </div>

      <div class="space-y-2">
        <Label>Port</Label>
        <Input
          v-if="!disabled"
          id="port"
          v-model.number="localConfig.port"
          type="number"
          placeholder="27017"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
        <div v-else class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.port || 'Not configured' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'

interface MongoDBConfig {
  host: string
  port: number
}

interface Props {
  modelValue: any
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  modelValue: () => ({
    host: '',
    port: 27017
  })
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const localConfig = reactive<MongoDBConfig>({ ...props.modelValue })

watch(() => props.modelValue, (newValue) => {
  Object.assign(localConfig, newValue)
}, { deep: true })

const updateConfig = () => {
  emit('update:modelValue', { ...localConfig })
}
</script>
