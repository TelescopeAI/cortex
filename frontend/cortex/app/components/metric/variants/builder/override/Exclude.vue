<template>
  <div class="space-y-2">
    <!-- Searchable multi-select when source metric is available -->
    <template v-if="availableNames.length > 0">
      <Popover v-model:open="popoverOpen">
        <ListboxRoot v-model="selectedNames" highlight-on-hover multiple class="w-full">
          <PopoverTrigger class="w-full">
            <TagsInput v-model="selectedNames">
              <TagsInputItem v-for="name in selectedNames" :key="name" :value="name">
                <TagsInputItemText />
                <TagsInputItemDelete />
              </TagsInputItem>

              <ListboxFilter v-model="searchTerm" as-child>
                <TagsInputInput
                  class="min-w-0"
                  :placeholder="selectedNames.length > 0 ? '' : 'Search components...'"
                  @keydown.enter.prevent
                  @keydown.down="popoverOpen = true"
                />
              </ListboxFilter>

              <Button size="icon-sm" variant="ghost" class="order-last self-start ml-auto" @click="popoverOpen = !popoverOpen">
                <ChevronDown class="size-3.5" />
              </Button>
            </TagsInput>
          </PopoverTrigger>

          <PopoverAnchor>
            <PopoverContent class="p-1 w-[var(--reka-popper-anchor-width)]" @open-auto-focus.prevent>
              <ListboxContent
                class="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto empty:after:content-['No_options'] empty:p-1 empty:after:block"
                tabindex="0"
              >
                <ListboxItem
                  v-for="name in filteredNames"
                  :key="name"
                  :value="name"
                  class="data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none"
                  @select="() => { searchTerm = '' }"
                >
                  <span>{{ name }}</span>
                  <ListboxItemIndicator class="ml-auto inline-flex items-center justify-center">
                    <CheckIcon class="size-4" />
                  </ListboxItemIndicator>
                </ListboxItem>
              </ListboxContent>
            </PopoverContent>
          </PopoverAnchor>
        </ListboxRoot>
      </Popover>
    </template>

    <!-- Fallback: manual text input when no source metric -->
    <template v-else>
      <div class="flex gap-2">
        <Input
          v-model="manualInput"
          placeholder="Enter component name"
          class="h-9"
          @keyup.enter="addManualName"
        />
        <Button size="sm" @click="addManualName">Add</Button>
      </div>
      <div v-if="selectedNames.length > 0" class="flex flex-wrap gap-2 mt-2">
        <Badge
          v-for="(name, index) in selectedNames"
          :key="index"
          variant="destructive"
          class="gap-1"
        >
          {{ name }}
          <X class="h-3 w-3 cursor-pointer" @click="removeManualName(index)" />
        </Badge>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { CheckIcon, ChevronDown, X } from 'lucide-vue-next'
import { ListboxContent, ListboxFilter, ListboxItem, ListboxItemIndicator, ListboxRoot, useFilter } from 'reka-ui'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { TagsInput, TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText } from '~/components/ui/tags-input'
import type { SemanticMetric } from '~/composables/useMetrics'
import type { OverrideItem, ComponentType } from './types'

interface Props {
  item: OverrideItem
  sourceMetric: SemanticMetric | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:item': [value: Partial<OverrideItem>]
}>()

const { contains } = useFilter({ sensitivity: 'base' })

const availableNames = computed(() => {
  if (!props.sourceMetric) return []
  const componentMap: Record<ComponentType, any[] | undefined> = {
    measure: props.sourceMetric.measures,
    dimension: props.sourceMetric.dimensions,
    filter: props.sourceMetric.filters,
    join: props.sourceMetric.joins,
  }
  const components = props.item.componentType ? componentMap[props.item.componentType] : undefined
  return components?.map((c: any) => c.name) || []
})

const selectedNames = computed({
  get: () => props.item.excludeNames || [],
  set: (value: string[]) => emit('update:item', { excludeNames: value })
})

const searchTerm = ref('')
const popoverOpen = ref(false)
const manualInput = ref('')

const filteredNames = computed(() =>
  searchTerm.value === ''
    ? availableNames.value
    : availableNames.value.filter((n: string) => contains(n, searchTerm.value))
)

watch(searchTerm, (val) => {
  if (val) popoverOpen.value = true
})

const addManualName = () => {
  const name = manualInput.value.trim()
  if (!name) return
  const current = props.item.excludeNames || []
  if (!current.includes(name)) {
    emit('update:item', { excludeNames: [...current, name] })
  }
  manualInput.value = ''
}

const removeManualName = (index: number) => {
  const current = [...(props.item.excludeNames || [])]
  current.splice(index, 1)
  emit('update:item', { excludeNames: current })
}
</script>
