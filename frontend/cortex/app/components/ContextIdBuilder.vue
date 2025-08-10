<template>
  <div class="space-y-4">
    <!-- Include Context Toggle -->
    <div class="flex items-center space-x-2">
      <Switch
        id="include-context"
        v-model="includeContext"
      />
      <Label for="include-context">Include Context</Label>
    </div>

    <!-- Context Selection (only shown when includeContext is true) -->
    <div v-if="includeContext" class="space-y-4">
      <!-- Consumer Selection -->
      <div class="space-y-2">
        <Label for="consumer">Consumer (Optional)</Label>
        <Select v-model="selectedConsumerId" :disabled="isLoading">
          <SelectTrigger>
            <SelectValue placeholder="Select a consumer" />
          </SelectTrigger>
          <SelectContent>
            <div class="p-2">
              <Input
                v-model="consumerSearchQuery"
                placeholder="Search consumers..."
                class="mb-2"
              />
            </div>
            <!-- None option -->
            <SelectItem :value="null">
              <div class="flex flex-col">
                <span class="font-medium text-muted-foreground">None</span>
              </div>
            </SelectItem>
            <SelectItem 
              v-for="consumer in filteredConsumers" 
              :key="consumer.id" 
              :value="consumer.id"
            >
              <div class="flex flex-col">
                <span class="font-medium">{{ consumer.first_name }} {{ consumer.last_name }} ({{ consumer.email }})</span>
              </div>
            </SelectItem>
            <div v-if="filteredConsumers.length === 0" class="p-2 text-sm text-muted-foreground">
              No consumers found
            </div>
          </SelectContent>
        </Select>
      </div>

      <!-- Group Selection -->
      <div class="space-y-2">
        <Label for="group">Consumer Group (Optional)</Label>
        <Select v-model="selectedGroupId" :disabled="isLoading">
          <SelectTrigger>
            <SelectValue placeholder="Select a group" />
          </SelectTrigger>
          <SelectContent>
            <div class="p-2">
              <Input
                v-model="groupSearchQuery"
                placeholder="Search groups..."
                class="mb-2"
              />
            </div>
            <!-- None option -->
            <SelectItem :value="null">
              <div class="flex flex-col">
                <span class="font-medium text-muted-foreground">None</span>
              </div>
            </SelectItem>
            <SelectItem 
              v-for="group in filteredGroups" 
              :key="group.id" 
              :value="group.id"
            >
              <div class="flex flex-col">
                <span class="font-medium">{{ group.name }} ({{ group.description || 'No description' }})</span>
              </div>
            </SelectItem>
            <div v-if="filteredGroups.length === 0" class="p-2 text-sm text-muted-foreground">
              No groups found
            </div>
          </SelectContent>
        </Select>
      </div>



      <!-- Validation Message -->
      <div v-if="includeContext && !selectedConsumerId && !selectedGroupId" class="text-sm text-amber-600 bg-amber-50 p-2 rounded">
        Please select at least one consumer or group to generate a context ID.
      </div>
      
      <!-- Context ID Display (show when selections are made, regardless of toggle state) -->
      <div v-if="shouldShowContextId" class="space-y-2">

        <Label>Generated Context ID</Label>
        <div class="flex items-center space-x-2">
          <Input
            v-model="generatedContextId"
            readonly
            class="font-mono text-sm"
          />
          <Button
            variant="outline"
            size="sm"
            @click="copyContextId"
          >
            <Copy class="h-4 w-4" />
          </Button>
        </div>
        <div class="text-xs text-muted-foreground">
          {{ getContextDescription() }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useConsumers } from '~/composables/useConsumers'
import { useConsumerGroups } from '~/composables/useConsumerGroups'
import { toast } from 'vue-sonner'
import { Switch } from '~/components/ui/switch'
import { Label } from '~/components/ui/label'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Copy } from 'lucide-vue-next'

