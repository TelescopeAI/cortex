<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Target, X, Code, Settings, ChevronDown, GitBranch } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import OutputFormatEditor from '../OutputFormatEditor.vue'
import SimpleMeasure from './Simple.vue'
import ConditionalMeasure from './Conditional.vue'
import { toSnakeCase, humanize } from '~/utils/stringCase'
import type { Condition } from '~/types/conditionals'

interface Measure {
  name: string
  description?: string
  type: string
  formatting?: any[]
  alias?: string
  query?: string
  table?: string
  conditional?: boolean
  conditions?: Condition | null
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

const showAdvanced = ref<Record<number, boolean>>({})

const updateMeasures = (newMeasures: Measure[]) => {
  emit('update:measures', newMeasures)
}

const toggleAdvanced = (index: number) => {
  showAdvanced.value[index] = !showAdvanced.value[index]
}

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
  // Emit the updated array
  updateMeasures([...props.measures]);
};

const addMeasure = (tableName: string, column: any) => {
  const humanizedName = humanize(column.name)
  const snakeCaseName = toSnakeCase(humanizedName)
  
  const newMeasure: Measure = {
    name: humanizedName,
    description: `Measure based on ${tableName}.${column.name}`,
    type: getDefaultType(column.type),
    table: tableName,
    alias: column.name,
    query: column.name,
    formatting: [],
    conditional: false
  }
  
  updateMeasures([...props.measures, newMeasure])
}

const addConditionalMeasure = () => {
  const newMeasure: Measure = {
    name: 'Conditional Measure',
    description: 'Measure with conditional logic',
    type: 'sum',
    table: availableTables.value[0]?.name,
    alias: 'conditional_measure',
    query: '',
    formatting: [],
    conditional: true,
    conditions: {
      when_clauses: [],
      else_return: 0
    }
  }
  
  updateMeasures([...props.measures, newMeasure])
}

const addCustomMeasure = () => {
  const newMeasure: Measure = {
    name: 'Custom Measure',
    description: 'Custom measure',
    type: 'custom',
    query: 'custom_measure',
    alias: 'custom_measure',
    table: undefined,
    formatting: [],
    conditional: false
  }
  
  updateMeasures([...props.measures, newMeasure])
}

const removeMeasure = (index: number) => {
  const updated = [...props.measures]
  updated.splice(index, 1)
  updateMeasures(updated)
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

const updateMeasure = (index: number, updates: Measure) => {
  const updated = [...props.measures]
  updated[index] = updates
  updateMeasures(updated)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Add Measure Buttons -->
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Measures</h4>
      <div class="flex items-center space-x-2">
        <ColumnSelector
          :available-tables="availableTables"
          button-text="Add Measure"
          @select="addMeasure"
        />
        <Button variant="outline" size="sm" @click="addConditionalMeasure">
          <GitBranch class="h-4 w-4 mr-2" />
          Add Condition
        </Button>
        <Button variant="outline" size="sm" @click="addCustomMeasure">
          <Code class="h-4 w-4 mr-2" />
          Custom Measure
        </Button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="props.measures.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Target class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No measures defined</p>
      <p class="text-xs text-muted-foreground">Add a measure to get started</p>
    </div>

    <!-- Measures List -->
    <div v-else class="space-y-3">
      <Card 
        v-for="(measure, index) in props.measures"
        :key="index"
        class="p-5 hover:shadow-md transition-shadow"
      >
        <div class="space-y-5">
          <!-- Header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <div :class="[
                'p-1.5 rounded-md',
                measure.conditional 
                  ? 'bg-purple-50 dark:bg-purple-950' 
                  : 'bg-blue-50 dark:bg-blue-950'
              ]">
                <GitBranch 
                  v-if="measure.conditional"
                  class="h-4 w-4 text-purple-600 dark:text-purple-400" 
                />
                <Target 
                  v-else
                  class="h-4 w-4 text-blue-600 dark:text-blue-400" 
                />
              </div>
              <span class="font-medium text-base">{{ measure.name || 'Unnamed Measure' }}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              @click="removeMeasure(index)"
              class="hover:bg-red-50 hover:text-red-600"
            >
              <X class="h-4 w-4" />
            </Button>
          </div>

          <!-- Simple or Conditional Component -->
          <SimpleMeasure
            v-if="!measure.conditional"
            :measure="measure"
            :available-tables="availableTables"
            @update:measure="updateMeasure(index, $event)"
          />
          
          <ConditionalMeasure
            v-else
            :measure="measure"
            :available-tables="availableTables"
            @update:measure="updateMeasure(index, $event)"
          />

          <!-- Name -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">Name it as</span>
            <Input
              :model-value="measure.name"
              @update:model-value="(value) => handleNameChange(measure, value)"
              placeholder="Measure name"
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
              <!-- Alias -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Alias</Label>
                <Input
                  :model-value="measure.alias"
                  @update:model-value="(val) => { 
                    const updated = [...props.measures];
                    updated[index] = { ...measure, alias: String(val) };
                    updateMeasures(updated);
                  }"
                  placeholder="Optional alias for this measure"
                  class="h-9"
                />
              </div>

              <!-- Description -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                <Textarea
                  :model-value="measure.description"
                  @update:model-value="(val) => { 
                    const updated = [...props.measures];
                    updated[index] = { ...measure, description: String(val) };
                    updateMeasures(updated);
                  }"
                  placeholder="Describe what this measure represents..."
                  rows="2"
                  class="resize-none"
                />
              </div>

              <!-- Output Formatting -->
              <div class="space-y-1.5">
                <Label class="text-xs font-medium text-muted-foreground">Output Formatting</Label>
                <OutputFormatEditor
                  :model-value="measure.formatting"
                  @update:model-value="(val) => { 
                    const updated = [...props.measures];
                    updated[index] = { ...measure, formatting: val };
                    updateMeasures(updated);
                  }"
                  object-type="measure"
                />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

