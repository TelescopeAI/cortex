<template>
  <div class="space-y-6">
    <!-- Ordering Enable Toggle -->
    <div class="flex items-center space-x-2">
      <input
        id="ordered-toggle"
        type="checkbox"
        :checked="ordered"
        @change="updateOrdered(($event.target as HTMLInputElement).checked)"
        class="h-4 w-4 rounded border-gray-300"
      />
      <Label for="ordered-toggle" class="text-sm font-medium">
        Enable result ordering
      </Label>
    </div>

    <!-- Order Sequences Configuration -->
    <div v-if="ordered" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h4 class="text-sm font-medium">Order Sequences</h4>
          <p class="text-xs text-muted-foreground">
            Define how results should be sorted. If no sequences are specified, default ordering will be applied.
          </p>
        </div>
        <ColumnSelector
          :available-tables="availableTablesFormatted"
          button-text="Add Order"
          @select="addOrderFromColumn"
        />
      </div>

      <!-- Existing Order Sequences -->
      <div v-if="orderSequences.length > 0" class="space-y-3">
        <div
          v-for="(sequence, index) in orderSequences"
          :key="index"
          class="border rounded-lg p-4 space-y-4"
        >
          <div class="flex items-center justify-between">
            <h5 class="text-sm font-medium">Order Sequence {{ index + 1 }}</h5>
            <Button
              @click="removeOrderSequence(index)"
              size="sm"
              variant="ghost"
              class="text-red-600 hover:text-red-800"
            >
              <Trash2 class="h-4 w-4" />
            </Button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <!-- Name -->
            <div class="space-y-2">
              <Label :for="`sequence-name-${index}`">Name *</Label>
              <Input
                :id="`sequence-name-${index}`"
                v-model="sequence.name"
                placeholder="e.g., revenue_desc"
                required
                @update:model-value="updateOrder"
              />
            </div>

              <!-- Ordering Type Selection -->
              <div class="space-y-2">
                <Label :for="`sequence-type-${index}`">Order By Type *</Label>
                <Select v-model="sequence.semantic_type" @update:model-value="(value) => onOrderTypeChange(index, value)">
                  <SelectTrigger :id="`sequence-type-${index}`">
                    <SelectValue placeholder="Select ordering type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="measure">📊 Measure (recommended)</SelectItem>
                    <SelectItem value="dimension">🏷️ Dimension (recommended)</SelectItem>
                    <SelectItem value="position">🔢 Position in SELECT</SelectItem>
                    <SelectItem value="column">🗂️ Raw Column (legacy)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <!-- Reference Selection (dynamic based on type) -->
              <div class="space-y-2">
                <Label :for="`sequence-reference-${index}`">
                  {{ getReferenceLabelForType(sequence.semantic_type) }} *
                </Label>
                
                <!-- Measure Selection -->
                <Select 
                  v-if="sequence.semantic_type === 'measure'"
                  v-model="sequence.semantic_name" 
                  @update:model-value="updateOrder"
                >
                  <SelectTrigger :id="`sequence-reference-${index}`">
                    <SelectValue placeholder="Select measure" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem
                      v-for="measure in measures || []"
                      :key="`measure-${measure.name}`"
                      :value="measure.name"
                    >
                      📊 {{ measure.name }}
                    </SelectItem>
                  </SelectContent>
                </Select>

                <!-- Dimension Selection -->
                <Select 
                  v-if="sequence.semantic_type === 'dimension'"
                  v-model="sequence.semantic_name" 
                  @update:model-value="updateOrder"
                >
                  <SelectTrigger :id="`sequence-reference-${index}`">
                    <SelectValue placeholder="Select dimension" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem
                      v-for="dimension in dimensions || []"
                      :key="`dimension-${dimension.name}`"
                      :value="dimension.name"
                    >
                      🏷️ {{ dimension.name }}
                    </SelectItem>
                  </SelectContent>
                </Select>

                <!-- Position Selection -->
                <Input
                  v-if="sequence.semantic_type === 'position'"
                  :id="`sequence-reference-${index}`"
                  v-model.number="sequence.position"
                  type="number"
                  min="1"
                  placeholder="Position in SELECT (1, 2, 3...)"
                  @update:model-value="updateOrder"
                />

                <!-- Raw Column Selection (Legacy) -->
                <div v-if="sequence.semantic_type === 'column'" class="space-y-2">
                  <Select v-model="sequence.query" @update:model-value="updateOrder">
                    <SelectTrigger :id="`sequence-reference-${index}`">
                      <SelectValue placeholder="Select column" />
                    </SelectTrigger>
                    <SelectContent>
                      <template v-for="table in availableTablesFormatted">
                        <SelectItem
                          v-for="column in table.columns"
                          :key="`column-${table.name}.${column.name}`"
                          :value="table.name === 'Measures' || table.name === 'Dimensions' ? column.name : column.name"
                        >
                          🗂️ {{ table.name === 'Measures' || table.name === 'Dimensions' ? '' : `${table.name}.` }}{{ column.name }} ({{ column.type }})
                        </SelectItem>
                      </template>
                    </SelectContent>
                  </Select>
                </div>
              </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <!-- Order Type -->
            <div class="space-y-2">
              <Label :for="`sequence-order-type-${index}`">Order Direction</Label>
              <Select v-model="sequence.order_type" @update:model-value="updateOrder">
                <SelectTrigger :id="`sequence-order-type-${index}`">
                  <SelectValue placeholder="Order direction" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="asc">Ascending</SelectItem>
                  <SelectItem value="desc">Descending</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Nulls Position -->
            <div class="space-y-2">
              <Label :for="`sequence-nulls-${index}`">Null Values</Label>
              <Select v-model="sequence.nulls" @update:model-value="updateOrder">
                <SelectTrigger :id="`sequence-nulls-${index}`">
                  <SelectValue placeholder="Null handling" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="first">Nulls First</SelectItem>
                  <SelectItem value="last">Nulls Last</SelectItem>
                </SelectContent>
              </Select>
            </div>

                <!-- Table (optional) -->
                <div class="space-y-2">
                  <Label :for="`sequence-table-${index}`">Table (optional)</Label>
                  <Select v-model="sequence.table" @update:model-value="updateOrder">
                    <SelectTrigger :id="`sequence-table-${index}`">
                      <SelectValue placeholder="Select table" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem
                        v-for="table in availableTables"
                        :key="table.name"
                        :value="table.name"
                      >
                        {{ table.name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <Label :for="`sequence-description-${index}`">Description</Label>
            <Input
              :id="`sequence-description-${index}`"
              v-model="sequence.description"
              placeholder="Describe this ordering rule"
              @update:model-value="updateOrder"
            />
          </div>
        </div>
      </div>

          <!-- Default Ordering Info -->
          <div v-if="orderSequences.length === 0" class="rounded-lg bg-muted p-4">
            <div class="flex items-start space-x-3">
              <Info class="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <h5 class="text-sm font-medium">Smart Default Ordering</h5>
                <p class="text-xs text-muted-foreground mt-1">
                  Our semantic system automatically applies intelligent default ordering:
                </p>
                <ul class="text-xs text-muted-foreground mt-2 space-y-1 list-disc list-inside">
                  <li><strong>Time dimensions</strong> with granularity → ascending (chronological)</li>
                  <li><strong>Measures</strong> (if no time) → descending (highest values first)</li>
                  <li><strong>Dimensions</strong> (if no measures) → ascending (alphabetical)</li>
                </ul>
                <div class="mt-2 p-2 bg-green-50 rounded border border-green-200 dark:bg-green-950 dark:border-green-800">
                  <p class="text-xs text-green-700 dark:text-green-300">
                    💡 <strong>Tip:</strong> Use semantic ordering (📊 Measures, 🏷️ Dimensions) for context-aware SQL generation that prevents GROUP BY errors!
                  </p>
                </div>
              </div>
            </div>
          </div>
    </div>

    <!-- Disabled State Info -->
    <div v-else class="rounded-lg bg-muted p-4">
      <div class="flex items-start space-x-3">
        <AlertCircle class="h-5 w-5 text-muted-foreground mt-0.5" />
        <div>
          <h5 class="text-sm font-medium">Ordering Disabled</h5>
          <p class="text-xs text-muted-foreground mt-1">
            Query results will not be sorted when ordering is disabled.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Plus, Trash2, Info, AlertCircle } from 'lucide-vue-next'
import type { SemanticOrderSequence, SemanticOrderReferenceType } from '~/types/order'
import ColumnSelector from '~/components/ColumnSelector.vue'

interface Props {
  order?: SemanticOrderSequence[]
  ordered?: boolean
  availableColumns?: Array<{ name: string; type: string }>
  measures?: Array<{ name: string; table?: string }>
  dimensions?: Array<{ name: string; table?: string }>
  availableTables?: Array<{ name: string; columns: Array<{ name: string; type: string }> }>
}

interface Emits {
  (e: 'update:order', value: SemanticOrderSequence[]): void
  (e: 'update:ordered', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  order: () => [],
  ordered: true,
  availableColumns: () => [],
  measures: () => [],
  dimensions: () => [],
  availableTables: () => []
})

const emit = defineEmits<Emits>()

// Simple reactive state with prop watchers
const orderSequences = ref<SemanticOrderSequence[]>([...props.order])
const ordered = ref(props.ordered ?? true)

// Watch for prop changes (needed for edit mode)
watch(() => props.order, (newOrder) => {
  if (newOrder && JSON.stringify(newOrder) !== JSON.stringify(orderSequences.value)) {
    orderSequences.value = [...newOrder]
  }
}, { deep: true })

watch(() => props.ordered, (newOrdered) => {
  if (newOrdered !== undefined && newOrdered !== ordered.value) {
    ordered.value = newOrdered
  }
})

// Simple update functions
const updateOrder = () => {
  emit('update:order', orderSequences.value)
}

const updateOrdered = (value: boolean) => {
  ordered.value = value
  emit('update:ordered', value)
}

// Computed properties
const availableTablesFormatted = computed(() => {
  const tables: Array<{ name: string; columns: Array<{ name: string; type: string }> }> = []

  // Add measures as a virtual table
  if (props.measures && props.measures.length > 0) {
    tables.push({
      name: 'Measures',
      columns: props.measures.map(measure => ({
        name: measure.name,
        type: 'measure'
      }))
    })
  }
  
  // Add dimensions as a virtual table  
  if (props.dimensions && props.dimensions.length > 0) {
    tables.push({
      name: 'Dimensions', 
      columns: props.dimensions.map(dimension => ({
        name: dimension.name,
        type: 'dimension'
      }))
    })
  }
  
  // Group available columns by table name
  const columnsByTable = new Map<string, Array<{ name: string; type: string }>>()
  
  props.availableColumns?.forEach(column => {
    const [tableName, ...columnParts] = column.name.split('.')
    const columnName = columnParts.length > 0 ? columnParts.join('.') : column.name
    const table = tableName || 'Columns'
    
    if (!columnsByTable.has(table)) {
      columnsByTable.set(table, [])
    }
    columnsByTable.get(table)?.push({
      name: columnName,
      type: column.type
    })
  })
  
  // Convert grouped columns to table format
  columnsByTable.forEach((columns, tableName) => {
    tables.push({
      name: tableName,
      columns
    })
  })
  
  return tables
})

// Methods
const getReferenceLabelForType = (semanticType?: string): string => {
  switch (semanticType) {
    case 'measure': return 'Measure'
    case 'dimension': return 'Dimension'
    case 'position': return 'Position (1-based)'
    case 'column': return 'Column'
    default: return 'Reference'
  }
}

const onOrderTypeChange = (index: number, semanticType: any) => {
  if (!orderSequences.value[index]) return
  
  // Clear existing reference data when type changes
  orderSequences.value[index].semantic_name = undefined
  orderSequences.value[index].position = undefined
  orderSequences.value[index].query = undefined
  orderSequences.value[index].table = undefined
  
  updateOrder()
}

const addOrderFromColumn = (tableName: string, column: { name: string; type: string }) => {
  let orderType: 'asc' | 'desc' = 'asc'
  let newSequence: SemanticOrderSequence

  if (tableName === 'Measures') {
    // Semantic measure ordering (recommended)
    orderType = 'desc' // Measures typically descending
    newSequence = {
      name: `order_${column.name}`,
      semantic_type: 'measure',
      semantic_name: column.name,
      order_type: orderType,
      description: `Order by ${column.name} measure`,
      nulls: undefined
    }
  } else if (tableName === 'Dimensions') {
    // Semantic dimension ordering (recommended)
    orderType = 'asc' // Dimensions typically ascending
    newSequence = {
      name: `order_${column.name}`,
      semantic_type: 'dimension',
      semantic_name: column.name,
      order_type: orderType,
      description: `Order by ${column.name} dimension`,
      nulls: undefined
    }
  } else {
    // Legacy column ordering for raw table columns
    orderType = 'asc'
    newSequence = {
      name: `order_${column.name}`,
      semantic_type: 'column',
      query: column.name,
      table: tableName !== 'Columns' ? tableName : undefined,
      order_type: orderType,
      description: `Order by ${column.name} column`,
      nulls: undefined
    }
  }

  orderSequences.value.push(newSequence)
  updateOrder()
}

const removeOrderSequence = (index: number) => {
  orderSequences.value.splice(index, 1)
  updateOrder()
}
</script>
