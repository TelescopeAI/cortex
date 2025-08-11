<script setup lang="ts">
import { ref, computed } from 'vue'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { Select as UiSelect, SelectContent as UiSelectContent, SelectItem as UiSelectItem, SelectTrigger as UiSelectTrigger, SelectValue as UiSelectValue } from '~/components/ui/select'
import ColumnSelector from '~/components/ColumnSelector.vue'
import { Button } from '~/components/ui/button'
import { Trash2 } from 'lucide-vue-next'

interface FieldMapping {
  field: string
  data_type: string
  label?: string
  required?: boolean
}

interface Props {
  label: string
  mapping?: FieldMapping
  availableTables: Array<{ name: string; columns: Array<{ name: string; type: string }> }>
  required?: boolean
  dataTypes?: string[]
}

interface Emits {
  (e: 'update', mapping: FieldMapping): void
  (e: 'remove'): void
}

const props = withDefaults(defineProps<Props>(), {
  required: false,
  dataTypes: () => ['numerical', 'categorical', 'temporal']
})

const emit = defineEmits<Emits>()

const currentMapping = ref<FieldMapping>(props.mapping || {
  field: '',
  data_type: 'numerical',
  label: '',
  required: props.required
})

const selectedFieldDisplay = computed(() => {
  if (!currentMapping.value.field) return 'Select Field'
  const field = currentMapping.value.field
  const label = currentMapping.value.label || field
  return `${label} (${field})`
})

function onFieldSelect(tableName: string, column: { name: string; type: string }) {
  currentMapping.value.field = column.name
  currentMapping.value.label = column.name
  // Auto-detect data type based on column type
  const lowerType = (column.type || '').toLowerCase()
  if (lowerType === 'measure') {
    currentMapping.value.data_type = 'numerical'
  } else if (lowerType === 'dimension') {
    currentMapping.value.data_type = 'categorical'
  } else if (lowerType.includes('int') || lowerType.includes('float') || lowerType.includes('decimal') || lowerType.includes('num')) {
    currentMapping.value.data_type = 'numerical'
  } else if (lowerType.includes('date') || lowerType.includes('time')) {
    currentMapping.value.data_type = 'temporal'
  } else {
    currentMapping.value.data_type = 'categorical'
  }
  
  emit('update', currentMapping.value)
}

function updateLabel(newLabel: string) {
  currentMapping.value.label = newLabel
  emit('update', currentMapping.value)
}

function updateDataType(newType: string) {
  currentMapping.value.data_type = newType
  emit('update', currentMapping.value)
}

function removeField() {
  emit('remove')
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center gap-2">
      <Label class="text-sm font-medium">{{ label }}</Label>
      <span v-if="required" class="text-red-500 text-xs">*</span>
    </div>
    
    <div class="space-y-2">
      <!-- Field Selection -->
      <div>
        <Label class="text-xs text-muted-foreground">Field</Label>
        <ColumnSelector
          :available-tables="availableTables"
          :button-text="selectedFieldDisplay"
          @select="onFieldSelect"
        />
      </div>
      
      <!-- Data type selection removed; inferred automatically -->
      
      <!-- Custom Label and Remove -->
      <div v-if="currentMapping.field">
        <div class="flex items-center gap-2">
          <div class="flex-1">
            <Label class="text-xs text-muted-foreground">Display Label (optional)</Label>
            <Input 
              :model-value="currentMapping.label" 
              @update:model-value="(v:any) => updateLabel(String(v ?? ''))"
              :placeholder="currentMapping.field"
            />
          </div>
          <Button variant="ghost" size="icon" class="text-destructive" @click="removeField">
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
