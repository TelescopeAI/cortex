<template>
  <div class="space-y-4">
    <!-- Header: Add Override + Sort -->
    <div class="flex items-center justify-between">
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="outline" size="sm">
            <Plus class="h-4 w-4 mr-2" /> Add Override
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent class="w-48">
          <!-- Add sub-menu -->
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Plus class="h-4 w-4 mr-2" /> Add
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <!-- Measure: hover to see tables → columns -->
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Measure</DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <ColumnSelector
                    :available-tables="availableTables"
                    :subs-only="true"
                    @select="(tableName: string, column: any) => addColumnBasedItem('measure', tableName, column)"
                  />
                  <DropdownMenuSeparator />
                  <DropdownMenuItem @click="addNewAddItem('measure')">
                    <Code class="h-4 w-4 mr-2" /> Custom Measure
                  </DropdownMenuItem>
                </DropdownMenuSubContent>
              </DropdownMenuSub>

              <!-- Dimension: hover to see tables → columns -->
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Dimension</DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <ColumnSelector
                    :available-tables="availableTables"
                    :subs-only="true"
                    @select="(tableName: string, column: any) => addColumnBasedItem('dimension', tableName, column)"
                  />
                </DropdownMenuSubContent>
              </DropdownMenuSub>

              <!-- Filter: hover to see tables → columns -->
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Filter</DropdownMenuSubTrigger>
                <DropdownMenuSubContent>
                  <ColumnSelector
                    :available-tables="availableTables"
                    :subs-only="true"
                    @select="(tableName: string, column: any) => addColumnBasedItem('filter', tableName, column)"
                  />
                </DropdownMenuSubContent>
              </DropdownMenuSub>

              <!-- Join: simple create (no column-based pre-fill) -->
              <DropdownMenuItem @click="addNewAddItem('join')">Join</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          <!-- Replace sub-menu -->
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <RefreshCw class="h-4 w-4 mr-2" /> Replace
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <template v-if="unreplacedMeasures.length > 0">
                <DropdownMenuLabel class="text-xs text-muted-foreground">Measures</DropdownMenuLabel>
                <DropdownMenuItem v-for="name in unreplacedMeasures" :key="'rm-' + name" @click="addReplaceItem('measure', name)">
                  {{ name }}
                </DropdownMenuItem>
                <DropdownMenuSeparator v-if="unreplacedDimensions.length > 0 || unreplacedFilters.length > 0 || unreplacedJoins.length > 0" />
              </template>
              <template v-if="unreplacedDimensions.length > 0">
                <DropdownMenuLabel class="text-xs text-muted-foreground">Dimensions</DropdownMenuLabel>
                <DropdownMenuItem v-for="name in unreplacedDimensions" :key="'rd-' + name" @click="addReplaceItem('dimension', name)">
                  {{ name }}
                </DropdownMenuItem>
                <DropdownMenuSeparator v-if="unreplacedFilters.length > 0 || unreplacedJoins.length > 0" />
              </template>
              <template v-if="unreplacedFilters.length > 0">
                <DropdownMenuLabel class="text-xs text-muted-foreground">Filters</DropdownMenuLabel>
                <DropdownMenuItem v-for="name in unreplacedFilters" :key="'rf-' + name" @click="addReplaceItem('filter', name)">
                  {{ name }}
                </DropdownMenuItem>
                <DropdownMenuSeparator v-if="unreplacedJoins.length > 0" />
              </template>
              <template v-if="unreplacedJoins.length > 0">
                <DropdownMenuLabel class="text-xs text-muted-foreground">Joins</DropdownMenuLabel>
                <DropdownMenuItem v-for="name in unreplacedJoins" :key="'rj-' + name" @click="addReplaceItem('join', name)">
                  {{ name }}
                </DropdownMenuItem>
              </template>
              <DropdownMenuItem v-if="!props.sourceMetric" disabled>
                Select a source metric first
              </DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          <!-- Exclude sub-menu -->
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Minus class="h-4 w-4 mr-2" /> Exclude
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem :disabled="hasExcludeCard('measure')" @click="addExcludeItem('measure')">Measures</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasExcludeCard('dimension')" @click="addExcludeItem('dimension')">Dimensions</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasExcludeCard('filter')" @click="addExcludeItem('filter')">Filters</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasExcludeCard('join')" @click="addExcludeItem('join')">Joins</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>

          <!-- Config sub-menu -->
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>
              <Sliders class="h-4 w-4 mr-2" /> Config
            </DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem :disabled="hasConfigCard('table_name')" @click="addConfigItem('table_name')">Table Name</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasConfigCard('limit')" @click="addConfigItem('limit')">Limit</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasConfigCard('grouped')" @click="addConfigItem('grouped')">Grouped</DropdownMenuItem>
              <DropdownMenuItem :disabled="hasConfigCard('ordered')" @click="addConfigItem('ordered')">Ordered</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
        </DropdownMenuContent>
      </DropdownMenu>

      <Button v-if="items.length > 1" variant="ghost" size="sm" @click="sortItems">
        <ArrowUpDown class="h-4 w-4 mr-2" /> Sort
      </Button>
    </div>

    <!-- Empty state -->
    <div v-if="items.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Settings class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No overrides defined</p>
      <p class="text-xs text-muted-foreground mt-1">Use "Add Override" to customize the variant</p>
    </div>

    <!-- Sortable list -->
    <div ref="parentRef" class="space-y-3">
      <div
        v-for="item in items"
        :key="item.id"
        :class="['rounded-lg border bg-card p-4', operationStyles[item.operation]]"
      >
        <!-- Card header: drag handle + badge + label + remove -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <GripVertical class="h-4 w-4 text-muted-foreground cursor-grab drag-handle" />
            <span :class="['text-[10px] font-semibold px-1.5 py-0.5 rounded', operationBadgeClasses[item.operation]]">
              {{ operationLabels[item.operation] }}
            </span>
            <span class="text-sm text-muted-foreground">{{ itemLabel(item) }}</span>
          </div>
          <Button variant="ghost" size="icon" class="h-7 w-7 hover:bg-red-50 hover:text-red-600" @click="removeItem(item.id)">
            <X class="h-3.5 w-3.5" />
          </Button>
        </div>

        <!-- Card content — delegates to sub-components -->
        <MetricVariantsBuilderOverrideAdd
          v-if="item.operation === 'add'"
          :item="item"
          :table-schema="props.tableSchema"
          @update:item="(updated) => updateItem(item.id, updated)"
        />
        <MetricVariantsBuilderOverrideReplace
          v-if="item.operation === 'replace'"
          :item="item"
          :source-metric="props.sourceMetric"
          :table-schema="props.tableSchema"
          @update:item="(updated) => updateItem(item.id, updated)"
        />
        <MetricVariantsBuilderOverrideExclude
          v-if="item.operation === 'exclude'"
          :item="item"
          :source-metric="props.sourceMetric"
          @update:item="(updated) => updateItem(item.id, updated)"
        />
        <MetricVariantsBuilderOverrideConfig
          v-if="item.operation === 'config'"
          :item="item"
          @update:item="(updated) => updateItem(item.id, updated)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, computed, nextTick } from 'vue'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import { Button } from '~/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuSub, DropdownMenuSubContent,
  DropdownMenuSubTrigger, DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Plus, Minus, RefreshCw, Sliders, Settings, GripVertical, X, ArrowUpDown, Code } from 'lucide-vue-next'
