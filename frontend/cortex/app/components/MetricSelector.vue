<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Database, ChevronDown, Sigma } from 'lucide-vue-next'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger
} from '~/components/ui/dropdown-menu'
import { Button } from '~/components/ui/button'
import { useDataModels } from '~/composables/useDataModels'
import { useMetrics, type SemanticMetric } from '~/composables/useMetrics'

interface Emits {
  (e: 'select', metric: SemanticMetric): void
}

interface Props {
  buttonText?: string
  disabled?: boolean
}

const emit = defineEmits<Emits>()
const props = withDefaults(defineProps<Props>(), {
  buttonText: 'Select Metric',
  disabled: false
})

const { models, fetchModels } = useDataModels()
const { getMetricsForModel } = useMetrics()
const modelIdToMetrics = ref<Record<string, SemanticMetric[]>>({})
const loadingModelIds = ref<Record<string, boolean>>({})

async function ensureMetrics(modelId: string) {
  if (modelIdToMetrics.value[modelId] || loadingModelIds.value[modelId]) return
  loadingModelIds.value[modelId] = true
  try {
    const metrics = await getMetricsForModel(modelId)
    modelIdToMetrics.value[modelId] = metrics
  } finally {
    loadingModelIds.value = { ...loadingModelIds.value, [modelId]: false }
  }
}

function handleSelect(metric: SemanticMetric) {
  emit('select', metric)
}

onMounted(async () => {
  await fetchModels()
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="outline" size="sm" :disabled="props.disabled">
        {{ props.buttonText }}
        <ChevronDown class="h-4 w-4 ml-2" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent class="w-80 z-[100001]">
      <DropdownMenuSub v-for="model in models" :key="model.id">
        <DropdownMenuSubTrigger @pointerenter="ensureMetrics(model.id)">
          <Database class="h-4 w-4 mr-2" />
          {{ model.name }}
        </DropdownMenuSubTrigger>
        <DropdownMenuSubContent class="z-[100001]">
          <DropdownMenuItem
            v-for="metric in modelIdToMetrics[model.id] || []"
            :key="metric.id"
            @click="handleSelect(metric)"
            class="cursor-pointer"
          >
            <Sigma class="h-4 w-4 mr-2" />
            <div class="flex flex-col">
              <span class="text-sm">{{ metric.name }}</span>
              <span class="text-xs text-muted-foreground" v-if="metric.data_model_name">{{ metric.data_model_name }}</span>
            </div>
          </DropdownMenuItem>
          <div v-if="loadingModelIds[model.id]" class="px-3 py-2 text-xs text-muted-foreground">Loading...</div>
          <div v-if="!loadingModelIds[model.id] && !(modelIdToMetrics[model.id]?.length)" class="px-3 py-2 text-xs text-muted-foreground">No metrics</div>
        </DropdownMenuSubContent>
      </DropdownMenuSub>
    </DropdownMenuContent>
  </DropdownMenu>
</template>


