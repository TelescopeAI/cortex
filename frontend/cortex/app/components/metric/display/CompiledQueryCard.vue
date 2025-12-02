<template>
  <Card v-if="compiledQuery || hasErrors">
    <CardHeader>
      <CardTitle class="flex items-center space-x-2">
        <Code class="h-5 w-5" />
        <span>Generated Query</span>
        <Badge v-if="hasErrors" variant="destructive" class="ml-auto">
          Invalid
        </Badge>
        <Badge v-else-if="compiledQuery" variant="success" class="ml-auto">
          Valid
        </Badge>
        <Button v-if="compiledQuery" variant="outline" size="sm" @click="$emit('copy')" class="ml-2">
          <Copy class="h-4 w-4 mr-2" />
          Copy
        </Button>
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div v-if="compiledQuery">
        <CodeHighlight lang="sql" :code="compiledQuery" />
      </div>
      
      <!-- Show warnings if there are validation warnings -->
      <div v-if="validationWarnings && validationWarnings.length > 0" class="space-y-2">
        <h4 class="font-medium text-sm text-yellow-600">Warnings:</h4>
        <div class="space-y-1">
          <div v-for="warning in validationWarnings" :key="warning" class="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
            {{ warning }}
          </div>
        </div>
      </div>
      
      <!-- Show errors if validation failed -->
      <div v-if="errors && errors.length > 0" class="space-y-2">
        <h4 class="font-medium text-sm text-red-600">Validation Errors:</h4>
        <div class="space-y-1">
          <div v-for="error in errors" :key="error" class="text-sm text-red-600 bg-red-50 p-2 rounded">
            {{ error }}
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Code, Copy } from 'lucide-vue-next'
import CodeHighlight from '~/components/CodeHighlight.vue'

interface Props {
  compiledQuery?: string
  errors?: string[]
  validationWarnings?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  errors: () => [],
  validationWarnings: () => []
})

const hasErrors = computed(() => (props.errors?.length ?? 0) > 0)

defineEmits<{
  'copy': []
}>()
</script>
