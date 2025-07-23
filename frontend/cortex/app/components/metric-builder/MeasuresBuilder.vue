<template>
  <div class="space-y-4">
    <!-- Add Measure Button -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Measures</h4>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="outline" size="sm">
            <Plus class="h-4 w-4 mr-2" />
            Add Measure
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuSub v-for="table in availableTables" :key="table.name">
            <DropdownMenuSubTrigger>
              <Database class="h-4 w-4 mr-2" />
              {{ table.name }}
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem
                v-for="column in table.columns"
                :key="`${table.name}.${column.name}`"
                @click="addMeasure(table.name, column)"
                class="cursor-pointer"
              >
                <span class="font-mono text-sm">{{ column.name }}</span>
                <span class="text-xs text-muted-foreground ml-2">({{ column.type }})</span>
              </DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="addCustomMeasure" class="cursor-pointer">
            <Code class="h-4 w-4 mr-2" />
            Custom Measure
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
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
                @update:model-value="updateMeasures"
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

            <!-- Table -->
            <div class="space-y-2">
              <Label>Table</Label>
              <Input
                v-model="measure.table"
                placeholder="table_name"
                @update:model-value="updateMeasures"
              />
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

          <!-- Custom Query for custom type -->
          <div v-if="measure.type === 'custom'" class="space-y-2">
            <Label>Custom Query Expression</Label>
            <Textarea
              v-model="measure.query"
              placeholder="SUM(column_name * rate) as custom_calculation"
              rows="3"
              class="font-mono text-sm"
              @update:model-value="updateMeasures"
            />
          </div>

          <!-- Format Options -->
          <div class="space-y-2">
            <Label>Output Format</Label>
            <Select v-model="measure.format" @update:model-value="updateMeasures">
              <SelectTrigger>
                <SelectValue placeholder="Default format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="number">Number</SelectItem>
                <SelectItem value="currency">Currency</SelectItem>
                <SelectItem value="percentage">Percentage</SelectItem>
                <SelectItem value="decimal">Decimal</SelectItem>
              </SelectContent>
            </Select>
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
import { Plus, Target, X, Database, Code } from 'lucide-vue-next'

interface Measure {
  name: string
  description?: string
  type: string
  format?: string
  alias?: string
  query?: string
  table?: string
  primary_key?: string
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

const addMeasure = (tableName: string, column: any) => {
  const newMeasure: Measure = {
    name: `${column.name}_measure`,
    description: `Measure based on ${tableName}.${column.name}`,
    type: getDefaultType(column.type),
    table: tableName,
    alias: column.name
  }
  
  measures.value.push(newMeasure)
  updateMeasures()
}

const addCustomMeasure = () => {
  const newMeasure: Measure = {
    name: 'custom_measure',
    description: 'Custom measure',
    type: 'custom',
    query: ''
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