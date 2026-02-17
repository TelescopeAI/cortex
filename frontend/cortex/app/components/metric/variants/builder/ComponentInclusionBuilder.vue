<template>
  <div class="space-y-4">
    <Alert>
      <Info class="h-4 w-4" />
      <AlertTitle>Component Inclusion</AlertTitle>
      <AlertDescription>
        By default, all components from the source metric are inherited. Use the selections below to whitelist specific components (everything else will be excluded).
      </AlertDescription>
    </Alert>

    <!-- Enable Inclusion Whitelist -->
    <div class="flex items-center justify-between space-x-2 rounded-lg border p-4">
      <div class="space-y-0.5">
        <Label class="text-base">
          Enable Component Whitelist
        </Label>
        <p class="text-sm text-muted-foreground">
          When enabled, only selected components will be inherited
        </p>
      </div>
      <Switch
        :checked="inclusionEnabled"
        @update:model-value="handleToggle"
      />
    </div>

    <!-- Component Selection (only shown when enabled) -->
    <div v-if="includeEnabled" class="space-y-4">
      <!-- Measures -->
      <div v-if="availableMeasures.length > 0" class="space-y-2">
        <Label class="text-sm font-medium">Measures</Label>
        <Popover v-model:open="measuresPopoverOpen">
          <ListboxRoot v-model="selectedMeasures" highlight-on-hover multiple
                       class="w-full">
            <PopoverTrigger class="w-full">
              <TagsInput v-model="selectedMeasures">
                <TagsInputItem v-for="item in selectedMeasures" :key="item" :value="item">
                  <TagsInputItemText />
                  <TagsInputItemDelete />
                </TagsInputItem>

                <ListboxFilter v-model="measuresSearchTerm" as-child>
                  <TagsInputInput class="min-w-0" :placeholder="selectedMeasures.length > 0 ? '' : 'Type to search...'" @keydown.enter.prevent @keydown.down="measuresPopoverOpen = true" />
                </ListboxFilter>

                <Button size="icon-sm" variant="ghost" class="order-last self-start ml-auto" @click="measuresPopoverOpen = !measuresPopoverOpen">
                  <ChevronDown class="size-3.5" />
                </Button>
              </TagsInput>
            </PopoverTrigger>

            <PopoverAnchor>
              <PopoverContent class="p-1 w-[var(--reka-popper-anchor-width)]" @open-auto-focus.prevent>
                <ListboxContent class="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto empty:after:content-['No_options'] empty:p-1 empty:after:block" tabindex="0">
                  <ListboxItem
                    v-for="item in filteredMeasures"
                    :key="item"
                    :value="item"
                    class="data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    @select="() => { measuresSearchTerm = '' }"
                  >
                    <span>{{ item }}</span>
                    <ListboxItemIndicator class="ml-auto inline-flex items-center justify-center">
                      <CheckIcon class="size-4" />
                    </ListboxItemIndicator>
                  </ListboxItem>
                </ListboxContent>
              </PopoverContent>
            </PopoverAnchor>
          </ListboxRoot>
        </Popover>
      </div>

      <!-- Dimensions -->
      <div v-if="availableDimensions.length > 0" class="space-y-2">
        <Label class="text-sm font-medium">Dimensions</Label>
        <Popover v-model:open="dimensionsPopoverOpen">
          <ListboxRoot v-model="selectedDimensions" highlight-on-hover multiple>
            <PopoverTrigger class="w-full">
              <TagsInput v-model="selectedDimensions" class="w-full">
                <TagsInputItem v-for="item in selectedDimensions" :key="item" :value="item">
                  <TagsInputItemText />
                  <TagsInputItemDelete />
                </TagsInputItem>

                <ListboxFilter v-model="dimensionsSearchTerm" as-child>
                  <TagsInputInput class="min-w-0" :placeholder="selectedDimensions.length > 0 ? '' : 'Type to search...'" @keydown.enter.prevent @keydown.down="dimensionsPopoverOpen = true" />
                </ListboxFilter>

                <Button size="icon-sm" variant="ghost" class="order-last self-start ml-auto" @click="dimensionsPopoverOpen = !dimensionsPopoverOpen">
                  <ChevronDown class="size-3.5" />
                </Button>
              </TagsInput>
            </PopoverTrigger>

            <PopoverAnchor>
              <PopoverContent class="p-1 w-[var(--reka-popper-anchor-width)]" @open-auto-focus.prevent>
                <ListboxContent class="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto empty:after:content-['No_options'] empty:p-1 empty:after:block" tabindex="0">
                  <ListboxItem
                    v-for="item in filteredDimensions"
                    :key="item"
                    :value="item"
                    class="data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    @select="() => { dimensionsSearchTerm = '' }"
                  >
                    <span>{{ item }}</span>
                    <ListboxItemIndicator class="ml-auto inline-flex items-center justify-center">
                      <CheckIcon class="size-4" />
                    </ListboxItemIndicator>
                  </ListboxItem>
                </ListboxContent>
              </PopoverContent>
            </PopoverAnchor>
          </ListboxRoot>
        </Popover>
      </div>

      <!-- Filters -->
      <div v-if="availableFilters.length > 0" class="space-y-2">
        <Label class="text-sm font-medium">Filters</Label>
        <Popover v-model:open="filtersPopoverOpen">
          <ListboxRoot v-model="selectedFilters" highlight-on-hover multiple>
            <PopoverTrigger class="w-full">
              <TagsInput v-model="selectedFilters" class="w-full">
                <TagsInputItem v-for="item in selectedFilters" :key="item" :value="item">
                  <TagsInputItemText />
                  <TagsInputItemDelete />
                </TagsInputItem>

                <ListboxFilter v-model="filtersSearchTerm" as-child>
                  <TagsInputInput class="min-w-0" :placeholder="selectedFilters.length > 0 ? '' : 'Type to search...'" @keydown.enter.prevent @keydown.down="filtersPopoverOpen = true" />
                </ListboxFilter>

                <Button size="icon-sm" variant="ghost" class="order-last self-start ml-auto" @click="filtersPopoverOpen = !filtersPopoverOpen">
                  <ChevronDown class="size-3.5" />
                </Button>
              </TagsInput>
            </PopoverTrigger>

            <PopoverAnchor>
              <PopoverContent class="p-1 w-[var(--reka-popper-anchor-width)]" @open-auto-focus.prevent>
                <ListboxContent class="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto empty:after:content-['No_options'] empty:p-1 empty:after:block" tabindex="0">
                  <ListboxItem
                    v-for="item in filteredFilters"
                    :key="item"
                    :value="item"
                    class="data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    @select="() => { filtersSearchTerm = '' }"
                  >
                    <span>{{ item }}</span>
                    <ListboxItemIndicator class="ml-auto inline-flex items-center justify-center">
                      <CheckIcon class="size-4" />
                    </ListboxItemIndicator>
                  </ListboxItem>
                </ListboxContent>
              </PopoverContent>
            </PopoverAnchor>
          </ListboxRoot>
        </Popover>
      </div>

      <!-- Joins -->
      <div v-if="availableJoins.length > 0" class="space-y-2">
        <Label class="text-sm font-medium">Joins</Label>
        <Popover v-model:open="joinsPopoverOpen">
          <ListboxRoot v-model="selectedJoins" highlight-on-hover multiple>
            <PopoverTrigger class="w-full">
              <TagsInput v-model="selectedJoins" class="w-full">
                <TagsInputItem v-for="item in selectedJoins" :key="item" :value="item">
                  <TagsInputItemText />
                  <TagsInputItemDelete />
                </TagsInputItem>

                <ListboxFilter v-model="joinsSearchTerm" as-child>
                  <TagsInputInput class="min-w-0" :placeholder="selectedJoins.length > 0 ? '' : 'Type to search...'" @keydown.enter.prevent @keydown.down="joinsPopoverOpen = true" />
                </ListboxFilter>

                <Button size="icon-sm" variant="ghost" class="order-last self-start ml-auto" @click="joinsPopoverOpen = !joinsPopoverOpen">
                  <ChevronDown class="size-3.5" />
                </Button>
              </TagsInput>
            </PopoverTrigger>

            <PopoverAnchor>
              <PopoverContent class="p-1 w-[var(--reka-popper-anchor-width)]" @open-auto-focus.prevent>
                <ListboxContent class="max-h-[300px] scroll-py-1 overflow-x-hidden overflow-y-auto empty:after:content-['No_options'] empty:p-1 empty:after:block" tabindex="0">
                  <ListboxItem
                    v-for="item in filteredJoins"
                    :key="item"
                    :value="item"
                    class="data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-hidden select-none data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    @select="() => { joinsSearchTerm = '' }"
                  >
                    <span>{{ item }}</span>
                    <ListboxItemIndicator class="ml-auto inline-flex items-center justify-center">
                      <CheckIcon class="size-4" />
                    </ListboxItemIndicator>
                  </ListboxItem>
                </ListboxContent>
              </PopoverContent>
            </PopoverAnchor>
          </ListboxRoot>
        </Popover>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { CheckIcon, ChevronDown, Info } from 'lucide-vue-next'
