<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Separator } from '~/components/ui/separator'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '~/components/ui/collapsible'
import {
  AlertCircle,
  Stethoscope,
  Loader2,
  Lightbulb,
  ChevronDown,
  Wrench,
  CheckCircle
} from 'lucide-vue-next'
import type { DiagnoseResponse, Suggestion } from '~/types/doctor'

interface Props {
  /** Error messages to display */
  errors: string[]
  /**
   * Callback that calls the appropriate diagnose API.
   * Parent provides this so the component stays entity-agnostic.
   * If not provided, the Diagnose button is hidden.
   */
  onDiagnose?: () => Promise<DiagnoseResponse>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'apply-fix': [fixed: Record<string, any>]
}>()

const diagnosing = ref(false)
const diagnosisResult = ref<DiagnoseResponse | null>(null)
const diagnosisError = ref<string | null>(null)
const diagnosisExpanded = ref(true)

const handleDiagnose = async () => {
  if (!props.onDiagnose) return

  diagnosing.value = true
  diagnosisError.value = null
  diagnosisResult.value = null

  try {
    diagnosisResult.value = await props.onDiagnose()
  } catch (err) {
    diagnosisError.value = err instanceof Error ? err.message : 'Diagnosis failed'
  } finally {
    diagnosing.value = false
  }
}

const handleApplyFix = (suggestion: Suggestion) => {
  emit('apply-fix', suggestion.fixed)
}
</script>

<template>
  <div class="space-y-3">
    <!-- Error Messages -->
    <div class="space-y-2">
      <h4 class="font-medium text-sm text-red-600 dark:text-red-400 flex items-center gap-1.5">
        <AlertCircle class="h-4 w-4" />
        Execution Errors
      </h4>
      <div class="space-y-1">
        <div
          v-for="error in errors"
          :key="error"
          class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950 p-2 rounded"
        >
          {{ error }}
        </div>
      </div>
    </div>

    <!-- Diagnose Button -->
    <div v-if="!diagnosisResult && onDiagnose" class="pt-1">
      <Button
        variant="outline"
        size="sm"
        :disabled="diagnosing"
        @click="handleDiagnose"
      >
        <Loader2 v-if="diagnosing" class="h-4 w-4 mr-2 animate-spin" />
        <Stethoscope v-else class="h-4 w-4 mr-2" />
        {{ diagnosing ? 'Diagnosing...' : 'Diagnose' }}
      </Button>
    </div>

    <!-- Diagnosis Error -->
    <div
      v-if="diagnosisError"
      class="text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 p-2 rounded"
    >
      Failed to run diagnosis: {{ diagnosisError }}
    </div>

    <!-- Diagnosis Results (unhealthy) -->
    <Collapsible
      v-if="diagnosisResult && !diagnosisResult.healthy && diagnosisResult.diagnosis"
      v-model:open="diagnosisExpanded"
    >
      <div class="border rounded-lg">
        <CollapsibleTrigger class="flex w-full items-center justify-between p-3 hover:bg-muted/50">
          <div class="flex items-center gap-2">
            <Stethoscope class="h-4 w-4 text-amber-600 dark:text-amber-400" />
            <span class="text-sm font-medium">Diagnosis</span>
            <Badge v-if="diagnosisResult.diagnosis.suggestions.length > 0" variant="secondary" class="text-xs">
              {{ diagnosisResult.diagnosis.suggestions.length }} suggestion{{
                diagnosisResult.diagnosis.suggestions.length !== 1 ? 's' : ''
              }}
            </Badge>
          </div>
          <ChevronDown
            class="h-4 w-4 text-muted-foreground transition-transform"
            :class="{ 'rotate-180': diagnosisExpanded }"
          />
        </CollapsibleTrigger>

        <CollapsibleContent>
          <Separator />
          <div class="p-3 space-y-3">
            <!-- Explanation -->
            <div class="text-sm text-muted-foreground bg-muted/50 p-2.5 rounded whitespace-pre-line">
              {{ diagnosisResult.diagnosis.explanation }}
            </div>

            <!-- Suggestions -->
            <div
              v-if="diagnosisResult.diagnosis.suggestions.length > 0"
              class="space-y-2"
            >
              <h5 class="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Suggestions
              </h5>
              <div
                v-for="(suggestion, index) in diagnosisResult.diagnosis.suggestions"
                :key="index"
                class="border rounded-md p-3 space-y-2"
              >
                <div class="flex items-start gap-2">
                  <Lightbulb class="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                  <p class="text-sm">{{ suggestion.description }}</p>
                </div>
                <div class="flex justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    @click="handleApplyFix(suggestion)"
                  >
                    <Wrench class="h-3.5 w-3.5 mr-1.5" />
                    Apply Fix
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>

    <!-- Healthy result -->
    <div
      v-if="diagnosisResult && diagnosisResult.healthy"
      class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950 p-2 rounded"
    >
      <CheckCircle class="h-4 w-4" />
      No configuration issues detected. The error may be transient.
    </div>
  </div>
</template>