import ColumnSelector from '~/components/ColumnSelector.vue'
import { humanize, toSnakeCase } from '~/utils/stringCase'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { MetricOverrides, OverrideComponents, ExcludeComponents } from '~/types/metric_variants'
import type { OverrideItem, OperationType, ComponentType } from './types'
import { COMPONENT_TYPES, CONFIG_FIELDS } from './types'

interface Props {
  modelValue: MetricOverrides | null
  sourceMetric: SemanticMetric | null
  tableSchema: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: MetricOverrides | null]
}>()

// ── Visual styles ──────────────────────────────────────────────────────

const operationStyles: Record<OperationType, string> = {
  config:  'border-l-4 border-l-slate-400 dark:border-l-slate-500',
  exclude: 'border-l-4 border-l-red-400 dark:border-l-red-500',
  add:     'border-l-4 border-l-emerald-400 dark:border-l-emerald-500',
  replace: 'border-l-4 border-l-amber-400 dark:border-l-amber-500',
}

const operationLabels: Record<OperationType, string> = {
  config: 'CONFIG', exclude: 'EXCLUDE', add: 'ADD', replace: 'REPLACE'
}

const operationBadgeClasses: Record<OperationType, string> = {
  config:  'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  exclude: 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300',
  add:     'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
  replace: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
}