import { ListboxContent, ListboxFilter, ListboxItem, ListboxItemIndicator, ListboxRoot, useFilter } from 'reka-ui'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Label } from '~/components/ui/label'
import { Switch } from '~/components/ui/switch'
import { Button } from '~/components/ui/button'
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from '~/components/ui/popover'
import { TagsInput, TagsInputInput, TagsInputItem, TagsInputItemDelete, TagsInputItemText } from '~/components/ui/tags-input'
import type { IncludedComponents } from '~/types/metric_variants'
import type { SemanticMetric } from '~/composables/useMetrics'

interface Props {
  inclusion: IncludedComponents | null
  sourceMetric: SemanticMetric | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:inclusion': [value: IncludedComponents | null]
}>()

// Local writable state for the switch
const inclusionEnabled = ref(false)

// Computed for v-if checks
const includeEnabled = computed(() => props.inclusion !== null)

// Sync local state when prop changes (from parent)
watch(() => props.inclusion, (newValue) => {
  inclusionEnabled.value = newValue !== null
}, { immediate: true })

// Toggle handler for the switch
const handleToggle = (enabled: boolean) => {
  console.log('Toggle called with:', enabled)
  console.log('Available components:', {
    measures: availableMeasures.value,
    dimensions: availableDimensions.value,
    filters: availableFilters.value,
    joins: availableJoins.value
  })

  inclusionEnabled.value = enabled

  if (enabled) {
    // Initialize with ALL components selected by default
    const inclusionData = {
      measures: availableMeasures.value.length > 0 ? [...availableMeasures.value] : undefined,
      dimensions: availableDimensions.value.length > 0 ? [...availableDimensions.value] : undefined,
      filters: availableFilters.value.length > 0 ? [...availableFilters.value] : undefined,
      joins: availableJoins.value.length > 0 ? [...availableJoins.value] : undefined
    }
    console.log('Emitting inclusion data:', inclusionData)
    emit('update:inclusion', inclusionData)
  } else {
    // Disable inclusion (inherit all)
    console.log('Emitting null (disable inclusion)')
    emit('update:inclusion', null)
  }
}

