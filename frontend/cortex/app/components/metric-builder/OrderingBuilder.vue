<template>
  <div class="space-y-6">
    <!-- Ordering Enable Toggle -->
    <div class="flex items-center space-x-2">
      <input
        id="ordered-toggle"
        type="checkbox"
        :checked="props.ordered"
        @change="updateOrdered(($event.target as HTMLInputElement).checked)"
        class="h-4 w-4 rounded border-gray-300"
      />
      <Label for="ordered-toggle" class="text-sm font-medium">
        Enable result ordering
      </Label>
    </div>

    <!-- Order Sequences Configuration -->
    <div v-if="props.ordered" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h4 class="text-sm font-medium">Order Sequences</h4>
          <p class="text-xs text-muted-foreground">
            Define how results should be sorted
          </p>
        </div>
        <ColumnSelector
          :available-tables="availableTablesFormatted"
          button-text="Add Order"
          @select="addOrderFromColumn"
        />
      </div>

      <!-- Empty State -->
      <div v-if="props.order.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
        <ArrowUpDown class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p class="text-sm text-muted-foreground">No ordering defined</p>
        <p class="text-xs text-muted-foreground">Default ordering will be applied</p>
      </div>

      <!-- Existing Order Sequences -->
      <div v-else class="space-y-3">
        <Card
          v-for="(sequence, index) in props.order"
          :key="index"
          class="p-5 hover:shadow-md transition-shadow"
        >
          <div class="space-y-5">
            <!-- Header -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <div class="p-1.5 rounded-md bg-purple-50 dark:bg-purple-950">
                  <ArrowUpDown class="h-4 w-4 text-purple-600 dark:text-purple-400" />
                </div>
                <span class="font-medium text-base">{{ sequence.name || `Order ${index + 1}` }}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                @click="removeOrderSequence(index)"
                class="hover:bg-red-50 hover:text-red-600"
              >
                <X class="h-4 w-4" />
              </Button>
            </div>

            <!-- Sentence-Completion Interface -->
            <div class="space-y-3">
              <!-- Row 1: Sort by [type] [reference] in [order] order -->
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm text-muted-foreground">Sort by</span>
                
                <!-- Semantic Type Selection -->
                <Select :model-value="sequence.semantic_type" @update:model-value="(value) => onOrderTypeChange(index, value)">
                  <SelectTrigger class="w-auto min-w-[110px] h-9">
                    <SelectValue placeholder="type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="measure">measure</SelectItem>
                    <SelectItem value="dimension">dimension</SelectItem>
                    <SelectItem value="column">column</SelectItem>
                    <SelectItem value="position">position</SelectItem>
                  </SelectContent>
                </Select>

                <!-- Reference Selection (dynamic based on type) -->
                <template v-if="sequence.semantic_type === 'measure'">
                  <Select :model-value="sequence.semantic_name" @update:model-value="(val) => updateSequenceField(index, 'semantic_name', val)">
                    <SelectTrigger class="w-auto min-w-[180px] h-9">
                      <SelectValue placeholder="Select measure" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="measure in measures" :key="measure.name" :value="measure.name">
                        {{ measure.name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </template>

                <template v-else-if="sequence.semantic_type === 'dimension'">
                  <Select :model-value="sequence.semantic_name" @update:model-value="(val) => updateSequenceField(index, 'semantic_name', val)">
                    <SelectTrigger class="w-auto min-w-[180px] h-9">
                      <SelectValue placeholder="Select dimension" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="dimension in dimensions" :key="dimension.name" :value="dimension.name">
                        {{ dimension.name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </template>

                <template v-else-if="sequence.semantic_type === 'column'">
                  <Input
                    :model-value="sequence.query"
                    placeholder="column_name"
                    class="w-auto min-w-[180px] h-9"
                    @update:model-value="(val) => updateSequenceField(index, 'query', val)"
                  />
                </template>

                <template v-else-if="sequence.semantic_type === 'position'">
                  <Input
                    :model-value="sequence.position"
                    type="number"
                    placeholder="1"
                    class="w-[100px] h-9"
                    @update:model-value="(val) => updateSequenceField(index, 'position', Number(val))"
                  />
                </template>

                <span class="text-sm text-muted-foreground">in</span>

                <!-- Order Type Selection -->
                <Select :model-value="sequence.order_type" @update:model-value="(val) => updateSequenceField(index, 'order_type', val)">
                  <SelectTrigger class="w-auto min-w-[120px] h-9">
                    <SelectValue placeholder="order" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="asc">ascending</SelectItem>
                    <SelectItem value="desc">descending</SelectItem>
                  </SelectContent>
                </Select>

                <span class="text-sm text-muted-foreground">order</span>
              </div>

              <!-- Row 2: Name it as [name] -->
              <div class="flex items-center gap-2">
                <span class="text-sm text-muted-foreground">Name it as</span>
                <Input
                  :model-value="sequence.name"
                  placeholder="Order name"
                  class="flex-1 h-9"
                  @update:model-value="(val) => updateSequenceField(index, 'name', val)"
                />
              </div>
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
                <!-- Table (for column type) -->
                <div v-if="sequence.semantic_type === 'column'" class="space-y-1.5">
                  <Label class="text-xs font-medium text-muted-foreground">Table</Label>
                  <Select :model-value="sequence.table" @update:model-value="(val) => updateSequenceField(index, 'table', val)">
                    <SelectTrigger class="h-9">
                      <SelectValue placeholder="Select table" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">
                        {{ table.name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <!-- Nulls Handling -->
                <div class="space-y-1.5">
                  <Label class="text-xs font-medium text-muted-foreground">Null Values Handling</Label>
                  <Select :model-value="sequence.nulls" @update:model-value="(val) => updateSequenceField(index, 'nulls', val)">
                    <SelectTrigger class="h-9">
                      <SelectValue placeholder="Default" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">Default</SelectItem>
                      <SelectItem value="first">Nulls First</SelectItem>
                      <SelectItem value="last">Nulls Last</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <!-- Description -->
                <div class="space-y-1.5">
                  <Label class="text-xs font-medium text-muted-foreground">Description</Label>
                  <Textarea
                    :model-value="sequence.description"
                    placeholder="Describe this sort order..."
                    rows="2"
                    class="resize-none"
                    @update:model-value="(val) => updateSequenceField(index, 'description', val)"
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
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
import { ArrowUpDown, X, Settings, ChevronDown } from 'lucide-vue-next'
import type { SemanticOrderSequence, SemanticOrderReferenceType } from '~/types/order'
import ColumnSelector from '~/components/ColumnSelector.vue'
import { humanize } from '~/utils/stringCase'

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

const showAdvanced = ref<Record<number, boolean>>({})

// Simple update functions
const updateOrder = (newOrder: SemanticOrderSequence[]) => {
  emit('update:order', newOrder)
}

const updateOrdered = (value: boolean) => {
  emit('update:ordered', value)
}

const toggleAdvanced = (index: number) => {
  showAdvanced.value[index] = !showAdvanced.value[index]
}

const updateSequenceField = (index: number, field: string, value: any) => {
  const updated = [...props.order]
  if (updated[index]) {
    (updated[index] as any)[field] = value
    updateOrder(updated)
  }
}

// Computed properties
const availableTablesFormatted = computed(() => {
  const tables: Array<{ name: string; columns: Array<{ name: string; type: string }> }> = []
  
  // Add measures as a virtual table
  if (props.measures && props.measures.length > 0) {
    tables.push({
      name: 'Measures',
      columns: props.measures.map(m => ({ name: m.name, type: 'measure' }))
    })
  }
  
  // Add dimensions as a virtual table
  if (props.dimensions && props.dimensions.length > 0) {
    tables.push({
      name: 'Dimensions',
      columns: props.dimensions.map(d => ({ name: d.name, type: 'dimension' }))
    })
  }
  
  // Add actual tables
  if (props.availableTables) {
    tables.push(...props.availableTables)
  }
  
  return tables
})

const onOrderTypeChange = (index: number, semanticType: any) => {
  const updated = [...props.order]
  if (!updated[index]) return
  
  // Clear existing reference data when type changes
  updated[index].semantic_name = undefined
  updated[index].position = undefined
  updated[index].query = undefined
  updated[index].table = undefined
  
  updateOrder(updated)
}

const addOrderFromColumn = (tableName: string, column: { name: string; type: string }) => {
  const humanizedName = humanize(column.name)
  let orderType: 'asc' | 'desc' = 'asc'
  let newSequence: SemanticOrderSequence

  if (tableName === 'Measures') {
    // Semantic measure ordering (recommended)
    orderType = 'desc' // Measures typically descending
    newSequence = {
      name: humanizedName,
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
      name: humanizedName,
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
      name: humanizedName,
      semantic_type: 'column',
      query: column.name,
      table: tableName !== 'Columns' ? tableName : undefined,
      order_type: orderType,
      description: `Order by ${column.name} column`,
      nulls: undefined
    }
  }

  updateOrder([...props.order, newSequence])
}

const removeOrderSequence = (index: number) => {
  const updated = [...props.order]
  updated.splice(index, 1)
  updateOrder(updated)
}
</script>