const SORT_ORDER: Record<OperationType, number> = {
  config: 0, exclude: 1, add: 2, replace: 3
}

// ── Decompose / Recompose ──────────────────────────────────────────────

function decomposeComponents(
  source: OverrideComponents | undefined,
  operation: 'add' | 'replace',
  items: OverrideItem[]
) {
  if (!source) return
  for (const ct of COMPONENT_TYPES) {
    const key = `${ct}s` as keyof OverrideComponents
    const arr = source[key] as any[] | undefined
    arr?.forEach((data: any) =>
      items.push({ id: crypto.randomUUID(), operation, componentType: ct, data: JSON.parse(JSON.stringify(data)) })
    )
  }
}

function decompose(overrides: MetricOverrides | null): OverrideItem[] {
  if (!overrides) return []
  const items: OverrideItem[] = []

  decomposeComponents(overrides.add, 'add', items)
  decomposeComponents(overrides.replace, 'replace', items)

  // Exclude — one card per component type that has exclusions
  for (const ct of COMPONENT_TYPES) {
    const key = `${ct}s` as keyof ExcludeComponents
    const names = overrides.exclude?.[key]
    if (names?.length) {
      items.push({ id: crypto.randomUUID(), operation: 'exclude', componentType: ct, excludeNames: [...names] })
    }
  }

  // Config — one card per scalar field that is set
  for (const field of CONFIG_FIELDS) {
    if (overrides[field] !== undefined) {
      items.push({ id: crypto.randomUUID(), operation: 'config', configField: field, configValue: overrides[field] })
    }
  }

  return items
}

function recomposeComponents(
  itemsList: OverrideItem[],
  operation: 'add' | 'replace'
): OverrideComponents | undefined {
  const group: any = {}
  for (const ct of COMPONENT_TYPES) {
    const key = `${ct}s` as keyof OverrideComponents
    const data = itemsList
      .filter(i => i.operation === operation && i.componentType === ct && i.data)
      .map(i => i.data)
    if (data.length) group[key] = data
  }
  return Object.keys(group).length > 0 ? group : undefined
}

function recompose(itemsList: OverrideItem[]): MetricOverrides | null {
  const result: any = {}

  const add = recomposeComponents(itemsList, 'add')
  const replace = recomposeComponents(itemsList, 'replace')
  if (add) result.add = add
  if (replace) result.replace = replace

  // Exclude
  const exclude: any = {}
  for (const ct of COMPONENT_TYPES) {
    const key = `${ct}s` as keyof ExcludeComponents
    const names = itemsList
      .filter(i => i.operation === 'exclude' && i.componentType === ct)
      .flatMap(i => i.excludeNames || [])
    if (names.length) exclude[key] = names
  }
  if (Object.keys(exclude).length) result.exclude = exclude

  // Config
  itemsList
    .filter(i => i.operation === 'config' && i.configField)
    .forEach(i => { result[i.configField!] = i.configValue })

  return Object.keys(result).length > 0 ? result : null
}

