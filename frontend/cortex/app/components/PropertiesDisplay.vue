<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <Label class="text-base font-medium">Properties</Label>
      <Button 
        v-if="properties && Object.keys(properties).length > 0"
        type="button" 
        variant="outline" 
        size="sm" 
        @click="copyAllProperties"
        :disabled="isLoading"
      >
        <Copy class="h-4 w-4 mr-2" />
        Copy All
      </Button>
    </div>
    
    <div v-if="!properties || Object.keys(properties).length === 0" class="text-center py-6 border-2 border-dashed border-muted-foreground/25 rounded-lg">
      <div class="text-muted-foreground">
        <p class="text-sm">No properties defined</p>
        <p class="text-xs mt-1">Properties will appear here when added</p>
      </div>
    </div>
    
    <div v-else class="grid gap-2">
      <div 
        v-for="(value, key) in properties" 
        :key="key" 
        class="flex items-center justify-between p-3 border rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
      >
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2">
            <span class="font-medium text-sm text-foreground">{{ key }}</span>
            <span class="text-muted-foreground">:</span>
            <span class="text-sm text-muted-foreground truncate">{{ value }}</span>
          </div>
        </div>
        <Button 
          type="button"
          variant="ghost" 
          size="sm" 
          @click="copyProperty(key, value)"
          :disabled="isLoading"
          class="ml-2 flex-shrink-0"
        >
          <Copy class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from '~/components/ui/button'
import { Label } from '~/components/ui/label'
import { Copy } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

interface Props {
  properties?: Record<string, any> | null
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  properties: null,
  isLoading: false
})

const copyProperty = async (key: string, value: any) => {
  try {
    const textToCopy = `${key}: ${value}`
    await navigator.clipboard.writeText(textToCopy)
    toast.success('Property copied to clipboard')
  } catch (error) {
    console.error('Failed to copy property:', error)
    toast.error('Failed to copy property')
  }
}

const copyAllProperties = async () => {
  if (!props.properties) return
  
  try {
    const allProperties = Object.entries(props.properties)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n')
    
    await navigator.clipboard.writeText(allProperties)
    toast.success('All properties copied to clipboard')
  } catch (error) {
    console.error('Failed to copy all properties:', error)
    toast.error('Failed to copy properties')
  }
}
</script> 