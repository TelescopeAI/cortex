<template>
  <Card class="border-0 shadow-none">
    <CardHeader>
      <div class="flex items-center justify-between">
        <div>
          <CardTitle>Metric Modifiers</CardTitle>
          <CardDescription>
            Temporarily adjust measures, dimensions, joins, filters, ordering, or limits when executing this metric.
          </CardDescription>
        </div>
        <div class="flex items-center space-x-2">
          <Switch 
            id="modifiers-enabled" 
            :model-value="modifiersEnabled" 
            @update:model-value="$emit('update:modifiersEnabled', $event)" 
          />
          <Label for="modifiers-enabled">Enable modifiers</Label>
        </div>
      </div>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="text-xs text-muted-foreground">
        <p>Modifiers are applied in-order. Each section upserts or overrides matching items on the base metric.</p>
      </div>

      <div v-if="modifiersEnabled" class="space-y-6">
        <div v-if="schemaError" class="rounded border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          Failed to load data source schema: {{ schemaError }}. Some builder features may be limited.
          <Button variant="link" size="sm" class="ml-2 p-0" @click="$emit('reload-schema')" :disabled="schemaLoading">
            {{ schemaLoading ? 'Reloading...' : 'Retry' }}
          </Button>
        </div>

        <div v-if="schemaLoading" class="rounded border border-dashed p-4 text-sm text-muted-foreground">
          Loading data source schema...
        </div>

        <div class="flex justify-end">
          <Button variant="outline" size="sm" @click="addModifier">
            <Plus class="h-4 w-4 mr-2" />
            Add Modifier
          </Button>
        </div>

        <div v-if="localModifiers.length === 0" class="rounded border border-dashed p-6 text-center text-sm text-muted-foreground">
          No modifiers defined. Add one to customize this execution.
        </div>

        <div v-for="(modifier, index) in localModifiers" :key="`modifier-${index}`" class="space-y-4 rounded-lg border p-4">
          <div class="flex items-center justify-between">
            <div class="font-medium text-sm">Modifier {{ index + 1 }}</div>
            <div class="flex items-center space-x-2">
              <Button variant="ghost" size="sm" @click="removeModifier(index)">
                <Trash2 class="h-4 w-4" />
                Remove
              </Button>
            </div>
          </div>

          <div class="space-y-6">
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label>Measures</Label>
                <Button variant="ghost" size="sm" @click="clearModifierSection(index, 'measures')"
                  :disabled="!modifier.measures || modifier.measures.length === 0">
                  Clear
                </Button>
              </div>
              <MeasuresBuilder
                :table-schema="tableSchema"
                :available-columns="availableColumns"
                :measures="modifier.measures || []"
                @update:measures="(value: any) => updateModifierSection(index, 'measures', value)"
              />
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label>Dimensions</Label>
                <Button variant="ghost" size="sm" @click="clearModifierSection(index, 'dimensions')"
                  :disabled="!modifier.dimensions || modifier.dimensions.length === 0">
                  Clear
                </Button>
              </div>
              <DimensionsBuilder
                :table-schema="tableSchema"
                :dimensions="modifier.dimensions || []"
                @update:dimensions="(value: any) => updateModifierSection(index, 'dimensions', value)"
              />
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label>Joins</Label>
                <Button variant="ghost" size="sm" @click="clearModifierSection(index, 'joins')"
                  :disabled="!modifier.joins || modifier.joins.length === 0">
                  Clear
                </Button>
              </div>
              <JoinsBuilder
                :model-value="modifier.joins || []"
                :available-tables="availableTables"
                @update:model-value="(value: any) => updateModifierSection(index, 'joins', value)"
              />
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label>Filters</Label>
                <Button variant="ghost" size="sm" @click="clearModifierSection(index, 'filters')"
                  :disabled="!modifier.filters || modifier.filters.length === 0">
                  Clear
                </Button>
              </div>
              <FiltersBuilder
                :filters="(modifier.filters || []) as any[]"
                :table-schema="tableSchema"
                @update:filters="(value: any) => updateModifierSection(index, 'filters', value)"
              />
            </div>

            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <Label>Ordering</Label>
                <Button variant="ghost" size="sm" @click="clearModifierSection(index, 'order')"
                  :disabled="!modifier.order || modifier.order.length === 0">
                  Clear
                </Button>
              </div>
              <OrderingBuilder
                :order="modifier.order || []"
                :ordered="true"
                :available-columns="availableColumns"
                :measures="metric?.measures || []"
                :dimensions="metric?.dimensions || []"
                :available-tables="availableTables"
                @update:order="(value: any) => updateModifierSection(index, 'order', value)"
              />
            </div>

            <div class="space-y-2">
              <Label>Limit Override</Label>
              <div class="flex items-center space-x-3">
                <Switch
                  :id="`modifier-limit-toggle-${index}`"
                  :model-value="modifier.limit !== undefined && modifier.limit !== null"
                  @update:model-value="(enabled: boolean) => toggleModifierLimit(index, enabled)"
                />
                <div v-if="modifier.limit !== undefined && modifier.limit !== null" class="flex items-center space-x-2">
                  <Input
                    class="w-32"
                    type="number"
                    min="1"
                    placeholder="100"
                    :model-value="modifier.limit ?? ''"
                    @input="(event: any) => updateModifierLimit(index, parseInt(event?.target?.value || '0', 10))"
                  />
                  <span class="text-sm text-muted-foreground">rows</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { Plus, Trash2 } from 'lucide-vue-next'
