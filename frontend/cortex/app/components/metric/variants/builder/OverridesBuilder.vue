<template>
  <div class="space-y-4">
    <Alert>
      <Settings class="h-4 w-4" />
      <AlertTitle>Component Overrides</AlertTitle>
      <AlertDescription>
        Add new components, replace existing ones, or exclude components from the source metric.
      </AlertDescription>
    </Alert>

    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="grid w-full grid-cols-4">
        <TabsTrigger value="add">
          <Plus class="h-4 w-4 mr-2" />
          Add
        </TabsTrigger>
        <TabsTrigger value="replace">
          <RefreshCw class="h-4 w-4 mr-2" />
          Replace
        </TabsTrigger>
        <TabsTrigger value="exclude">
          <Minus class="h-4 w-4 mr-2" />
          Exclude
        </TabsTrigger>
        <TabsTrigger value="scalar">
          <Sliders class="h-4 w-4 mr-2" />
          Scalar
        </TabsTrigger>
      </TabsList>

      <!-- Add Tab -->
      <TabsContent value="add" class="space-y-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle class="text-sm">Add Components</CardTitle>
            <CardDescription>
              Add new components that don't exist in the source metric
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="text-center py-8 text-muted-foreground">
              <Plus class="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p class="text-sm">Component addition coming soon</p>
              <p class="text-xs mt-1">
                You'll be able to add new measures, dimensions, filters, and joins
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Replace Tab -->
      <TabsContent value="replace" class="space-y-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle class="text-sm">Replace Components</CardTitle>
            <CardDescription>
              Replace existing components from the source metric
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="text-center py-8 text-muted-foreground">
              <RefreshCw class="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p class="text-sm">Component replacement coming soon</p>
              <p class="text-xs mt-1">
                You'll be able to modify existing measures, dimensions, filters, and joins
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Exclude Tab -->
      <TabsContent value="exclude" class="space-y-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle class="text-sm">Exclude Components</CardTitle>
            <CardDescription>
              Remove components from the source metric by name
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Exclude Measures -->
            <div class="space-y-2">
              <Label>Exclude Measures</Label>
              <div class="flex gap-2">
                <Input
                  v-model="excludeMeasureInput"
                  placeholder="Enter measure name"
                  @keyup.enter="addExcludeMeasure"
                />
                <Button size="sm" @click="addExcludeMeasure">
                  Add
                </Button>
              </div>
              <div v-if="excludedMeasures.length > 0" class="flex flex-wrap gap-2 mt-2">
                <Badge
                  v-for="(measure, index) in excludedMeasures"
                  :key="index"
                  variant="destructive"
                  class="gap-1"
                >
                  {{ measure }}
                  <X class="h-3 w-3 cursor-pointer" @click="removeExcludeMeasure(index)" />
                </Badge>
              </div>
            </div>

            <!-- Exclude Dimensions -->
            <div class="space-y-2">
              <Label>Exclude Dimensions</Label>
              <div class="flex gap-2">
                <Input
                  v-model="excludeDimensionInput"
                  placeholder="Enter dimension name"
                  @keyup.enter="addExcludeDimension"
                />
                <Button size="sm" @click="addExcludeDimension">
                  Add
                </Button>
              </div>
              <div v-if="excludedDimensions.length > 0" class="flex flex-wrap gap-2 mt-2">
                <Badge
                  v-for="(dimension, index) in excludedDimensions"
                  :key="index"
                  variant="destructive"
                  class="gap-1"
                >
                  {{ dimension }}
                  <X class="h-3 w-3 cursor-pointer" @click="removeExcludeDimension(index)" />
                </Badge>
              </div>
            </div>

            <!-- Exclude Filters -->
            <div class="space-y-2">
              <Label>Exclude Filters</Label>
              <div class="flex gap-2">
                <Input
                  v-model="excludeFilterInput"
                  placeholder="Enter filter name"
                  @keyup.enter="addExcludeFilter"
                />
                <Button size="sm" @click="addExcludeFilter">
                  Add
                </Button>
              </div>
              <div v-if="excludedFilters.length > 0" class="flex flex-wrap gap-2 mt-2">
                <Badge
                  v-for="(filter, index) in excludedFilters"
                  :key="index"
                  variant="destructive"
                  class="gap-1"
                >
                  {{ filter }}
                  <X class="h-3 w-3 cursor-pointer" @click="removeExcludeFilter(index)" />
                </Badge>
              </div>
            </div>

            <!-- Exclude Joins -->
            <div class="space-y-2">
              <Label>Exclude Joins</Label>
              <div class="flex gap-2">
                <Input
                  v-model="excludeJoinInput"
                  placeholder="Enter join name"
                  @keyup.enter="addExcludeJoin"
                />
                <Button size="sm" @click="addExcludeJoin">
                  Add
                </Button>
              </div>
              <div v-if="excludedJoins.length > 0" class="flex flex-wrap gap-2 mt-2">
                <Badge
                  v-for="(join, index) in excludedJoins"
                  :key="index"
                  variant="destructive"
                  class="gap-1"
                >
                  {{ join }}
                  <X class="h-3 w-3 cursor-pointer" @click="removeExcludeJoin(index)" />
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Scalar Tab -->
      <TabsContent value="scalar" class="space-y-4 mt-4">
        <Card>
          <CardHeader>
            <CardTitle class="text-sm">Scalar Overrides</CardTitle>
            <CardDescription>
              Override scalar properties like table name, limit, grouping, and ordering
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Table Name -->
            <div class="space-y-2">
              <Label for="table-name">Table Name</Label>
              <Input
                id="table-name"
                :model-value="modelValue?.table_name"
                @update:model-value="updateScalar('table_name', $event)"
                placeholder="Override table name"
              />
            </div>

            <!-- Limit -->
            <div class="space-y-2">
              <Label for="limit">Limit</Label>
              <Input
                id="limit"
                type="number"
                :model-value="modelValue?.limit"
                @update:model-value="updateScalar('limit', $event ? parseInt($event) : undefined)"
                placeholder="Override row limit"
              />
            </div>

            <!-- Grouped -->
            <div class="flex items-center justify-between space-x-2 rounded-lg border p-4">
              <div class="space-y-0.5">
                <Label class="text-base">Grouped</Label>
                <p class="text-sm text-muted-foreground">
                  Enable GROUP BY in query
                </p>
              </div>
              <Switch
                :checked="modelValue?.grouped"
                @update:checked="updateScalar('grouped', $event)"
              />
            </div>

            <!-- Ordered -->
            <div class="flex items-center justify-between space-x-2 rounded-lg border p-4">
              <div class="space-y-0.5">
                <Label class="text-base">Ordered</Label>
                <p class="text-sm text-muted-foreground">
                  Enable ORDER BY in query
                </p>
              </div>
              <Switch
                :checked="modelValue?.ordered"
                @update:checked="updateScalar('ordered', $event)"
              />
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Switch } from '~/components/ui/switch'
import { Settings, Plus, RefreshCw, Minus, Sliders, X } from 'lucide-vue-next'
import type { MetricOverrides } from '~/types/metric_variants'

