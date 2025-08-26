<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <Button variant="outline" size="sm" :disabled="disabled">
        <Plus class="h-4 w-4 mr-2" />
        {{ buttonText }}
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent class="w-80 z-[100001]">
      <DropdownMenuSub v-for="table in availableTables" :key="table.name">
        <DropdownMenuSubTrigger>
          <Database class="h-4 w-4 mr-2" />
          {{ table.name }}
        </DropdownMenuSubTrigger>
        <DropdownMenuSubContent class="z-[100001]">
          <DropdownMenuItem
            v-for="column in table.columns"
            :key="`${table.name}.${column.name}`"
            @click="handleColumnSelect(table.name, column)"
            class="cursor-pointer"
          >
            <span class="font-mono text-sm">{{ column.name }}</span>
            <span class="text-xs text-muted-foreground ml-2">({{ column.type }})</span>
          </DropdownMenuItem>
        </DropdownMenuSubContent>
      </DropdownMenuSub>
    </DropdownMenuContent>
  </DropdownMenu>
</template>

<script setup lang="ts">
import { Database, Plus } from 'lucide-vue-next'
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

interface Column {
  name: string
  type: string
}

interface Table {
  name: string
  columns: Column[]
}

interface Props {
  availableTables: Table[]
  buttonText?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  buttonText: 'Select Column',
  disabled: false
})

const emit = defineEmits<{
  'select': [tableName: string, column: Column]
}>()

const handleColumnSelect = (tableName: string, column: Column) => {
  emit('select', tableName, column)
}
</script> 