interface Props {
  modelValue?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { consumers, fetchConsumers } = useConsumers()
const { consumerGroups, fetchConsumerGroups } = useConsumerGroups()

const isLoading = ref(false)
const includeContext = ref(false)
const selectedConsumerId = ref<string | null>(null)
const selectedGroupId = ref<string | null>(null)
const consumerSearchQuery = ref('')
const groupSearchQuery = ref('')

// Computed property for display condition
const shouldShowContextId = computed(() => {
  return selectedConsumerId.value || selectedGroupId.value
})

// Filtered lists for search
const filteredConsumers = computed(() => {
  if (!consumers.value) return []
  
  return consumers.value.filter(consumer => {
    const searchTerm = consumerSearchQuery.value.toLowerCase()
    return consumer.first_name.toLowerCase().includes(searchTerm) ||
           consumer.last_name.toLowerCase().includes(searchTerm) ||
           consumer.email.toLowerCase().includes(searchTerm)
  })
})

const filteredGroups = computed(() => {
  if (!consumerGroups.value) return []
  
  return consumerGroups.value.filter(group => {
    const searchTerm = groupSearchQuery.value.toLowerCase()
    return group.name.toLowerCase().includes(searchTerm) ||
           (group.description && group.description.toLowerCase().includes(searchTerm))
  })
})

// Generate context ID based on selections
const generatedContextId = computed(() => {
  if (selectedConsumerId.value && selectedGroupId.value) {
    return `CCG_${selectedConsumerId.value}_${selectedGroupId.value}`
  } else if (selectedConsumerId.value) {
    return `C_${selectedConsumerId.value}`
  } else if (selectedGroupId.value) {
    return `CG_${selectedGroupId.value}`
  }
  
  return ''
})

// Get human-readable description of the context
const getContextDescription = () => {
  if (!generatedContextId.value) return ''
  
  if (selectedConsumerId.value && selectedGroupId.value) {
    const consumer = consumers.value?.find(c => c.id === selectedConsumerId.value)
    const group = consumerGroups.value?.find(g => g.id === selectedGroupId.value)
    return `Consumer "${consumer?.first_name} ${consumer?.last_name}" in group "${group?.name}"`
  } else if (selectedConsumerId.value) {
    const consumer = consumers.value?.find(c => c.id === selectedConsumerId.value)
    return `Consumer "${consumer?.first_name} ${consumer?.last_name}"`
  } else if (selectedGroupId.value) {
    const group = consumerGroups.value?.find(g => g.id === selectedGroupId.value)
    return `Consumer group "${group?.name}"`
  }
  
  return ''
}

// Copy context ID to clipboard
const copyContextId = async () => {
  try {
    await navigator.clipboard.writeText(generatedContextId.value)
    toast.success('Context ID copied to clipboard')
  } catch (error) {
    toast.error('Failed to copy context ID')
  }
}

// Load data on mount
onMounted(async () => {
  isLoading.value = true
  try {
    await Promise.all([
      fetchConsumers(),
      fetchConsumerGroups()
    ])
  } catch (error) {
    console.error('Failed to load consumers/groups:', error)
    toast.error('Failed to load consumers and groups')
  } finally {
    isLoading.value = false
  }
})

// Watch for changes and emit updates only when context is enabled
watch([generatedContextId, includeContext], ([contextId, isEnabled]) => {
  emit('update:modelValue', isEnabled ? contextId : '')
})

// Initialize from props (only on mount to avoid interference)
onMounted(() => {
  if (props.modelValue) {
    includeContext.value = true
    // Parse existing context ID if provided
    const parts = props.modelValue.split('_')
    if (parts.length === 2) {
      if (parts[0] === 'C') {
        selectedConsumerId.value = parts[1] || null
        selectedGroupId.value = null
      } else if (parts[0] === 'CG') {
        selectedGroupId.value = parts[1] || null
        selectedConsumerId.value = null
      }
    } else if (parts.length === 3 && parts[0] === 'CCG') {
      selectedConsumerId.value = parts[1] || null
      selectedGroupId.value = parts[2] || null
    }
  }
})
</script> 