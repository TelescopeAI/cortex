<template>
  <div class="space-y-6">
    <MetricDisplayCompiledQueryCard
      :compiled-query="compiledQuery"
      :validation-result="validationResult"
      @copy="$emit('copy-query')"
    />

    <MetricDisplayOriginalQueryCard
      v-if="originalQuery"
      :query="originalQuery"
    />
  </div>
</template>

<script setup lang="ts">
import MetricDisplayCompiledQueryCard from './CompiledQueryCard.vue'
import MetricDisplayOriginalQueryCard from './OriginalQueryCard.vue'

interface Props {
  validationResult: any
  compiledQuery: string
  originalQuery: string
}

defineProps<Props>()

defineEmits<{
  'copy-query': []
}>()
</script>
