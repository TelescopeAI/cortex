<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Joins</h4>
      <Button variant="outline" size="sm" @click="addJoin">
        <Plus class="h-4 w-4 mr-2" />
        Add Join
      </Button>
    </div>

    <div v-if="localJoins.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Link class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No joins defined</p>
      <p class="text-xs text-muted-foreground">Joins will be auto-generated from relationships</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(join, joinIndex) in localJoins"
        :key="joinIndex"
        class="p-4 bg-muted/50"
      >
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Link class="h-4 w-4 text-purple-500" />
              <Input 
                v-model="join.name"
                placeholder="join_name"
                class="text-base font-medium bg-transparent border-none focus-visible:ring-0 p-0 h-auto"
                @update:model-value="updateJoins"
              />
            </div>
            <Button variant="ghost" size="sm" @click="removeJoin(joinIndex)">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Left Table</Label>
              <Select v-model="join.left_table" @update:model-value="updateJoins">
                <SelectTrigger>
                  <SelectValue placeholder="Select left table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label>Right Table</Label>
              <Select v-model="join.right_table" @update:model-value="updateJoins">
                <SelectTrigger>
                  <SelectValue placeholder="Select right table" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Join Type</Label>
              <Select v-model="join.join_type" @update:model-value="updateJoins">
                <SelectTrigger>
                  <SelectValue placeholder="Select join type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="inner">Inner Join</SelectItem>
                  <SelectItem value="left">Left Join</SelectItem>
                  <SelectItem value="right">Right Join</SelectItem>
                  <SelectItem value="full">Full Join</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label>Description</Label>
              <Input v-model="join.description" placeholder="Optional description" @update:model-value="updateJoins" />
            </div>
          </div>

          <!-- Join Conditions -->
          <div class="space-y-3 pt-2">
            <div class="flex items-center justify-between">
              <Label class="text-xs uppercase text-muted-foreground">Join Conditions</Label>
              <Button v-if="!join.on" variant="outline" size="sm" @click="addCondition(joinIndex)">
                <Plus class="h-3 w-3 mr-1" />
                Add Condition
              </Button>
            </div>
            
            <div v-if="!join.on && (join.conditions || []).length === 0" class="text-center text-xs text-muted-foreground py-2">
              No conditions defined. Add a condition to link the tables.
            </div>

            <!-- SQL ON Clause -->
            <div v-if="join.on !== undefined" class="space-y-2">
              <Label>SQL ON Clause</Label>
              <Textarea 
                v-model="join.on"
                placeholder="e.g., table1.id = table2.table1_id"
                class="font-mono text-xs"
                rows="2"
                @update:model-value="updateJoins"
              />
            </div>

            <!-- Condition Builder -->
            <div v-else class="space-y-2">
              <div 
                v-for="(condition, condIndex) in join.conditions"
                :key="condIndex"
                class="flex items-center space-x-2 bg-background p-2 rounded-md"
              >
                <Select v-model="condition.left_table" @update:model-value="updateJoins">
                  <SelectTrigger class="flex-1">
                    <SelectValue placeholder="Left Table" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                  </SelectContent>
                </Select>
                <Select v-model="condition.left_column" @update:model-value="updateJoins">
                  <SelectTrigger class="flex-1">
                    <SelectValue placeholder="Left Column" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem 
                      v-for="col in getColumnsForTable(condition.left_table)"
                      :key="col.name"
                      :value="col.name"
                    >{{ col.name }}</SelectItem>
                  </SelectContent>
                </Select>

                <span class="text-muted-foreground font-bold">=</span>

                <Select v-model="condition.right_table" @update:model-value="updateJoins">
                  <SelectTrigger class="flex-1">
                    <SelectValue placeholder="Right Table" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="table in availableTables" :key="table.name" :value="table.name">{{ table.name }}</SelectItem>
                  </SelectContent>
                </Select>
                <Select v-model="condition.right_column" @update:model-value="updateJoins">
                  <SelectTrigger class="flex-1">
                    <SelectValue placeholder="Right Column" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem 
                      v-for="col in getColumnsForTable(condition.right_table)"
                      :key="col.name"
                      :value="col.name"
                    >{{ col.name }}</SelectItem>
                  </SelectContent>
                </Select>

                <Button variant="ghost" size="icon" class="w-7 h-7" @click="removeCondition(joinIndex, condIndex)">
                  <X class="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div class="flex items-center justify-end">
              <Button 
                variant="link" 
                size="sm" 
                class="text-xs"
                @click="toggleSqlMode(join)"
              >
                {{ join.on !== undefined ? 'Switch to Builder' : 'Switch to SQL Mode' }}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Plus, X, Link } from 'lucide-vue-next'

// --- Types ---
interface JoinCondition {
  left_table: string
  left_column: string
  right_table: string
  right_column: string
}

interface Join {
  name: string
  description?: string
  join_type: 'inner' | 'left' | 'right' | 'full'
  left_table: string
  right_table: string
  conditions?: JoinCondition[]
  on?: string
  alias?: string
}

interface TableSchema {
  name: string
  columns: { name: string; type: string }[]
}

interface Props {
  modelValue: Join[]
  availableTables: TableSchema[]
}

// --- Composables ---
const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  availableTables: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: Join[]]
}>()

// --- State ---
const localJoins = ref<Join[]>([])

watch(() => props.modelValue, (newValue) => {
  localJoins.value = JSON.parse(JSON.stringify(newValue || []))
}, { immediate: true, deep: true })

// --- Methods ---
const updateJoins = () => {
  emit('update:modelValue', localJoins.value)
}

const addJoin = () => {
  localJoins.value.push({
    name: `new_join_${localJoins.value.length + 1}`,
    join_type: 'left',
    left_table: '',
    right_table: '',
    conditions: [{
      left_table: '',
      left_column: '',
      right_table: '',
      right_column: '',
    }],
  })
  updateJoins()
}

const removeJoin = (index: number) => {
  localJoins.value.splice(index, 1)
  updateJoins()
}

const addCondition = (joinIndex: number) => {
  const join = localJoins.value[joinIndex]
  if (!join) return

  if (join.on !== undefined) return // Don't add conditions in SQL mode

  if (!join.conditions) {
    join.conditions = []
  }
  join.conditions.push({
    left_table: '',
    left_column: '',
    right_table: '',
    right_column: '',
  })
  updateJoins()
}

const removeCondition = (joinIndex: number, condIndex: number) => {
  const join = localJoins.value[joinIndex]
  if (join && join.conditions) {
    join.conditions.splice(condIndex, 1)
    updateJoins()
  }
}

const getColumnsForTable = (tableName: string) => {
  const table = props.availableTables.find(t => t.name === tableName)
  return table ? table.columns : []
}

const toggleSqlMode = (join: Join) => {
  if (join.on === undefined) {
    // Switching from Builder to SQL
    join.on = (join.conditions || []).map(c => `${c.left_table}.${c.left_column} = ${c.right_table}.${c.right_column}`).join(' AND ')
    join.conditions = undefined
  } else {
    // Switching from SQL to Builder
    join.on = undefined
    if (!join.conditions || join.conditions.length === 0) {
      join.conditions = [{ left_table: '', left_column: '', right_table: '', right_column: '' }]
    }
  }
  updateJoins()
}

</script>