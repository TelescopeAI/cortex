<template>
  <div class="flex-1 space-y-4 p-4 pt-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Data Models</h1>
        <p class="text-muted-foreground">
          Create and manage semantic data models for analytics
        </p>
      </div>
      <Button @click="navigateToCreate" class="gap-2">
        <Plus class="h-4 w-4" />
        New Model
      </Button>
    </div>

    <!-- Search and Filters -->
    <div class="flex items-center space-x-4">
      <div class="flex-1 max-w-sm">
        <Input
          v-model="searchQuery"
          placeholder="Search models..."
          class="w-full"
        />
      </div>
      

      <Select v-model="statusFilter">
        <SelectTrigger class="w-[150px]">
          <SelectValue placeholder="All statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="inactive">Inactive</SelectItem>
          <SelectItem value="valid">Valid</SelectItem>
          <SelectItem value="invalid">Invalid</SelectItem>
        </SelectContent>
      </Select>

      <Button variant="outline" size="sm" @click="toggleView">
        <Grid3x3 v-if="viewMode === 'list'" class="h-4 w-4" />
        <List v-if="viewMode === 'grid'" class="h-4 w-4" />
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card v-for="i in 6" :key="i" class="p-6">
        <Skeleton class="h-4 w-[250px] mb-2" />
        <Skeleton class="h-4 w-[200px] mb-4" />
        <Skeleton class="h-8 w-[100px]" />
      </Card>
    </div>

    <!-- Error State -->
    <Alert v-if="error" variant="destructive" class="mb-4">
      <AlertCircle class="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <!-- Empty State -->
    <div 
      v-if="!isLoading && !error && filteredModels.length === 0" 
      class="text-center py-12"
    >
      <Database class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No data models found</h3>
      <p class="text-muted-foreground mb-4">
        {{ dataModels.length === 0 ? 'Get started by creating your first data model.' : 'Try adjusting your filters.' }}
      </p>
      <Button v-if="dataModels.length === 0" @click="navigateToCreate">
        Create Data Model
      </Button>
    </div>

    <!-- Grid View -->
    <div 
      v-if="!isLoading && !error && filteredModels.length > 0 && viewMode === 'grid'" 
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <Card 
        v-for="model in filteredModels" 
        :key="model.id" 
        class="cursor-pointer hover:shadow-md transition-shadow"
        @click="navigateToModel(model.id)"
      >
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="space-y-1 flex-1 min-w-0">
              <CardTitle class="text-lg truncate">{{ model.name }}</CardTitle>
              <p v-if="model.description" class="text-sm text-muted-foreground line-clamp-2">
                {{ model.description }}
              </p>
            </div>
            <Badge :variant="getStatusVariant(model)">
              {{ getStatusText(model) }}
            </Badge>
          </div>
        </CardHeader>

        <CardContent class="pt-0">
          <div class="space-y-3">
            <!-- Model Info -->
            <div class="flex items-center gap-4 text-sm text-muted-foreground">
              <div class="flex items-center gap-1">
                <Hash class="h-3 w-3" />
                v{{ model.version }}
              </div>
              <div class="flex items-center gap-1">
                <Clock class="h-3 w-3" />
                {{ formatDate(model.updated_at) }}
              </div>
            </div>

            <!-- Validation Status -->
            <div class="flex items-center gap-2">
              <Badge 
                :variant="model.is_valid ? 'default' : 'destructive'" 
                class="text-xs"
              >
                <CheckCircle v-if="model.is_valid" class="h-3 w-3 mr-1" />
                <XCircle v-else class="h-3 w-3 mr-1" />
                {{ model.is_valid ? 'Valid' : `${model.validation_errors?.length || 0} errors` }}
              </Badge>
            </div>

            <!-- Actions -->
            <div class="flex gap-2 pt-2">
              <Button 
                size="sm" 
                variant="outline" 
                @click.stop="navigateToModel(model.id)"
              >
                Edit
              </Button>
              <Button 
                size="sm" 
                variant="ghost"
                @click.stop="executeModel(model.id)"
                :disabled="!model.is_valid"
              >
                Execute
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <Button size="sm" variant="ghost" @click.stop>
                    <MoreHorizontal class="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem @click="cloneModel(model.id)">
                    <Copy class="h-4 w-4 mr-2" />
                    Clone
                  </DropdownMenuItem>
                  <DropdownMenuItem @click="validateModel(model.id)">
                    <CheckCircle class="h-4 w-4 mr-2" />
                    Validate
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    @click="confirmDelete(model.id)"
                    class="text-destructive"
                  >
                    <Trash2 class="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- List View -->
    <Card v-if="!isLoading && !error && filteredModels.length > 0 && viewMode === 'list'">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Version</TableHead>
            <TableHead>Updated</TableHead>
            <TableHead class="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow 
            v-for="model in filteredModels" 
            :key="model.id"
            class="cursor-pointer"
            @click="navigateToModel(model.id)"
          >
            <TableCell>
              <div>
                <div class="font-medium">{{ model.name }}</div>
                <div v-if="model.description" class="text-sm text-muted-foreground">
                  {{ model.description }}
                </div>
              </div>
            </TableCell>
            <TableCell>
              <div class="flex items-center gap-2">
                <Badge :variant="getStatusVariant(model)">
                  {{ getStatusText(model) }}
                </Badge>
                <Badge 
                  :variant="model.is_valid ? 'default' : 'destructive'" 
                  class="text-xs"
                >
                  {{ model.is_valid ? 'Valid' : 'Invalid' }}
                </Badge>
              </div>
            </TableCell>
            <TableCell>v{{ model.version }}</TableCell>
            <TableCell>-</TableCell>
            <TableCell>{{ formatDate(model.updated_at) }}</TableCell>
            <TableCell class="text-right">
              <div class="flex justify-end gap-2">
                <Button size="sm" variant="outline" @click.stop="navigateToModel(model.id)">
                  Edit
                </Button>
                <Button 
                  size="sm" 
                  variant="ghost"
                  @click.stop="executeModel(model.id)"
                  :disabled="!model.is_valid"
                >
                  Execute
                </Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Card>
  </div>

  <!-- Delete Confirmation Dialog -->
  <Dialog v-model:open="showDeleteDialog">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Delete Data Model</DialogTitle>
        <DialogDescription>
          Are you sure you want to delete this data model? This action cannot be undone.
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" @click="showDeleteDialog = false">
          Cancel
        </Button>
        <Button variant="destructive" @click="handleDelete">
          Delete
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDataModels } from '~/composables/useDataModels'
import { useDataSources } from '~/composables/useDataSources'
import { useEnvironments } from '~/composables/useEnvironments'
import { 
  Plus, Grid3x3, List, Database, Hash, Clock, CheckCircle, XCircle, 
  MoreHorizontal, Copy, Trash2, AlertCircle 
} from 'lucide-vue-next'

