<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center">
      <h4 class="text-sm font-medium">Aggregations</h4>
      <Button variant="outline" size="sm" @click="addAggregation">
        <Plus class="h-4 w-4 mr-2" />
        Add Aggregation
      </Button>
    </div>

    <div v-if="aggregations.length === 0" class="text-center py-8 border-2 border-dashed rounded-lg">
      <Calculator class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
      <p class="text-sm text-muted-foreground">No aggregations defined</p>
      <p class="text-xs text-muted-foreground">Aggregations will be applied to your measures</p>
    </div>

    <div v-else class="space-y-3">
      <Card 
        v-for="(aggregation, index) in aggregations"
        :key="index"
        class="p-4"
      >
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Calculator class="h-4 w-4 text-orange-500" />
              <span class="font-medium">{{ aggregation.name || 'Unnamed Aggregation' }}</span>
            </div>
            <Button variant="ghost" size="sm" @click="removeAggregation(index)">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label>Name *</Label>
              <Input v-model="aggregation.name" placeholder="aggregation_name" @update:model-value="updateAggregations" />
            </div>
            <div class="space-y-2">
              <Label>Type</Label>
              <Select v-model="aggregation.type" @update:model-value="updateAggregations">
                <SelectTrigger>
                  <SelectValue placeholder="Select aggregation type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="count">Count</SelectItem>
                  <SelectItem value="sum">Sum</SelectItem>
                  <SelectItem value="avg">Average</SelectItem>
                  <SelectItem value="min">Minimum</SelectItem>
                  <SelectItem value="max">Maximum</SelectItem>
                  <SelectItem value="stddev">Standard Deviation</SelectItem>
                  <SelectItem value="variance">Variance</SelectItem>
                  <SelectItem value="percentile">Percentile</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div class="space-y-2">
            <Label>Target Column</Label>
            <Input v-model="aggregation.target_column" placeholder="result_column_name" @update:model-value="updateAggregations" />
          </div>

          <div class="space-y-2">
            <Label>Description</Label>
            <Textarea v-model="aggregation.description" placeholder="Describe this aggregation..." rows="2" @update:model-value="updateAggregations" />
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
import { Plus, Calculator, X } from 'lucide-vue-next'

interface Aggregation {
  name: string
  description?: string
  type: string
  source_columns: string[]
  target_column: string
}

interface Props {
  aggregations?: Aggregation[]
  availableColumns?: any[]
  measures?: any[]
}

const props = withDefaults(defineProps<Props>(), {
  aggregations: () => []
})

const emit = defineEmits<{
  'update:aggregations': [value: Aggregation[]]
}>()

const aggregations = ref<Aggregation[]>([...props.aggregations])

watch(() => props.aggregations, (newAggregations) => {
  aggregations.value = [...newAggregations]
})

const updateAggregations = () => {
  emit('update:aggregations', aggregations.value)
}

const addAggregation = () => {
  const newAggregation: Aggregation = {
    name: 'new_aggregation',
    type: 'count',
    source_columns: [],
    target_column: 'result_column'
  }
  
  aggregations.value.push(newAggregation)
  updateAggregations()
}

const removeAggregation = (index: number) => {
  aggregations.value.splice(index, 1)
  updateAggregations()
}
</script> 