// ── Drag and drop ──────────────────────────────────────────────────────

const [parentRef, items] = useDragAndDrop<OverrideItem>(
  decompose(props.modelValue),
  {
    dragHandle: '.drag-handle',
    onSort: () => {
      emitRecomposed()
    }
  }
)

// Watch for external changes (undo/redo, prop updates from parent)
let isInternalUpdate = false

watch(() => props.modelValue, (newVal) => {
  if (isInternalUpdate) return
  items.value = decompose(newVal)
}, { deep: true })

// Auto-detect joins that should be "replace" instead of "add"
// When a join in "add" has the same name as a source join, convert to "replace"
watch([() => items.value, () => props.sourceMetric], () => {
  if (!props.sourceMetric?.joins) return

  const sourceJoinNames = new Set(props.sourceMetric.joins.map((j: any) => j.name))
  let hasChanges = false

  items.value.forEach((item, index) => {
    if (item.operation === 'add' && item.componentType === 'join' && item.data?.name) {
      // If an "add join" has the same name as a source join, convert to "replace"
      if (sourceJoinNames.has(item.data.name)) {
        items.value[index] = { ...item, operation: 'replace' }
        hasChanges = true
      }
    }
  })

  if (hasChanges) {
    emitRecomposed()
  }
}, { deep: true })

const emitRecomposed = () => {
  isInternalUpdate = true
  emit('update:modelValue', recompose(items.value))
  nextTick(() => { isInternalUpdate = false })
}

// ── Item management ────────────────────────────────────────────────────

const updateItem = (id: string, updated: Partial<OverrideItem>) => {
  const index = items.value.findIndex(i => i.id === id)
  const current = items.value[index]
  if (index === -1 || !current) return
  items.value[index] = { ...current, ...updated, id: current.id, operation: current.operation }
  emitRecomposed()
}

const removeItem = (id: string) => {
  items.value = items.value.filter(i => i.id !== id)
  emitRecomposed()
}

const sortItems = () => {
  items.value = [...items.value].sort((a, b) =>
    SORT_ORDER[a.operation] - SORT_ORDER[b.operation]
  )
  emitRecomposed()
}

const itemLabel = (item: OverrideItem): string => {
  if (item.operation === 'config' && item.configField) {
    const labels: Record<string, string> = {
      table_name: 'Table Name',
      limit: 'Limit',
      grouped: 'Grouped',
      ordered: 'Ordered'
    }
    return labels[item.configField] || item.configField
  }
  if (item.componentType) {
    const typeLabel = item.componentType.charAt(0).toUpperCase() + item.componentType.slice(1)
    if (item.operation === 'exclude') return `${typeLabel}s`
    if (item.data?.name) return `${typeLabel}: ${item.data.name}`
    return typeLabel
  }
  return ''
}

// ── Add item helpers ───────────────────────────────────────────────────

const hasExcludeCard = (ct: ComponentType) => {
  return items.value.some(i => i.operation === 'exclude' && i.componentType === ct)
}

const hasConfigCard = (field: string) => {
  return items.value.some(i => i.operation === 'config' && i.configField === field)
}

const addNewAddItem = (ct: ComponentType) => {
  const defaults: Record<ComponentType, any> = {
    measure: {
      name: '', description: null, alias: '', query: '', table: undefined,
      type: 'count', formatting: [], conditional: false, conditions: null
    },
    dimension: {
      name: '', query: '', table: undefined,
      formatting: [], combine: []
    },
    filter: {
      name: '', query: '', operator: 'equals', value: '',
      value_type: 'string', filter_type: 'where', is_active: true,
      formatting: []
    },
    join: {
      name: '', join_type: 'left', left_table: '', right_table: '',
      conditions: [{ left_table: '', left_column: '', right_table: '', right_column: '' }]
    }
  }

  items.value = [...items.value, {
    id: crypto.randomUUID(),
    operation: 'add',
    componentType: ct,
    data: defaults[ct]
  }]
  emitRecomposed()
}

