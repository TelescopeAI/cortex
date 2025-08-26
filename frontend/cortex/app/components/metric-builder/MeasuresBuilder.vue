<template>
  <div class="space-y-4">
    <!-- Add Measure Button -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Measures</h4>
      <div class="flex items-center space-x-2">
        <ColumnSelector
          :available-tables="availableTables"
          button-text="Add Measure"
          @select="addMeasure"
        />
        <Button variant="outline" size="sm" @click="addCustomMeasure">
          <Code class="h-4 w-4 mr-2" />
          Custom Measure
        </Button>
      </div>
    </div>

    <!-- Measures List -->
    <div v-if="measures.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Target class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No measures defined</p>
      <p class="text-xs text-muted-foreground">Add a measure to get started</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(measure, index) in measures"
        :key="index"
        class="p-4"
      >
        <div class="space-y-4">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Target class="h-4 w-4 text-blue-500" />
              <span class="font-medium">{{ measure.name || 'Unnamed Measure' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeMeasure(index)"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Form Fields -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Name -->
            <div class="space-y-2">
              <Label>Name *</Label>
              <Input
                v-model="measure.name"
                placeholder="measure_name"
                @update:model-value="(value) => handleNameChange(measure, value)"
              />
            </div>

            <!-- Type -->
            <div class="space-y-2">
              <Label>Type *</Label>
              <Select v-model="measure.type" @update:model-value="updateMeasures">
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="count">Count</SelectItem>
                  <SelectItem value="sum">Sum</SelectItem>
                  <SelectItem value="avg">Average</SelectItem>
                  <SelectItem value="min">Minimum</SelectItem>
                  <SelectItem value="max">Maximum</SelectItem>
                  <SelectItem value="distinct_count">Distinct Count</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Alias -->
            <div class="space-y-2">
              <Label>Alias</Label>
              <Input
                v-model="measure.alias"
                placeholder="Optional alias"
                @update:model-value="updateMeasures"
              />
            </div>

            <!-- Query -->
            <div class="space-y-2">
              <Label>Query</Label>
              <Input
                v-model="measure.query"
                placeholder="column_name or expression"
                @update:model-value="updateMeasures"
              />
            </div>

            <!-- Table -->
            <div class="space-y-2">
              <Label>Table</Label>
              <Select v-model="measure.table" @update:model-value="updateMeasures">
                <SelectTrigger>
                  <SelectValue placeholder="Select table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea
              v-model="measure.description"
              placeholder="Describe what this measure represents..."
              rows="2"
              @update:model-value="updateMeasures"
            />
          </div>

          

          <!-- Output Formatting -->
          <OutputFormatEditor
            v-model="measure.formatting"
            object-type="measure"
            @update:model-value="updateMeasures"
          />
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
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Target, X, Code } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import OutputFormatEditor from './OutputFormatEditor.vue'

interface Measure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
}

interface Props {
  measures?: Measure[]
  availableColumns?: Array<{ name: string; type: string }>
  tableSchema?: any
}

const props = withDefaults(defineProps<Props>(), {
  measures: () => []
})

const emit = defineEmits<{
  'update:measures': [value: Measure[]]
}>()

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const measures = ref<Measure[]>([...props.measures])

// Watch for changes from parent
watch(() => props.measures, (newMeasures) => {
  measures.value = [...newMeasures]
})

const updateMeasures = () => {
  emit('update:measures', measures.value)
}

const toSnakeCase = (str: string) => {
  if (!str) return '';
  return String(str)
    .replace(/^[^A-Za-z0-9]*|[^A-Za-z0-9]*$/g, '')
    .replace(/([a-z])([A-Z])/g, (m, a, b) => `${a}_${b.toLowerCase()}`)
    .replace(/[^A-Za-z0-9]+|_+/g, '_')
    .toLowerCase();
};

const handleNameChange = (measure: Measure, newName: string | number) => {
  const newNameStr = String(newName);
    const snakeCaseName = toSnakeCase(newNameStr);
  // Auto-fill alias and query only if they are empty or were auto-filled before
  if (!measure.alias || measure.alias === toSnakeCase(measure.name)) {
    measure.alias = snakeCaseName;
  }
  if (!measure.query || measure.query === toSnakeCase(measure.name)) {
    measure.query = snakeCaseName;
  }
    measure.name = newNameStr;
  updateMeasures();
};

const addMeasure = (tableName: string, column: any) => {
  const newMeasure: Measure = {
    name: `${column.name}_measure`,
    description: `Measure based on ${tableName}.${column.name}`,
    type: getDefaultType(column.type),
    table: tableName,
    alias: column.name,
    query: column.name,
    formatting: []
  }
  
  measures.value.push(newMeasure)
  updateMeasures()
}

const addCustomMeasure = () => {
  const newMeasure: Measure = {
    name: 'custom_measure',
    description: 'Custom measure',
    type: 'custom',
    query: 'custom_measure',
    alias: 'custom_measure',
    table: undefined, // User will select table manually
    formatting: []
  }
  
  measures.value.push(newMeasure)
  updateMeasures()
}

const removeMeasure = (index: number) => {
  measures.value.splice(index, 1)
  updateMeasures()
}

const getDefaultType = (columnType: string): string => {
  const type = columnType.toLowerCase()
  
  if (type.includes('int') || type.includes('decimal') || type.includes('float') || type.includes('numeric')) {
    return 'sum'
  } else if (type.includes('date') || type.includes('timestamp')) {
    return 'count'
  } else {
    return 'count'
  }
}
</script> 