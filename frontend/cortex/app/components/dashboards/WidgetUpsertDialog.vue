<script setup lang="ts">
import { reactive, computed, watch, ref, onMounted } from 'vue'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '~/components/ui/dialog'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Select as UiSelect, SelectContent as UiSelectContent, SelectItem as UiSelectItem, SelectTrigger as UiSelectTrigger, SelectValue as UiSelectValue } from '~/components/ui/select'
import MetricSelector from '~/components/MetricSelector.vue'
import DataMappingEditor from './DataMappingEditor.vue'
import type { DashboardWidget } from '~/types/dashboards'
import { Button } from '~/components/ui/button'
import { NumberField, NumberFieldContent, NumberFieldDecrement, NumberFieldIncrement, NumberFieldInput } from '~/components/ui/number-field'
import { useMetrics, type SemanticMetric } from '~/composables/useMetrics'

interface Props {
  open: boolean
  mode?: 'create' | 'edit'
  initial?: Partial<DashboardWidget>
}

interface Emits {
  (e: 'update:open', val: boolean): void
  (e: 'submit', widget: Partial<DashboardWidget>): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'create',
  initial: () => ({})
})
const emit = defineEmits<Emits>()

const form = reactive({
  title: '',
  metric_id: '',
  type: 'single_value',
  columns: 3,
  rows: 1
})

const selectedMetric = ref<SemanticMetric | null>(null)
const { getMetric } = useMetrics()

type AvailableTable = { name: string; columns: { name: string; type: string }[] }
const availableTables = ref<AvailableTable[]>([])

function buildAvailableTablesFromMetric(metric: SemanticMetric | null) {
  if (!metric) { availableTables.value = []; return }
  const columns: { name: string; type: string }[] = []
  try {
    ;(metric.dimensions || []).forEach((d: any) => columns.push({ name: d.name || d, type: d.type || 'dimension' }))
    ;(metric.measures || []).forEach((m: any) => columns.push({ name: m.name || m, type: m.type || 'measure' }))
  } catch {}
  const tableName = metric.data_model_name || metric.table_name || 'Metric'
  availableTables.value = [{ name: tableName, columns }]
}

watch(() => props.initial, (val) => {
  form.title = val?.title ?? ''
  form.metric_id = (val as any)?.metric_id ?? ''
  form.type = (val as any)?.visualization?.type ?? 'single_value'
  form.columns = (val as any)?.grid_config?.columns ?? 3
  form.rows = (val as any)?.grid_config?.rows ?? 1
  if ((val as any)?.metric_id) {
    // fetch metric details for friendly label
    getMetric((val as any).metric_id as any).then(m => { if (m) { selectedMetric.value = m; buildAvailableTablesFromMetric(m) } })
  }
}, { immediate: true })

function close() {
  emit('update:open', false)
}

function onMetricSelect(metric: any) {
  form.metric_id = metric.id
  selectedMetric.value = metric
  buildAvailableTablesFromMetric(metric)
}

function submit() {
  emit('submit', {
    title: form.title,
    metric_id: form.metric_id,
    grid_config: { columns: form.columns, rows: form.rows },
    visualization: { 
      type: form.type as any,
      data_mapping: dataMapping,
      single_value_config: form.type === 'single_value' ? singleValue : undefined,
      gauge_config: form.type === 'gauge' ? gauge : undefined
    }
  } as any)
}

const selectedMetricLabel = computed(() => {
  if (!selectedMetric.value && !form.metric_id) return ''
  const name = selectedMetric.value?.name
  const model = selectedMetric.value?.data_model_name
  return name ? `${name}${model ? ' • ' + model : ''}` : ''
})

// Visualization mapping/config state
const dataMapping = reactive<any>({})

const singleValue = reactive<any>({
  number_format: 'decimal',
  prefix: '',
  suffix: '',
  show_comparison: true,
  show_trend: true,
  trend_period: 'previous_period',
  show_sparkline: false,
  show_title: true,
  show_description: false,
  compact_mode: false,
})

const gauge = reactive<any>({
  min_value: 0,
  max_value: 100,
  target_value: undefined,
  color_ranges: undefined,
  show_value: true,
  show_target: true,
  gauge_type: 'arc',
  thickness: 10,
})

// Seed from initial
watch(() => props.initial, (val) => {
  if ((val as any)?.visualization?.data_mapping) {
    Object.assign(dataMapping, (val as any).visualization.data_mapping)
  }
  if ((val as any)?.visualization?.single_value_config) {
    Object.assign(singleValue, (val as any).visualization.single_value_config)
  }
  if ((val as any)?.visualization?.gauge_config) {
    Object.assign(gauge, (val as any).visualization.gauge_config)
  }
}, { immediate: true })

function updateDataMapping(mapping: any) {
  Object.assign(dataMapping, mapping)
}
</script>