import MeasuresBuilder from '~/components/metric/builder/MeasuresBuilder.vue'
import DimensionsBuilder from '~/components/metric/builder/DimensionsBuilder.vue'
import JoinsBuilder from '~/components/metric/builder/JoinsBuilder.vue'
import FiltersBuilder from '~/components/metric/builder/FiltersBuilder.vue'
import OrderingBuilder from '~/components/metric/builder/OrderingBuilder.vue'
import type { MetricModifier, MetricModifiers } from '~/types/metric-modifiers'
import { createMetricModifier } from '~/types/metric-modifiers'

interface Props {
  modifiersEnabled: boolean
  modifiers: MetricModifiers
  tableSchema: any
  availableTables: any[]
  availableColumns: any[]
  metric: any
  schemaLoading: boolean
  schemaError: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modifiersEnabled': [value: boolean]
  'update:modifiers': [value: MetricModifiers]
  'reload-schema': []
}>()

const localModifiers = ref<MetricModifiers>([...props.modifiers])

watch(() => props.modifiers, (newModifiers) => {
  localModifiers.value = [...newModifiers]
}, { deep: true })

const emitUpdate = () => {
  emit('update:modifiers', [...localModifiers.value])
}

const ensureModifierAt = (index: number) => {
  if (!localModifiers.value[index]) {
    localModifiers.value[index] = createMetricModifier()
  }
  return localModifiers.value[index]
}

const addModifier = () => {
  localModifiers.value.push(createMetricModifier())
  emitUpdate()
}

const removeModifier = (index: number) => {
  localModifiers.value.splice(index, 1)
  if (localModifiers.value.length === 0) {
    emit('update:modifiersEnabled', false)
  }
  emitUpdate()
}

const updateModifierSection = (index: number, key: keyof MetricModifier, value: any) => {
  const modifier = ensureModifierAt(index)
  ;(modifier as any)[key] = value
  localModifiers.value[index] = { ...modifier }
  emitUpdate()
}

const clearModifierSection = (index: number, key: keyof MetricModifier) => {
  const modifier = ensureModifierAt(index)
  switch (key) {
    case 'measures':
      modifier.measures = []
      break
    case 'dimensions':
      modifier.dimensions = []
      break
    case 'joins':
      modifier.joins = []
      break
    case 'filters':
      modifier.filters = []
      break
    case 'order':
      modifier.order = []
      break
    case 'limit':
      delete modifier.limit
      break
  }
  localModifiers.value[index] = { ...modifier }
  emitUpdate()
}

const updateModifierLimit = (index: number, value?: number | null) => {
  const modifier = localModifiers.value[index]
  if (!modifier) return
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    delete modifier.limit
  } else {
    modifier.limit = Number(value)
  }
  localModifiers.value[index] = { ...modifier }
  emitUpdate()
}

const toggleModifierLimit = (index: number, enabled: boolean) => {
  if (enabled) {
    updateModifierLimit(index, 100)
  } else {
    clearModifierSection(index, 'limit')
  }
}
</script>