// Available components from source
const availableMeasures = computed(() => {
  return props.sourceMetric?.measures?.map(m => m.name) || []
})

const availableDimensions = computed(() => {
  return props.sourceMetric?.dimensions?.map(d => d.name) || []
})

const availableFilters = computed(() => {
  return props.sourceMetric?.filters?.map(f => f.name) || []
})

const availableJoins = computed(() => {
  return props.sourceMetric?.joins?.map(j => j.name) || []
})

// Selected components (computed with getter/setter to sync with props and emit changes)
const selectedMeasures = computed({
  get: () => props.inclusion?.measures || [],
  set: (value: string[]) => {
    emit('update:inclusion', {
      ...props.inclusion,
      measures: value.length > 0 ? value : undefined
    })
  }
})

const selectedDimensions = computed({
  get: () => props.inclusion?.dimensions || [],
  set: (value: string[]) => {
    emit('update:inclusion', {
      ...props.inclusion,
      dimensions: value.length > 0 ? value : undefined
    })
  }
})

const selectedFilters = computed({
  get: () => props.inclusion?.filters || [],
  set: (value: string[]) => {
    emit('update:inclusion', {
      ...props.inclusion,
      filters: value.length > 0 ? value : undefined
    })
  }
})

const selectedJoins = computed({
  get: () => props.inclusion?.joins || [],
  set: (value: string[]) => {
    emit('update:inclusion', {
      ...props.inclusion,
      joins: value.length > 0 ? value : undefined
    })
  }
})

// Autocomplete functionality
const { contains } = useFilter({ sensitivity: 'base' })

const measuresSearchTerm = ref('')
const dimensionsSearchTerm = ref('')
const filtersSearchTerm = ref('')
const joinsSearchTerm = ref('')

const measuresPopoverOpen = ref(false)
const dimensionsPopoverOpen = ref(false)
const filtersPopoverOpen = ref(false)
const joinsPopoverOpen = ref(false)

const filteredMeasures = computed(() =>
  measuresSearchTerm.value === ''
    ? availableMeasures.value
    : availableMeasures.value.filter(m => contains(m, measuresSearchTerm.value)),
)

const filteredDimensions = computed(() =>
  dimensionsSearchTerm.value === ''
    ? availableDimensions.value
    : availableDimensions.value.filter(d => contains(d, dimensionsSearchTerm.value)),
)

const filteredFilters = computed(() =>
  filtersSearchTerm.value === ''
    ? availableFilters.value
    : availableFilters.value.filter(f => contains(f, filtersSearchTerm.value)),
)

const filteredJoins = computed(() =>
  joinsSearchTerm.value === ''
    ? availableJoins.value
    : availableJoins.value.filter(j => contains(j, joinsSearchTerm.value)),
)

// Auto-open popovers when user starts typing
watch(measuresSearchTerm, (val) => { if (val) measuresPopoverOpen.value = true })
watch(dimensionsSearchTerm, (val) => { if (val) dimensionsPopoverOpen.value = true })
watch(filtersSearchTerm, (val) => { if (val) filtersPopoverOpen.value = true })
watch(joinsSearchTerm, (val) => { if (val) joinsPopoverOpen.value = true })
</script>
