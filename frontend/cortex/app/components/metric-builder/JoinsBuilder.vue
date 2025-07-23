<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Joins</h4>
      <Button variant="outline" size="sm" @click="addJoin">
        <Plus class="h-4 w-4 mr-2" />
        Add Join
      </Button>
    </div>

    <div v-if="joins.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Link class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No joins defined</p>
      <p class="text-xs text-muted-foreground">Joins will be auto-generated from relationships</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(join, index) in joins"
        :key="index"
        class="p-4"
      >
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Link class="h-4 w-4 text-purple-500" />
              <span class="font-medium">{{ join.name || 'Unnamed Join' }}</span>
            </div>
            <Button variant="ghost" size="sm" @click="removeJoin(index)">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Name *</Label>
              <Input v-model="join.name" placeholder="join_name" @update:model-value="updateJoins" />
            </div>
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
          </div>

          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea v-model="join.description" placeholder="Describe this join..." rows="2" @update:model-value="updateJoins" />
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Card } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Plus, Link, X } from 'lucide-vue-next'

interface Join {
  name: string
  description?: string
  join_type: string
  left_table: string
  right_table: string
  conditions: any[]
}

interface Props {
  joins?: Join[]
  availableTables?: any[]
  tableSchema?: any
}

const props = withDefaults(defineProps<Props>(), {
  joins: () => []
})

const emit = defineEmits<{
  'update:joins': [value: Join[]]
}>()

const joins = ref<Join[]>([...props.joins])

watch(() => props.joins, (newJoins) => {
  joins.value = [...newJoins]
})

const updateJoins = () => {
  emit('update:joins', joins.value)
}

const addJoin = () => {
  const newJoin: Join = {
    name: 'new_join',
    join_type: 'inner',
    left_table: '',
    right_table: '',
    conditions: []
  }
  
  joins.value.push(newJoin)
  updateJoins()
}

const removeJoin = (index: number) => {
  joins.value.splice(index, 1)
  updateJoins()
}
</script> 