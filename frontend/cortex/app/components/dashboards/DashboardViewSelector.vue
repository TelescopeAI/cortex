<script setup lang="ts">
import { computed } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { ChevronDown, Eye, Star, Settings, Plus } from 'lucide-vue-next'
import type { Dashboard, DashboardView } from '~/types/dashboards'

interface Props {
  dashboard: Dashboard
  selectedViewId: string
  defaultViewId: string
}

interface Emits {
  (e: 'view-changed', viewId: string): void
  (e: 'set-default'): void
  (e: 'edit-view', view: DashboardView): void
  (e: 'add-view'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Computed
const selectedView = computed(() => {
  return props.dashboard.views.find(view => view.alias === props.selectedViewId)
})

const isDefaultView = computed(() => {
  return props.selectedViewId === props.defaultViewId
})

// Methods
function handleViewChange(value: any) {
  const viewId = String(value)
  emit('view-changed', viewId)
}

function setAsDefault() {
  emit('set-default')
}

function editView(view: DashboardView) {
  emit('edit-view', view)
}

function addView() {
  emit('add-view')
}
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- View Selector -->
    <Select :model-value="selectedViewId" @update:model-value="handleViewChange">
      <SelectTrigger class="w-64">
        <SelectValue>
          <div v-if="selectedView" class="flex items-center gap-2">
            <Star v-if="isDefaultView" class="w-3 h-3 text-yellow-500" />
            <span>{{ selectedView.title }}</span>
            <Badge v-if="isDefaultView" variant="secondary" class="text-xs">
              Default
            </Badge>
          </div>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="view in dashboard.views"
          :key="view.alias"
          :value="view.alias"
        >
          <div class="flex items-center gap-2 w-full">
            <Star 
              v-if="view.alias === defaultViewId" 
              class="w-3 h-3 text-yellow-500" 
            />
            <div class="flex-1">
              <div class="font-medium">{{ view.title }}</div>
              <div v-if="view.description" class="text-xs text-muted-foreground">
                {{ view.description }}
              </div>
            </div>
            <div class="flex items-center gap-1">
              <Badge variant="outline" class="text-xs">
                {{ view.sections.length }} section{{ view.sections.length !== 1 ? 's' : '' }}
              </Badge>
              <Badge 
                v-if="view.alias === defaultViewId" 
                variant="secondary" 
                class="text-xs"
              >
                Default
              </Badge>
            </div>
          </div>
        </SelectItem>
      </SelectContent>
    </Select>

    <!-- View Actions -->
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <Button variant="ghost" size="icon">
          <Settings class="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem @click="addView">
          <Plus class="w-4 h-4 mr-2" />
          Add View
        </DropdownMenuItem>
        <DropdownMenuItem 
          v-if="selectedView"
          @click="setAsDefault"
          :disabled="isDefaultView"
        >
          <Star class="w-4 h-4 mr-2" />
          Set as Default
        </DropdownMenuItem>
        <DropdownMenuItem 
          v-if="selectedView"
          @click="editView(selectedView)"
        >
          <Settings class="w-4 h-4 mr-2" />
          Edit View
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>