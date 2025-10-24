<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Grid, X, Settings, ChevronDown, GitBranch } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import OutputFormatEditor from '../OutputFormatEditor.vue'
import SimpleDimension from './Simple.vue'
import ConditionalDimension from './Conditional.vue'
import { humanize } from '~/utils/stringCase'
import type { Condition } from '~/types/conditionals'

interface CombineColumnSpec {
  query: string
  table?: string
  delimiter?: string
}

interface Dimension {
  name: string
  description?: string
  query: string
  table?: string
  formatting?: any[]
  combine?: CombineColumnSpec[]
  conditional?: boolean
  conditions?: Condition | null
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
const showAdvanced = ref<Record<number, boolean>>({})
const isLocalUpdate = ref(false)

// Watch for changes from parent (but not from our own updates)
watch(() => props.dimensions, (newDimensions) => {
  // Skip if this was triggered by our own local update
  if (isLocalUpdate.value) {
    isLocalUpdate.value = false
    return
  }
  dimensions.value = [...newDimensions]
})

const updateDimensions = () => {
  isLocalUpdate.value = true
  emit('update:dimensions', dimensions.value)
}

const toggleAdvanced = (index: number) => {
  showAdvanced.value[index] = !showAdvanced.value[index]
}

const addDimension = (tableName: string, column: any) => {
  const humanizedName = humanize(column.name)
  
  const newDimension: Dimension = {
    name: humanizedName,
    description: `Dimension based on ${tableName}.${column.name}`,
    query: column.name,
    table: tableName,
    formatting: [],
    combine: [],
    conditional: false
  }
  
  dimensions.value.push(newDimension)
  updateDimensions()
}

const addConditionalDimension = () => {
  const newDimension: Dimension = {
    name: 'Conditional Dimension',
    description: 'Dimension with conditional logic',
    query: '',
    table: availableTables.value[0]?.name,
    formatting: [],
    conditional: true,
    conditions: {
      when_clauses: [],
      else_return: ''
    }
  }
  
  dimensions.value.push(newDimension)
  updateDimensions()
}

const removeDimension = (index: number) => {
  dimensions.value.splice(index, 1)
  updateDimensions()
}

const updateDimension = (index: number, updates: Dimension) => {
  dimensions.value[index] = updates
  updateDimensions()
}
</script>

<template>
  <div class="space-y-4">
    <!-- Add Dimension Buttons -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Dimensions</h4>
      <div class="flex items-center space-x-2">
        <ColumnSelector
          :available-tables="availableTables"
          button-text="Add Dimension"
          @select="addDimension"
        />
        <Button variant="outline" size="sm" @click="addConditionalDimension">
          <GitBranch class="h-4 w-4 mr-2" />
          Add Condition
        </Button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="dimensions.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Grid class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No dimensions defined</p>
      <p class="text-xs text-muted-foreground">Add a dimension to enable grouping</p>
    </div>

    <!-- Dimensions List -->
    <div v-else class="space-y-3">
      <Card 
        v-for="(dimension, index) in dimensions"
        :key="index"
        class="p-5 hover:shadow-md transition-shadow"
      >
        <div class="space-y-5">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div :class="[
                'p-1.5 rounded-md',
                dimension.conditional 
                  ? 'bg-purple-50 dark:bg-purple-950' 
                  : 'bg-green-50 dark:bg-green-950'
              ]">
                <GitBranch 
                  v-if="dimension.conditional"
                  class="h-4 w-4 text-purple-600 dark:text-purple-400" 
                />
                <Grid 
                  v-else
                  class="h-4 w-4 text-green-600 dark:text-green-400" 
                />
              </div>
              <span class="font-medium text-base">{{ dimension.name || 'Unnamed Dimension' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeDimension(index)"
              class="hover:bg-red-50 hover:text-red-600"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Simple or Conditional Component -->
          <SimpleDimension
            v-if="!dimension.conditional"
            :dimension="dimension"
            :available-tables="availableTables"
            @update:dimension="updateDimension(index, $event)"
          />
          
          <ConditionalDimension
            v-else
            :dimension="dimension"
            :available-tables="availableTables"
            @update:dimension="updateDimension(index, $event)"
          />

          <!-- Name -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">Name it as</span>
            <Input
              :model-value="dimension.name"
              @update:model-value="(val) => { dimension.name = val; updateDimensions(); }"
              placeholder="Dimension name"
              class="flex-1 h-9"
            />
          </div>

          <!-- Advanced Section -->
          <div class="pt-3">
            <button 
              type="button"
              class="flex items-center justify-between w-full text-xs text-muted-foreground hover:text-foreground transition-colors group"
              @click="toggleAdvanced(index)"
            >
              <span class="flex items-center gap-1.5">
                <Settings class="h-3.5 w-3.5" />
                Advanced
              </span>
              <ChevronDown :class="['h-3.5 w-3.5 transition-transform duration-200', showAdvanced[index] && 'rotate-180']" />
            </button>

            <div 
              v-if="showAdvanced[index]" 
              class="mt-4 space-y-4 pt-4 border-t"
            >
              <!-- Description -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                <Textarea
                  :model-value="dimension.description"
                  @update:model-value="(val) => { dimension.description = val; updateDimensions(); }"
                  placeholder="Describe what this dimension represents..."
                  rows="2"
                  class="resize-none"
                />
              </div>

              <!-- Output Formatting -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Output Formatting</Label>
                <OutputFormatEditor
                  :model-value="dimension.formatting"
                  @update:model-value="(val) => { dimension.formatting = val; updateDimensions(); }"
                  object-type="dimension"
                />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

