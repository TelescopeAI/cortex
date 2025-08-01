<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <Label class="text-base font-medium">Properties</Label>
      <Button 
        type="button" 
        variant="outline" 
        size="sm" 
        @click="addNewPair"
        :disabled="isLoading"
      >
        <Plus class="h-4 w-4 mr-2" />
        Add New Pair
      </Button>
    </div>
    
    <div v-if="pairs.length === 0" class="text-center py-8 border-2 border-dashed border-muted-foreground/25 rounded-lg">
      <div class="text-muted-foreground">
        <p class="text-sm">No properties added yet</p>
        <p class="text-xs mt-1">Click "Add New Pair" to get started</p>
      </div>
    </div>
    
    <div v-else class="space-y-3">
      <div 
        v-for="(pair, index) in pairs" 
        :key="index" 
        class="flex items-center space-x-2"
      >
        <div class="flex-1">
          <Input
            :value="pair.key"
            placeholder="key_name"
            :disabled="isLoading"
            @input="(e: Event) => updatePair(index, 'key', (e.target as HTMLInputElement).value)"
          />
        </div>
        <ArrowRight class="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <div class="flex-1">
          <Input
            :value="pair.value"
            placeholder="value_name"
            :disabled="isLoading"
            @input="(e: Event) => updatePair(index, 'value', (e.target as HTMLInputElement).value)"
          />
        </div>
        <Button 
          type="button"
          variant="ghost" 
          size="sm" 
          @click="removePair(index)"
          :disabled="isLoading"
          class="text-destructive hover:text-destructive"
        >
          <Trash2 class="h-4 w-4" />
        </Button>
      </div>
    </div>
    
    <p class="text-xs text-muted-foreground">
      Optional key-value pairs for additional metadata
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Plus, ArrowRight, Trash2 } from 'lucide-vue-next'

interface KeyValuePair {
  key: string
  value: string
}

interface Props {
  modelValue?: Record<string, any> | null
  isLoading?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any> | null): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  isLoading: false
})

const emit = defineEmits<Emits>()

const pairs = ref<KeyValuePair[]>([])
const isUpdating = ref(false)

const addNewPair = () => {
  pairs.value.push({ key: '', value: '' })
  // Don't call updateJson here since the new pair is empty
}

const updatePair = (index: number, field: 'key' | 'value', value: string) => {
  if (pairs.value[index]) {
    isUpdating.value = true
    pairs.value[index][field] = value
    updateJson()
    // Reset the flag after a short delay to allow the emit to complete
    setTimeout(() => {
      isUpdating.value = false
    }, 0)
  }
}

const removePair = (index: number) => {
  isUpdating.value = true
  pairs.value.splice(index, 1)
  updateJson()
  // Reset the flag after a short delay to allow the emit to complete
  setTimeout(() => {
    isUpdating.value = false
  }, 0)
}

const updateJson = () => {
  // Build JSON object from all pairs, including empty ones for UI state
  const jsonObject: Record<string, any> = {}
  
  pairs.value.forEach(pair => {
    if (pair.key.trim() && pair.value.trim()) {
      jsonObject[pair.key.trim()] = pair.value.trim()
    }
  })
  
  // Emit null if no valid pairs, otherwise emit the JSON object
  const result = Object.keys(jsonObject).length > 0 ? jsonObject : null
  console.log('KeyValuePairs: Emitting properties:', result) // Debug log
  emit('update:modelValue', result)
}

const loadFromJson = () => {
  if (props.modelValue && typeof props.modelValue === 'object') {
    pairs.value = Object.entries(props.modelValue).map(([key, value]) => ({
      key: String(key),
      value: String(value)
    }))
  } else {
    pairs.value = []
  }
}

// Watch for external changes to modelValue, but only when not updating internally
watch(() => props.modelValue, (newValue) => {
  if (!isUpdating.value) {
    loadFromJson()
  }
}, { deep: true, immediate: true })

// Load initial data
onMounted(() => {
  loadFromJson()
})
</script> 