<template>
  <Card v-if="query">
    <CardHeader>
      <CardTitle>Original SQL Query</CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <CodeHighlight lang="sql" :code="query" />
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import CodeHighlight from '~/components/CodeHighlight.vue'

interface Props {
  query: string
}

defineProps<Props>()
</script>
