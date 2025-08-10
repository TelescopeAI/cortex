<script setup lang="ts">
import { reactive, computed, watch } from 'vue'
import { Label } from '~/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Trash2, Plus } from 'lucide-vue-next'
import FieldMappingSelector from './FieldMappingSelector.vue'

interface FieldMapping {
  field: string
  data_type: string
  label?: string
  required?: boolean
}

interface ColumnMapping {
  field: string
  label: string
  width?: number
  sortable?: boolean
  filterable?: boolean
  alignment?: string
}

interface DataMapping {
  x_axis?: FieldMapping
  y_axis?: FieldMapping
  value_field?: FieldMapping
  category_field?: FieldMapping
  series_field?: FieldMapping
  columns?: ColumnMapping[]
}

interface Props {
  visualizationType: string
  mapping?: DataMapping
  availableTables: Array<{ name: string; columns: Array<{ name: string; type: string }> }>
}

interface Emits {
  (e: 'update', mapping: DataMapping): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const currentMapping = reactive<DataMapping>(props.mapping || {})

// Visualization type requirements
const requiresXY = computed(() => 
  ['bar_chart', 'line_chart', 'area_chart', 'scatter_plot'].includes(props.visualizationType)
)

const requiresValue = computed(() => 
  ['single_value', 'gauge'].includes(props.visualizationType)
)

const requiresCategory = computed(() => 
  ['pie_chart', 'donut_chart'].includes(props.visualizationType)
)

const requiresColumns = computed(() => 
  props.visualizationType === 'table'
)

const supportsSeries = computed(() => 
  ['bar_chart', 'line_chart', 'area_chart'].includes(props.visualizationType)
)

// Watch for changes and emit updates
watch(currentMapping, (newMapping) => {
  emit('update', newMapping)
}, { deep: true })

function updateFieldMapping(field: keyof DataMapping, mapping: FieldMapping) {
  if (field === 'columns') {
    // Skip for columns as it has different type
    return
  }
  (currentMapping as any)[field] = mapping
}

function addColumn() {
  if (!currentMapping.columns) {
    currentMapping.columns = []
  }
  currentMapping.columns.push({
    field: '',
    label: '',
    sortable: true,
    filterable: true
  })
}

function removeColumn(index: number) {
  if (currentMapping.columns) {
    currentMapping.columns.splice(index, 1)
  }
}

function updateColumn(index: number, field: string, column: { name: string; type: string }) {
  if (currentMapping.columns && currentMapping.columns[index]) {
    currentMapping.columns[index].field = column.name
    currentMapping.columns[index].label = column.name
  }
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <Label class="text-base font-medium">Data Mapping</Label>
      <p class="text-sm text-muted-foreground">
        Configure how metric data maps to your visualization
      </p>
    </div>

    <!-- X/Y Axis for Charts -->
    <div v-if="requiresXY" class="grid grid-cols-2 gap-4">
      <FieldMappingSelector
        label="X Axis"
        :mapping="currentMapping.x_axis"
        :available-tables="availableTables"
        :data-types="['categorical', 'temporal']"
        required
        @update="(mapping) => updateFieldMapping('x_axis', mapping)"
      />
      <FieldMappingSelector
        label="Y Axis"
        :mapping="currentMapping.y_axis"
        :available-tables="availableTables"
        :data-types="['numerical']"
        required
        @update="(mapping) => updateFieldMapping('y_axis', mapping)"
      />
    </div>

    <!-- Value Field for Single Values and Gauges -->
    <div v-if="requiresValue">
      <FieldMappingSelector
        label="Value Field"
        :mapping="currentMapping.value_field"
        :available-tables="availableTables"
        :data-types="['numerical']"
        required
        @update="(mapping) => updateFieldMapping('value_field', mapping)"
      />
    </div>

    <!-- Category Field for Pie/Donut Charts -->
    <div v-if="requiresCategory" class="grid grid-cols-2 gap-4">
      <FieldMappingSelector
        label="Category Field"
        :mapping="currentMapping.category_field"
        :available-tables="availableTables"
        :data-types="['categorical']"
        required
        @update="(mapping) => updateFieldMapping('category_field', mapping)"
      />
      <FieldMappingSelector
        label="Value Field"
        :mapping="currentMapping.value_field"
        :available-tables="availableTables"
        :data-types="['numerical']"
        required
        @update="(mapping) => updateFieldMapping('value_field', mapping)"
      />
    </div>

    <!-- Series Field for Multi-Series Charts -->
    <div v-if="supportsSeries">
      <FieldMappingSelector
        label="Series Field (optional)"
        :mapping="currentMapping.series_field"
        :available-tables="availableTables"
        :data-types="['categorical']"
        @update="(mapping) => updateFieldMapping('series_field', mapping)"
      />
    </div>

    <!-- Column Configuration for Tables -->
    <Card v-if="requiresColumns">
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle class="text-sm">Table Columns</CardTitle>
          <Button size="sm" variant="outline" @click="addColumn">
            <Plus class="w-4 h-4 mr-1" />
            Add Column
          </Button>
        </div>
      </CardHeader>
      <CardContent class="space-y-3">
        <div v-if="!currentMapping.columns || currentMapping.columns.length === 0" class="text-center py-4 text-muted-foreground">
          No columns configured. Add columns to display in your table.
        </div>
        <div
          v-else
          v-for="(column, index) in currentMapping.columns"
          :key="index"
          class="flex items-center gap-2 p-3 border rounded-lg"
        >
          <div class="flex-1">
            <ColumnSelector
              :available-tables="availableTables"
              :button-text="column.field || 'Select Column'"
              @select="(tableName, col) => updateColumn(index, tableName, col)"
            />
          </div>
          <Button
            size="icon"
            variant="ghost"
            @click="removeColumn(index)"
            class="text-destructive"
          >
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
