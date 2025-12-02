<template>
  <div class="space-y-6">
    <MetricDisplayBasicInformationCard
      :metric="metric"
      :parent-model="parentModel"
      :metric-status="metricStatus"
      :format-relative-time="formatRelativeTime"
      :format-absolute-date="formatAbsoluteDate"
      :get-status-badge-variant="getStatusBadgeVariant"
      @model-click="$emit('model-click')"
    />
  </div>
</template>

<script setup lang="ts">
import MetricDisplayBasicInformationCard from './BasicInformationCard.vue'

interface Props {
  metric: any
  parentModel: any
  metricStatus: string
  formatRelativeTime: (date: string | Date) => any
  formatAbsoluteDate: (date: string | Date) => any
  getStatusBadgeVariant: (status: string) => string
}

defineProps<Props>()

defineEmits<{
  'model-click': []
}>()
</script>
