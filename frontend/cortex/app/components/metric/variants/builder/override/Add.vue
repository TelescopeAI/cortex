<template>
  <div>
    <!-- Measure -->
    <MetricBuilderMeasuresBuilder
      v-if="item.componentType === 'measure'"
      :measures="[item.data]"
      :table-schema="props.tableSchema"
      :show-header="false"
      :show-empty-state="false"
      @update:measures="(v) => { if (v && v.length > 0 && v[0]) emit('update:item', { data: v[0] }) }"
    />

    <!-- Dimension -->
    <MetricBuilderDimensionsBuilder
      v-if="item.componentType === 'dimension'"
      :dimensions="[item.data]"
      :table-schema="props.tableSchema"
      :show-header="false"
      :show-empty-state="false"
      @update:dimensions="(v) => { if (v && v.length > 0 && v[0]) emit('update:item', { data: v[0] }) }"
    />

    <!-- Filter -->
    <MetricBuilderFiltersBuilder
      v-if="item.componentType === 'filter'"
      :filters="[item.data]"
      :table-schema="props.tableSchema"
      :show-header="false"
      :show-empty-state="false"
      @update:filters="(v) => { if (v && v.length > 0 && v[0]) emit('update:item', { data: v[0] }) }"
    />

    <!-- Join -->
    <MetricBuilderJoinsBuilder
      v-if="item.componentType === 'join'"
      :model-value="[item.data]"
      :available-tables="availableTables"
      :show-header="false"
      :show-empty-state="false"
      :show-auto-generated="true"
      @update:model-value="(v) => { if (v && v.length > 0 && v[0]) emit('update:item', { data: v[0] }) }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { OverrideItem } from './types'

interface Props {
  item: OverrideItem
  tableSchema: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:item': [value: Partial<OverrideItem>]
}>()

const availableTables = computed(() => props.tableSchema?.tables || [])
</script>
