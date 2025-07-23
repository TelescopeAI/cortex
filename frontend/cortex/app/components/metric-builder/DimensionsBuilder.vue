<template>
  <div class="space-y-4">
    <!-- Add Dimension Button -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Dimensions</h4>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="outline" size="sm">
            <Plus class="h-4 w-4 mr-2" />
            Add Dimension
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
                @click="addDimension(table.name, column)"
                class="cursor-pointer"
              >
                <span class="font-mono text-sm">{{ column.name }}</span>
                <span class="text-xs text-muted-foreground ml-2">({{ column.type }})</span>
              </DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>
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

            <!-- Primary Key -->
            <div class="space-y-2">
              <Label>Primary Key</Label>
              <Input
                v-model="dimension.primary_key"
                placeholder="Optional primary key column"
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Plus, Grid, X, Database } from 'lucide-vue-next'

interface Dimension {
  name: string
  description?: string
  primary_key?: string
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
    primary_key: column.primary_key ? column.name : undefined
  }
  
  dimensions.value.push(newDimension)
  updateDimensions()
}

const removeDimension = (index: number) => {
  dimensions.value.splice(index, 1)
  updateDimensions()
}
</script> 