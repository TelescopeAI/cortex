<template>
  <div class="space-y-6 p-6">
    <!-- Basic Information -->
    <Card>
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Database class="h-5 w-5" />
          <span>Basic Information</span>
        </CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <Label class="text-sm font-medium text-muted-foreground">Data Source</Label>
            <p class="text-sm">{{ metric.data_source_id || 'Not specified' }}</p>
          </div>
          <div class="space-y-2">
            <Label class="text-sm font-medium text-muted-foreground">Source Table</Label>
            <p class="text-sm">{{ metric.table_name || 'Not specified' }}</p>
          </div>
          <div class="space-y-2">
            <Label class="text-sm font-medium text-muted-foreground">Custom Query</Label>
            <p class="text-sm font-mono text-xs bg-muted p-2 rounded">
              {{ metric.query || 'Not specified' }}
            </p>
          </div>
          <div class="space-y-2">
            <Label class="text-sm font-medium text-muted-foreground">Default Limit</Label>
            <p class="text-sm">{{ metric.limit || 'No limit' }}</p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Measures -->
    <Card v-if="metric.measures && metric.measures.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Target class="h-5 w-5" />
          <span>Measures ({{ metric.measures.length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(measure, index) in metric.measures"
            :key="index"
            class="flex items-center justify-between p-3 border rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <Target class="h-4 w-4 text-blue-500" />
              <div>
                <p class="font-medium text-sm">{{ measure.name }}</p>
                <p class="text-xs text-muted-foreground">{{ measure.description || 'No description' }}</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <Badge variant="outline">{{ measure.type }}</Badge>
              <Badge v-if="measure.table" variant="secondary">{{ measure.table }}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Dimensions -->
    <Card v-if="metric.dimensions && metric.dimensions.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Grid class="h-5 w-5" />
          <span>Dimensions ({{ metric.dimensions.length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(dimension, index) in metric.dimensions"
            :key="index"
            class="flex items-center justify-between p-3 border rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <Grid class="h-4 w-4 text-green-500" />
              <div>
                <p class="font-medium text-sm">{{ dimension.name }}</p>
                <p class="text-xs text-muted-foreground">{{ dimension.description || 'No description' }}</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <Badge variant="outline">{{ dimension.query }}</Badge>
              <Badge v-if="dimension.table" variant="secondary">{{ dimension.table }}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Joins -->
    <Card v-if="metric.joins && metric.joins.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Link class="h-5 w-5" />
          <span>Joins ({{ metric.joins.length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(join, index) in metric.joins"
            :key="index"
            class="p-3 border rounded-lg"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-3">
                <Link class="h-4 w-4 text-purple-500" />
                <p class="font-medium text-sm">{{ join.name }}</p>
              </div>
              <Badge variant="outline">{{ join.join_type }}</Badge>
            </div>
            <div class="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span class="text-muted-foreground">Left:</span> {{ join.left_table }}
              </div>
              <div>
                <span class="text-muted-foreground">Right:</span> {{ join.right_table }}
              </div>
            </div>
            <p v-if="join.description" class="text-xs text-muted-foreground mt-2">
              {{ join.description }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Aggregations -->
    <Card v-if="metric.aggregations && metric.aggregations.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Calculator class="h-5 w-5" />
          <span>Aggregations ({{ metric.aggregations.length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(aggregation, index) in metric.aggregations"
            :key="index"
            class="flex items-center justify-between p-3 border rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <Calculator class="h-4 w-4 text-orange-500" />
              <div>
                <p class="font-medium text-sm">{{ aggregation.name }}</p>
                <p class="text-xs text-muted-foreground">{{ aggregation.description || 'No description' }}</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <Badge variant="outline">{{ aggregation.type }}</Badge>
              <Badge v-if="aggregation.target_column" variant="secondary">{{ aggregation.target_column }}</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Filters -->
    <Card v-if="metric.filters && metric.filters.length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Filter class="h-5 w-5" />
          <span>Filters ({{ metric.filters.length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(filter, index) in metric.filters"
            :key="index"
            class="p-3 border rounded-lg"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center space-x-3">
                <Filter class="h-4 w-4 text-red-500" />
                <p class="font-medium text-sm">{{ filter.name }}</p>
              </div>
              <div class="flex items-center space-x-2">
                <Badge :variant="filter.filter_type === 'where' ? 'default' : 'secondary'">
                  {{ filter.filter_type === 'where' ? 'WHERE' : 'HAVING' }}
                </Badge>
                <Badge v-if="filter.is_active" variant="outline">Active</Badge>
                <Badge v-else variant="secondary">Inactive</Badge>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span class="text-muted-foreground">Column:</span> {{ filter.query || 'Custom expression' }}
              </div>
              <div>
                <span class="text-muted-foreground">Operator:</span> {{ filter.operator || 'Custom' }}
              </div>
              <div v-if="filter.table">
                <span class="text-muted-foreground">Table:</span> {{ filter.table }}
              </div>
              <div>
                <span class="text-muted-foreground">Type:</span> {{ filter.value_type }}
              </div>
            </div>
            <p v-if="filter.description" class="text-xs text-muted-foreground mt-2">
              {{ filter.description }}
            </p>
            <p v-if="filter.custom_expression" class="text-xs font-mono bg-muted p-2 rounded mt-2">
              {{ filter.custom_expression }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Parameters -->
    <Card v-if="metric.parameters && Object.keys(metric.parameters).length > 0">
      <CardHeader>
        <CardTitle class="flex items-center space-x-2">
          <Settings class="h-5 w-5" />
          <span>Parameters ({{ Object.keys(metric.parameters).length }})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div class="space-y-3">
          <div
            v-for="(parameter, key) in metric.parameters"
            :key="key"
            class="flex items-center justify-between p-3 border rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <Settings class="h-4 w-4 text-indigo-500" />
              <div>
                <p class="font-medium text-sm">{{ parameter.name }}</p>
                <p class="text-xs text-muted-foreground">{{ parameter.description || 'No description' }}</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <Badge variant="outline">{{ parameter.type }}</Badge>
              <Badge v-if="parameter.required" variant="destructive">Required</Badge>
              <Badge v-else variant="secondary">Optional</Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Empty State -->
    <Card v-if="!hasAnyContent">
      <CardContent class="text-center py-8">
        <Code class="h-8 w-8 mx-auto text-muted-foreground mb-2" />
        <p class="text-sm text-muted-foreground">No schema configuration found</p>
        <p class="text-xs text-muted-foreground">This metric doesn't have any schema components defined</p>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Badge } from '~/components/ui/badge'
import { Label } from '~/components/ui/label'
import { 
  Database, 
  Target, 
  Grid, 
  Link, 
  Calculator, 
  Filter, 
  Settings, 
  Code 
} from 'lucide-vue-next'

interface Props {
  metric: any
}

const props = defineProps<Props>()

// Check if there's any content to display
const hasAnyContent = computed(() => {
  const metric = props.metric
  return (
    metric.table_name ||
    metric.query ||
    metric.limit ||
    (metric.measures && metric.measures.length > 0) ||
    (metric.dimensions && metric.dimensions.length > 0) ||
    (metric.joins && metric.joins.length > 0) ||
    (metric.aggregations && metric.aggregations.length > 0) ||
    (metric.filters && metric.filters.length > 0) ||
    (metric.parameters && Object.keys(metric.parameters).length > 0)
  )
})
</script> 