interface Props {
  modelValue: MetricOverrides | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: MetricOverrides | null]
}>()

const activeTab = ref('add')

// Exclude inputs
const excludeMeasureInput = ref('')
const excludeDimensionInput = ref('')
const excludeFilterInput = ref('')
const excludeJoinInput = ref('')

// Excluded items
const excludedMeasures = computed(() => props.modelValue?.exclude?.measures || [])
const excludedDimensions = computed(() => props.modelValue?.exclude?.dimensions || [])
const excludedFilters = computed(() => props.modelValue?.exclude?.filters || [])
const excludedJoins = computed(() => props.modelValue?.exclude?.joins || [])

// Exclude handlers
const addExcludeMeasure = () => {
  if (!excludeMeasureInput.value.trim()) return

  const current = props.modelValue?.exclude?.measures || []
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      measures: [...current, excludeMeasureInput.value.trim()]
    }
  })
  excludeMeasureInput.value = ''
}

const removeExcludeMeasure = (index: number) => {
  const current = [...excludedMeasures.value]
  current.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      measures: current.length > 0 ? current : undefined
    }
  })
}

const addExcludeDimension = () => {
  if (!excludeDimensionInput.value.trim()) return

  const current = props.modelValue?.exclude?.dimensions || []
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      dimensions: [...current, excludeDimensionInput.value.trim()]
    }
  })
  excludeDimensionInput.value = ''
}

const removeExcludeDimension = (index: number) => {
  const current = [...excludedDimensions.value]
  current.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      dimensions: current.length > 0 ? current : undefined
    }
  })
}

const addExcludeFilter = () => {
  if (!excludeFilterInput.value.trim()) return

  const current = props.modelValue?.exclude?.filters || []
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      filters: [...current, excludeFilterInput.value.trim()]
    }
  })
  excludeFilterInput.value = ''
}

const removeExcludeFilter = (index: number) => {
  const current = [...excludedFilters.value]
  current.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      filters: current.length > 0 ? current : undefined
    }
  })
}

const addExcludeJoin = () => {
  if (!excludeJoinInput.value.trim()) return

  const current = props.modelValue?.exclude?.joins || []
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      joins: [...current, excludeJoinInput.value.trim()]
    }
  })
  excludeJoinInput.value = ''
}

const removeExcludeJoin = (index: number) => {
  const current = [...excludedJoins.value]
  current.splice(index, 1)
  emit('update:modelValue', {
    ...props.modelValue,
    exclude: {
      ...props.modelValue?.exclude,
      joins: current.length > 0 ? current : undefined
    }
  })
}

// Scalar override handler
const updateScalar = (field: string, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}
</script>