<template>
  <Dialog :open="open" @update:open="val => emit('update:open', val)">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{{ mode === 'create' ? 'Add Widget' : 'Edit Widget' }}</DialogTitle>
        <DialogDescription>
          {{ mode === 'create' ? 'Create a widget in the selected section.' : 'Update this widget.' }}
        </DialogDescription>
      </DialogHeader>
      <div class="space-y-4 py-2">
        <div class="space-y-2">
          <Label>Title</Label>
          <Input v-model="form.title" placeholder="Widget title" />
        </div>
        <div class="space-y-2">
          <Label>Metric</Label>
          <MetricSelector :button-text="selectedMetricLabel || 'Select Metric'" @select="onMetricSelect" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label>Visualization</Label>
            <UiSelect v-model="form.type">
              <UiSelectTrigger>
                <UiSelectValue placeholder="Visualization type" />
              </UiSelectTrigger>
              <UiSelectContent>
                <UiSelectItem value="single_value">Single Value</UiSelectItem>
                <UiSelectItem value="gauge">Gauge</UiSelectItem>
                <UiSelectItem value="bar_chart">Bar</UiSelectItem>
                <UiSelectItem value="line_chart">Line</UiSelectItem>
                <UiSelectItem value="area_chart">Area</UiSelectItem>
                <UiSelectItem value="pie_chart">Pie</UiSelectItem>
                <UiSelectItem value="donut_chart">Donut</UiSelectItem>
                <UiSelectItem value="scatter_plot">Scatter</UiSelectItem>
                <UiSelectItem value="box_plot">Box Plot</UiSelectItem>
                <UiSelectItem value="table">Table</UiSelectItem>
              </UiSelectContent>
            </UiSelect>
          </div>
          <div class="grid grid-cols-2 gap-4 items-end">
            <div class="space-y-2">
              <Label>Columns</Label>
              <NumberField v-model="form.columns" :min="1" :max="12" :step="1">
                <NumberFieldContent>
                  <NumberFieldDecrement />
                  <NumberFieldInput />
                  <NumberFieldIncrement />
                </NumberFieldContent>
              </NumberField>
            </div>
            <div class="space-y-2">
              <Label>Rows</Label>
              <NumberField v-model="form.rows" :min="1" :step="1">
                <NumberFieldContent>
                  <NumberFieldDecrement />
                  <NumberFieldInput />
                  <NumberFieldIncrement />
                </NumberFieldContent>
              </NumberField>
            </div>
          </div>
        </div>

        <!-- Data Mapping Configuration -->
        <DataMappingEditor
          :visualization-type="form.type"
          :mapping="dataMapping"
          :available-tables="availableTables"
          @update="updateDataMapping"
        />

        <div v-if="form.type === 'single_value'" class="space-y-3">
          <Label>Single Value Options</Label>
          <div class="grid grid-cols-3 gap-3">
            <div class="space-y-2">
              <Label class="text-xs">Prefix</Label>
              <Input v-model="singleValue.prefix" placeholder="$" />
            </div>
            <div class="space-y-2">
              <Label class="text-xs">Suffix</Label>
              <Input v-model="singleValue.suffix" placeholder="units" />
            </div>
            <div class="space-y-2">
              <Label class="text-xs">Number format</Label>
              <UiSelect v-model="singleValue.number_format">
                <UiSelectTrigger>
                  <UiSelectValue placeholder="Select format" />
                </UiSelectTrigger>
                <UiSelectContent>
                  <UiSelectItem value="integer">Integer</UiSelectItem>
                  <UiSelectItem value="decimal">Decimal</UiSelectItem>
                  <UiSelectItem value="percentage">Percentage</UiSelectItem>
                  <UiSelectItem value="currency">Currency</UiSelectItem>
                  <UiSelectItem value="abbreviated">Abbreviated</UiSelectItem>
                  <UiSelectItem value="scientific">Scientific</UiSelectItem>
                </UiSelectContent>
              </UiSelect>
            </div>
          </div>
        </div>

        <div v-if="form.type === 'gauge'" class="space-y-3">
          <Label>Gauge Options</Label>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <Label class="text-xs">Min</Label>
              <NumberField v-model="gauge.min_value" :min="0" :step="1"><NumberFieldContent><NumberFieldDecrement/><NumberFieldInput/><NumberFieldIncrement/></NumberFieldContent></NumberField>
            </div>
            <div>
              <Label class="text-xs">Max</Label>
              <NumberField v-model="gauge.max_value" :min="1" :step="1"><NumberFieldContent><NumberFieldDecrement/><NumberFieldInput/><NumberFieldIncrement/></NumberFieldContent></NumberField>
            </div>
            <div>
              <Label class="text-xs">Thickness</Label>
              <NumberField v-model="gauge.thickness" :min="1" :step="1"><NumberFieldContent><NumberFieldDecrement/><NumberFieldInput/><NumberFieldIncrement/></NumberFieldContent></NumberField>
            </div>
          </div>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" @click="close">Cancel</Button>
        <Button :disabled="!form.metric_id" @click="submit">{{ mode === 'create' ? 'Add' : 'Save' }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>


