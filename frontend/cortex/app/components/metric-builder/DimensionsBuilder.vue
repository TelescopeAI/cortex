<template>
  <div class="space-y-4">
    <!-- Add Dimension Button -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Dimensions</h4>
      <ColumnSelector
        :available-tables="availableTables"
        button-text="Add Dimension"
        @select="addDimension"
      />
    </div>

    <!-- Dimensions List -->
    <div v-if="dimensions.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Grid class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No dimensions defined</p>
      <p class="text-xs text-muted-foreground">Add a dimension to enable grouping</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(dimension, index) in dimensions"
        :key="index"
        class="p-4"
      >
        <div class="space-y-4">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Grid class="h-4 w-4 text-green-500" />
              <span class="font-medium">{{ dimension.name || 'Unnamed Dimension' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeDimension(index)"
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
                v-model="dimension.name"
                placeholder="dimension_name"
                @update:model-value="updateDimensions"
              />
            </div>

            <!-- Table -->
            <div class="space-y-2">
              <Label>Table</Label>
              <Select v-model="dimension.table" @update:model-value="updateDimensions">
                <SelectTrigger>
                  <SelectValue placeholder="Select table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4">
            <!-- Query -->
            <div class="space-y-2">
              <Label>Query *</Label>
              <Input
                v-model="dimension.query"
                placeholder="e.g., column_name or CAST(column AS type)"
                @update:model-value="updateDimensions"
              />
            </div>
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea
              v-model="dimension.description"
              placeholder="Describe what this dimension represents..."
              rows="2"
              @update:model-value="updateDimensions"
            />
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
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Grid, X } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'

interface Dimension {
  name: string
  description?: string
  query: string
  table?: string
}

interface Props {
  dimensions?: Dimension[]
  availableColumns?: Array<{ name: string; type: string }>
  tableSchema?: any
}

const props = withDefaults(defineProps<Props>(), {
  dimensions: () => []
})

const emit = defineEmits<{
  'update:dimensions': [value: Dimension[]]
}>()

// Get available tables from tableSchema
const availableTables = computed(() => {
  if (!props.tableSchema?.tables) return []
  return props.tableSchema.tables
})

const dimensions = ref<Dimension[]>([...props.dimensions])

// Watch for changes from parent
watch(() => props.dimensions, (newDimensions) => {
  dimensions.value = [...newDimensions]
})

const updateDimensions = () => {
  emit('update:dimensions', dimensions.value)
}

const addDimension = (tableName: string, column: any) => {
  const newDimension: Dimension = {
    name: column.name,
    description: `Dimension based on ${tableName}.${column.name}`,
    query: column.name,
    table: tableName
  }
  
  dimensions.value.push(newDimension)
  updateDimensions()
}

const removeDimension = (index: number) => {
  dimensions.value.splice(index, 1)
  updateDimensions()
}
</script> 