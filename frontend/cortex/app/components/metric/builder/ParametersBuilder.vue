<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Parameters</h4>
      <Button variant="outline" size="sm" @click="addParameter">
        <Plus class="h-4 w-4 mr-2" />
        Add Parameter
      </Button>
    </div>

    <div v-if="Object.keys(parameters).length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Settings class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No parameters defined</p>
      <p class="text-xs text-muted-foreground">Parameters allow dynamic query generation</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(parameter, key) in parameters"
        :key="key"
        class="p-4"
      >
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Settings class="h-4 w-4 text-indigo-500" />
              <span class="font-medium">{{ parameter.name || 'Unnamed Parameter' }}</span>
            </div>
            <Button variant="ghost" size="sm" @click="removeParameter(key)">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Name *</Label>
              <Input v-model="parameter.name" placeholder="parameter_name" @update:model-value="updateParameters" />
            </div>
            <div class="space-y-2">
              <Label>Type</Label>
              <Select v-model="parameter.type" @update:model-value="updateParameters">
                <SelectTrigger>
                  <SelectValue placeholder="Select parameter type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="string">String</SelectItem>
                  <SelectItem value="integer">Integer</SelectItem>
                  <SelectItem value="float">Float</SelectItem>
                  <SelectItem value="boolean">Boolean</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="datetime">DateTime</SelectItem>
                  <SelectItem value="list">List</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Default Value</Label>
              <Input v-model="parameter.default_value" placeholder="Optional default value" @update:model-value="updateParameters" />
            </div>
            <div class="flex items-center space-x-2 pt-7">
              <input
                type="checkbox"
                v-model="parameter.required"
                @change="updateParameters"
                class="h-4 w-4 rounded border-gray-300"
              />
              <Label class="text-sm font-normal">Required</Label>
            </div>
          </div>

          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea v-model="parameter.description" placeholder="Describe this parameter..." rows="2" @update:model-value="updateParameters" />
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Plus, Settings, X } from 'lucide-vue-next'

interface Parameter {
  name: string
  type: string
  description?: string
  default_value?: any
  required: boolean
}

interface Props {
  parameters?: Record<string, Parameter>
}

const props = withDefaults(defineProps<Props>(), {
  parameters: () => ({})
})

const emit = defineEmits<{
  'update:parameters': [value: Record<string, Parameter>]
}>()

const parameters = ref<Record<string, Parameter>>({ ...props.parameters })

watch(() => props.parameters, (newParameters) => {
  parameters.value = { ...newParameters }
})

const updateParameters = () => {
  emit('update:parameters', parameters.value)
}

const addParameter = () => {
  const paramKey = `param_${Date.now()}`
  const newParameter: Parameter = {
    name: 'new_parameter',
    type: 'string',
    required: false
  }
  
  parameters.value[paramKey] = newParameter
  updateParameters()
}

const removeParameter = (key: string) => {
  delete parameters.value[key]
  updateParameters()
}
</script> 