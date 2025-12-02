<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h5 class="text-sm font-medium">Output Formatting</h5>
        <p class="text-xs text-muted-foreground">
          Define how this {{ objectType }} should be formatted
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        @click="addFormat"
      >
        <Plus class="h-4 w-4 mr-2" />
        Add Format
      </Button>
    </div>

    <!-- Formats List -->
    <div v-if="!formats || formats.length === 0" class="text-center py-4 border-2 border-dashed rounded-lg">
      <Settings class="h-6 w-6 mx-auto text-muted-foreground mb-2" />
      <p class="text-xs text-muted-foreground">No formatting defined</p>
      <p class="text-xs text-muted-foreground">Add formatting to customize output</p>
    </div>

    <div v-else-if="formats && formats.length > 0" class="space-y-3">
        <Card 
          v-for="(format, index) in (formats || [])"
          :key="index"
          class="p-4"
        >
        <div class="space-y-4">
          <!-- Format Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Settings class="h-4 w-4 text-blue-500" />
              <span class="font-medium">{{ format.name || 'Unnamed Format' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeFormat(index)"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Format Configuration -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Name -->
            <div class="space-y-2">
              <Label>Format Name *</Label>
              <Input
                v-model="format.name"
                placeholder="format_name"
                @update:model-value="updateFormats"
              />
            </div>

            <!-- Type -->
            <div class="space-y-2">
              <Label>Format Type *</Label>
              <Select v-model="format.type" @update:model-value="updateFormats">
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="OutputFormatType.RAW">Raw (No transformation)</SelectItem>
                  <SelectItem :value="OutputFormatType.CAST">Cast (Type conversion)</SelectItem>
                  <SelectItem :value="OutputFormatType.FORMAT">Format (String formatting)</SelectItem>
                  <SelectItem :value="OutputFormatType.CALCULATE">Calculate (Math operations)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Mode -->
            <div class="space-y-2">
              <Label>Processing Mode</Label>
              <Select v-model="format.mode" @update:model-value="updateFormats">
                <SelectTrigger>
                  <SelectValue placeholder="Select mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem :value="OutputFormatMode.IN_QUERY">In Query (SQL level)</SelectItem>
                  <SelectItem :value="OutputFormatMode.POST_QUERY">Post Query (Result level)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Description -->
            <div class="space-y-2">
              <Label>Description</Label>
              <Input
                v-model="format.description"
                placeholder="Describe this format..."
                @update:model-value="updateFormats"
              />
            </div>
          </div>

          <!-- Type-specific Configuration -->
          <div v-if="format.type === OutputFormatType.CAST" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Target Type</Label>
                <Select v-model="format.target_type" @update:model-value="updateFormats">
                  <SelectTrigger>
                    <SelectValue placeholder="Select target type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="string">String</SelectItem>
                    <SelectItem value="integer">Integer</SelectItem>
                    <SelectItem value="float">Float</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="timestamp">Timestamp</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <div v-if="format.type === OutputFormatType.FORMAT" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Format Type</Label>
                <Select v-model="format.format_type" @update:model-value="updateFormats">
                  <SelectTrigger>
                    <SelectValue placeholder="Select format type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="datetime">Date/Time</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="currency">Currency</SelectItem>
                    <SelectItem value="percentage">Percentage</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label>Format String</Label>
                <Input
                  v-model="format.format_string"
                  placeholder="e.g., DD-MM-YYYY, %.2f, $999.99, or any custom format"
                  @update:model-value="updateFormats"
                />
              </div>
            </div>
          </div>

          <div v-if="format.type === OutputFormatType.CALCULATE" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label>Operation</Label>
                <Select v-model="format.operation" @update:model-value="updateFormats">
                  <SelectTrigger>
                    <SelectValue placeholder="Select operation" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="add">Add (+)</SelectItem>
                    <SelectItem value="subtract">Subtract (-)</SelectItem>
                    <SelectItem value="multiply">Multiply (×)</SelectItem>
                    <SelectItem value="divide">Divide (÷)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label>Operands (comma-separated)</Label>
                <Input
                  v-model="operandsString"
                  placeholder="e.g., col1, col2, col3"
                  @update:model-value="updateOperands"
                />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Settings, X, Plus } from 'lucide-vue-next'
import type { OutputFormat } from '~/types/output-formats'
import { OutputFormatType, OutputFormatMode } from '~/types/output-formats'

interface Props {
  modelValue?: OutputFormat[]
  objectType: 'measure' | 'dimension' | 'filter'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: OutputFormat[]]
}>()

const formats = ref<OutputFormat[]>([...(props.modelValue || [])])

// Watch for changes from parent
watch(() => props.modelValue, (newFormats) => {
  formats.value = [...(newFormats || [])]
})

// Computed properties for comma-separated strings
const operandsString = computed({
  get: () => formats.value?.find(f => f.type === OutputFormatType.CALCULATE)?.operands?.join(', ') || '',
  set: (value: string) => {
    const calcFormat = formats.value?.find(f => f.type === OutputFormatType.CALCULATE)
    if (calcFormat) {
      calcFormat.operands = value.split(',').map(s => s.trim()).filter(Boolean)
      updateFormats()
    }
  }
})

const updateFormats = () => {
  emit('update:modelValue', formats.value || [])
}

const updateOperands = () => {
  // Handled by computed setter
}

const addFormat = () => {
  const newFormat: OutputFormat = {
    name: `format_${(formats.value?.length || 0) + 1}`,
    type: OutputFormatType.RAW,
    mode: OutputFormatMode.IN_QUERY,
    description: ''
  }
  if (!formats.value) {
    formats.value = []
  }
  formats.value.push(newFormat)
  updateFormats()
}

const removeFormat = (index: number) => {
  if (formats.value) {
    formats.value.splice(index, 1)
    updateFormats()
  }
}
</script>
