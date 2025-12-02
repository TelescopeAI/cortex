<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import { Search, X } from 'lucide-vue-next'

type SearchMode = 'minimal' | 'compact' | 'full'

interface Props {
  modelValue: string
  placeholder?: string | string[]
  defaultMode?: SearchMode
  minimalWidth?: string
  compactWidth?: string
  fullWidth?: string
  autoFocus?: boolean
  expandOnFocus?: boolean
  expandTo?: 'compact' | 'full'  // Target mode when expanding from minimal
  collapseOnBlur?: boolean
  placeholderInterval?: number
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'mode-change', mode: SearchMode): void
  (e: 'focus'): void
  (e: 'blur'): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Search...',
  defaultMode: 'compact',
  minimalWidth: '40px',
  compactWidth: '300px',
  fullWidth: '100%',
  autoFocus: false,
  expandOnFocus: true,
  expandTo: 'compact',
  collapseOnBlur: true,
  placeholderInterval: 3000
})

const emit = defineEmits<Emits>()

// State
const currentMode = ref<SearchMode>(props.defaultMode)
const isFocused = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const currentPlaceholderIndex = ref(0)
let placeholderIntervalId: ReturnType<typeof setInterval> | null = null

// Computed
const placeholders = computed(() => {
  if (Array.isArray(props.placeholder)) {
    return props.placeholder
  }
  return [props.placeholder]
})

const currentPlaceholder = computed(() => {
  return placeholders.value[currentPlaceholderIndex.value] || placeholders.value[0]
})

const hasMultiplePlaceholders = computed(() => placeholders.value.length > 1)

const containerWidth = computed(() => {
  switch (currentMode.value) {
    case 'minimal':
      return props.minimalWidth
    case 'compact':
      return props.compactWidth
    case 'full':
      return props.fullWidth
    default:
      return props.compactWidth
  }
})

const showInput = computed(() => currentMode.value !== 'minimal')
const showClearButton = computed(() => props.modelValue && currentMode.value !== 'minimal')

// Methods
function setMode(mode: SearchMode) {
  currentMode.value = mode
  emit('mode-change', mode)
}

function expand() {
  if (currentMode.value === 'minimal') {
    setMode('compact')
  } else if (currentMode.value === 'compact') {
    setMode('full')
  }
}

function collapse() {
  if (!props.modelValue) {
    if (currentMode.value === 'full') {
      setMode('compact')
    } else if (currentMode.value === 'compact' && props.defaultMode === 'minimal') {
      setMode('minimal')
    }
  }
}

function handleFocus() {
  isFocused.value = true
  emit('focus')
  
  if (props.expandOnFocus && currentMode.value === 'minimal') {
    setMode(props.expandTo)
  }
}

function handleBlur() {
  isFocused.value = false
  emit('blur')
  
  if (props.collapseOnBlur && !props.modelValue) {
    // Delay collapse to allow click events to register
    setTimeout(() => {
      if (!isFocused.value) {
        collapse()
      }
    }, 150)
  }
}

function handleIconClick() {
  if (currentMode.value === 'minimal') {
    setMode(props.expandTo)
    // Focus input after transition
    setTimeout(() => {
      inputRef.value?.focus()
    }, 100)
  } else {
    inputRef.value?.focus()
  }
}

function handleClear() {
  emit('update:modelValue', '')
  inputRef.value?.focus()
}

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function cyclePlaceholder() {
  if (hasMultiplePlaceholders.value && !isFocused.value && !props.modelValue) {
    currentPlaceholderIndex.value = (currentPlaceholderIndex.value + 1) % placeholders.value.length
  }
}

// Lifecycle
onMounted(() => {
  if (props.autoFocus) {
    inputRef.value?.focus()
  }
  
  if (hasMultiplePlaceholders.value) {
    placeholderIntervalId = setInterval(cyclePlaceholder, props.placeholderInterval)
  }
})

onUnmounted(() => {
  if (placeholderIntervalId) {
    clearInterval(placeholderIntervalId)
  }
})

// Watch for external mode changes
watch(() => props.defaultMode, (newMode) => {
  if (!isFocused.value && !props.modelValue) {
    currentMode.value = newMode
  }
})

// Expose methods for parent components
defineExpose({
  setMode,
  expand,
  collapse,
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur()
})
</script>

<template>
  <div 
    class="expandable-search relative flex items-center"
    :style="{ width: containerWidth }"
    :class="[
      'transition-all duration-300 ease-in-out',
      { 'ring-2 ring-ring ring-offset-2 ring-offset-background rounded-md': isFocused && showInput }
    ]"
  >
    <!-- Search Icon / Button -->
    <button
      type="button"
      class="absolute left-0 z-10 flex items-center justify-center transition-all duration-200"
      :class="[
        currentMode === 'minimal' 
          ? 'w-10 h-10 rounded-md hover:bg-accent cursor-pointer' 
          : 'w-10 h-10 pointer-events-none'
      ]"
      @click="handleIconClick"
    >
      <Search 
        class="text-muted-foreground transition-colors duration-200"
        :class="[
          currentMode === 'minimal' ? 'w-5 h-5' : 'w-4 h-4',
          { 'text-foreground': isFocused }
        ]"
      />
    </button>

    <!-- Input Field -->
    <div 
      class="w-full overflow-hidden transition-all duration-300 ease-in-out"
      :class="{ 'opacity-0 pointer-events-none': !showInput, 'opacity-100': showInput }"
    >
      <Input
        ref="inputRef"
        :value="modelValue"
        :placeholder="currentPlaceholder"
        class="pl-10 pr-8 h-10 transition-all duration-200 focus-visible:ring-0 focus-visible:ring-offset-0"
        :class="[
          hasMultiplePlaceholders && !isFocused && !modelValue ? 'placeholder-transition' : ''
        ]"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      />
    </div>

    <!-- Clear Button -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 scale-75"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-75"
    >
      <button
        v-if="showClearButton"
        type="button"
        class="absolute right-2 p-1 rounded-sm hover:bg-accent transition-colors duration-150"
        @click="handleClear"
      >
        <X class="w-4 h-4 text-muted-foreground hover:text-foreground" />
      </button>
    </Transition>

    <!-- Mode Toggle (optional, for debugging or advanced use) -->
    <slot name="mode-toggle" :current-mode="currentMode" :set-mode="setMode" />
  </div>
</template>

<style scoped>
.expandable-search {
  min-height: 40px;
}

/* Smooth placeholder text transition */
.placeholder-transition::placeholder {
  transition: opacity 0.3s ease-in-out;
}

/* Ensure the container doesn't jump during transitions */
.expandable-search > * {
  flex-shrink: 0;
}
</style>