import { Button } from '~/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '~/components/ui/select'
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, 
  DropdownMenuSeparator, DropdownMenuTrigger 
} from '~/components/ui/dropdown-menu'
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from '~/components/ui/table'
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle 
} from '~/components/ui/dialog'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import { Skeleton } from '~/components/ui/skeleton'

// Composables
const router = useRouter()
const { 
  models: dataModels, loading: isLoading, error, fetchModels: fetchDataModels, deleteModel: deleteDataModel, 
  validateModel: validateModelAction, executeModel: executeModelAction
} = useDataModels()
const { selectedEnvironmentId } = useEnvironments()

// Reactive state
const searchQuery = ref('')
const statusFilter = ref('all')
const viewMode = ref<'grid' | 'list'>('grid')
const showDeleteDialog = ref(false)
const modelToDelete = ref<string | null>(null)

// Computed
const filteredModels = computed(() => {
  let filtered = dataModels.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(model => 
      model.name.toLowerCase().includes(query) ||
      model.description?.toLowerCase().includes(query) ||
      model.alias?.toLowerCase().includes(query)
    )
  }


  // Status filter
  if (statusFilter.value && statusFilter.value !== 'all') {
    switch (statusFilter.value) {
      case 'active':
        filtered = filtered.filter(model => model.is_active)
        break
      case 'inactive':
        filtered = filtered.filter(model => !model.is_active)
        break
      case 'valid':
        filtered = filtered.filter(model => model.is_valid)
        break
      case 'invalid':
        filtered = filtered.filter(model => !model.is_valid)
        break
    }
  }

  return filtered
})

// Methods
const navigateToCreate = () => {
  router.push('/data/models/create')
}

const navigateToModel = (id: string) => {
  router.push(`/data/models/${id}`)
}

const executeModel = (id: string) => {
  router.push(`/data/models/${id}/execution`)
}

const toggleView = () => {
  viewMode.value = viewMode.value === 'grid' ? 'list' : 'grid'
}

const getStatusVariant = (model: any) => {
  if (!model.is_active) return 'secondary'
  return model.is_valid ? 'default' : 'destructive'
}

const getStatusText = (model: any) => {
  if (!model.is_active) return 'Inactive'
  return model.is_valid ? 'Active' : 'Error'
}


const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const validateModel = async (id: string) => {
  try {
    await validateModelAction(id)
    // Refresh the model data
    if (selectedEnvironmentId.value) {
      await fetchDataModels(selectedEnvironmentId.value)
    }
  } catch (err) {
    console.error('Failed to validate model:', err)
  }
}

const cloneModel = async (id: string) => {
  // TODO: Implement clone functionality
  console.log('Clone model:', id)
}

const confirmDelete = (id: string) => {
  modelToDelete.value = id
  showDeleteDialog.value = true
}

const handleDelete = async () => {
  if (modelToDelete.value) {
    try {
      await deleteDataModel(modelToDelete.value, selectedEnvironmentId.value || '')
      showDeleteDialog.value = false
      modelToDelete.value = null
    } catch (err) {
      console.error('Failed to delete model:', err)
    }
  }
}

// Lifecycle
onMounted(async () => {
  if (selectedEnvironmentId.value) {
    await fetchDataModels(selectedEnvironmentId.value)
  }
})
</script> 