// ── Column-based add (pre-filled from ColumnSelector) ─────────────────

const availableTables = computed(() => props.tableSchema?.tables || [])

const getDefaultMeasureType = (columnType: string): string => {
  const type = columnType.toLowerCase()
  if (type.includes('int') || type.includes('decimal') || type.includes('float') || type.includes('numeric')) {
    return 'sum'
  }
  return 'count'
}

const addColumnBasedItem = (ct: ComponentType, tableName: string, column: any) => {
  const name = humanize(column.name)
  const defaults: Record<ComponentType, any> = {
    measure: {
      name,
      description: null,
      alias: toSnakeCase(name),
      query: column.name,
      table: tableName,
      type: getDefaultMeasureType(column.type),
      formatting: [],
      conditional: false,
      conditions: null,
    },
    dimension: {
      name,
      query: column.name,
      table: tableName,
      formatting: [],
      combine: [],
    },
    filter: {
      name,
      query: column.name,
      table: tableName,
      operator: 'equals',
      value: '',
      value_type: 'string',
      filter_type: 'where',
      is_active: true,
      formatting: [],
    },
    join: {
      name: `${tableName} Join`,
      join_type: 'left',
      left_table: '',
      right_table: tableName,
      conditions: [{ left_table: '', left_column: '', right_table: tableName, right_column: column.name }],
    },
  }

  items.value = [...items.value, {
    id: crypto.randomUUID(),
    operation: 'add',
    componentType: ct,
    data: defaults[ct],
  }]
  emitRecomposed()
}

const addReplaceItem = (ct: ComponentType, name: string) => {
  const sourceComponents: Record<ComponentType, any[] | undefined> = {
    measure: props.sourceMetric?.measures,
    dimension: props.sourceMetric?.dimensions,
    filter: props.sourceMetric?.filters,
    join: props.sourceMetric?.joins,
  }
  const source = sourceComponents[ct]?.find((c: any) => c.name === name)
  if (!source) return

  items.value = [...items.value, {
    id: crypto.randomUUID(),
    operation: 'replace',
    componentType: ct,
    data: JSON.parse(JSON.stringify(source))
  }]
  emitRecomposed()
}

const addExcludeItem = (ct: ComponentType) => {
  if (hasExcludeCard(ct)) return
  items.value = [...items.value, {
    id: crypto.randomUUID(),
    operation: 'exclude',
    componentType: ct,
    excludeNames: []
  }]
  emitRecomposed()
}

const addConfigItem = (field: typeof CONFIG_FIELDS[number]) => {
  if (hasConfigCard(field)) return
  const defaults: Record<string, any> = {
    table_name: '',
    limit: undefined,
    grouped: true,
    ordered: true,
  }
  items.value = [...items.value, {
    id: crypto.randomUUID(),
    operation: 'config',
    configField: field,
    configValue: defaults[field]
  }]
  emitRecomposed()
}

// ── Unreplaced components (for Replace dropdown) ───────────────────────

const getUnreplaced = (ct: ComponentType) => {
  const replacedNames = items.value
    .filter(i => i.operation === 'replace' && i.componentType === ct)
    .map(i => i.data?.name)
  const sourceComponents: Record<ComponentType, any[] | undefined> = {
    measure: props.sourceMetric?.measures,
    dimension: props.sourceMetric?.dimensions,
    filter: props.sourceMetric?.filters,
    join: props.sourceMetric?.joins,
  }
  return (sourceComponents[ct] || [])
    .map((c: any) => c.name)
    .filter((n: string) => !replacedNames.includes(n))
}

const unreplacedMeasures = computed(() => getUnreplaced('measure'))
const unreplacedDimensions = computed(() => getUnreplaced('dimension'))
const unreplacedFilters = computed(() => getUnreplaced('filter'))
const unreplacedJoins = computed(() => getUnreplaced('join'))
</script>
