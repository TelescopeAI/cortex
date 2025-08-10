<script setup lang="ts">
import { computed, ref } from 'vue'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import { Button } from '~/components/ui/button'
import { Input } from '~/components/ui/input'
import { Badge } from '~/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { Search, ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import type { DashboardWidget, StandardChartData, TableColumn } from '~/types/dashboards'

interface Props {
  widget: DashboardWidget
  data: StandardChartData
  executionResult?: any
}

const props = defineProps<Props>()

// State
const searchQuery = ref('')
const currentPage = ref(1)
const sortColumn = ref<string>('')
const sortDirection = ref<'asc' | 'desc'>('asc')

// Computed
const tableConfig = computed(() => {
  // @ts-expect-error table_config is provided by backend shape for table viz
  return props.widget.visualization?.table_config as any
})

const tableData = computed(() => {
  return props.data.processed.table
})

const columns = computed(() => {
  return tableData.value?.columns || []
})

const allRows = computed(() => {
  return tableData.value?.rows || []
})

const pageSize = computed(() => {
  return tableConfig.value?.page_size || 10
})

const showPagination = computed(() => {
  return tableConfig.value?.pagination !== false && allRows.value.length > pageSize.value
})

const showSearch = computed(() => {
  return tableConfig.value?.searchable === true
})

const filteredAndSortedRows = computed(() => {
  let rows = [...allRows.value]
  
  // Apply search filter
  if (searchQuery.value && showSearch.value) {
    const query = searchQuery.value.toLowerCase()
    rows = rows.filter(row => 
      Object.values(row.data).some(value => 
        String(value).toLowerCase().includes(query)
      )
    )
  }
  
  // Apply sorting
  if (sortColumn.value) {
    rows.sort((a, b) => {
      const aValue = a.data[sortColumn.value]
      const bValue = b.data[sortColumn.value]
      
      // Handle different data types
      let comparison = 0
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue
      } else {
        comparison = String(aValue).localeCompare(String(bValue))
      }
      
      return sortDirection.value === 'asc' ? comparison : -comparison
    })
  }
  
  return rows
})

const paginatedRows = computed(() => {
  if (!showPagination.value) {
    return filteredAndSortedRows.value
  }
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAndSortedRows.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredAndSortedRows.value.length / pageSize.value)
})

const showingRange = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value + 1
  const end = Math.min(start + pageSize.value - 1, filteredAndSortedRows.value.length)
  return { start, end, total: filteredAndSortedRows.value.length }
})

// Methods
function sortBy(columnName: string) {
  if (!tableConfig.value?.sortable) return
  
  if (sortColumn.value === columnName) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = columnName
    sortDirection.value = 'asc'
  }
  
  // Reset to first page when sorting
  currentPage.value = 1
}

function getSortIcon(columnName: string) {
  if (sortColumn.value !== columnName) return ArrowUpDown
  return sortDirection.value === 'asc' ? ArrowUp : ArrowDown
}

function formatCellValue(value: any, column: TableColumn) {
  if (value === null || value === undefined) return '-'
  
  switch (column.type) {
    case 'number':
      return typeof value === 'number' ? value.toLocaleString() : value
    case 'currency':
      return new Intl.NumberFormat(undefined, { 
        style: 'currency', 
        currency: 'USD' 
      }).format(Number(value))
    case 'percentage':
      return `${(Number(value) * 100).toFixed(1)}%`
    case 'date':
      return new Date(value).toLocaleDateString()
    case 'datetime':
      return new Date(value).toLocaleString()
    default:
      return String(value)
  }
}

function goToPage(page: number) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

function getColumnWidth(column: TableColumn) {
  // Auto-size columns based on content type
  switch (column.type) {
    case 'number':
    case 'currency':
    case 'percentage':
      return 'w-24'
    case 'date':
      return 'w-32'
    case 'datetime':
      return 'w-40'
    default:
      return 'w-auto'
  }
}
</script>

<template>
  <div class="h-full flex flex-col space-y-4">
    <!-- Search and Controls -->
    <div v-if="showSearch" class="flex items-center gap-4">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          placeholder="Search table..."
          class="pl-10"
        />
      </div>
      <Badge variant="secondary" class="text-xs">
        {{ filteredAndSortedRows.length }} row{{ filteredAndSortedRows.length !== 1 ? 's' : '' }}
      </Badge>
    </div>

    <!-- Table -->
    <div class="flex-1 border rounded-md">
      <Table>
        <TableHeader v-if="tableConfig?.show_header !== false">
          <TableRow>
            <TableHead
              v-for="column in columns"
              :key="column.name"
              :class="[
                getColumnWidth(column),
                tableConfig?.sortable ? 'cursor-pointer hover:bg-muted/50' : ''
              ]"
              @click="sortBy(column.name)"
            >
              <div class="flex items-center gap-2">
                <span class="font-medium">{{ column.name }}</span>
                <component
                  :is="getSortIcon(column.name)"
                  v-if="tableConfig?.sortable"
                  class="w-4 h-4 text-muted-foreground"
                />
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-if="paginatedRows.length === 0">
            <TableCell :colspan="columns.length" class="text-center py-8 text-muted-foreground">
              {{ searchQuery ? 'No matching results found' : 'No data available' }}
            </TableCell>
          </TableRow>
          <TableRow
            v-for="(row, index) in paginatedRows"
            :key="index"
            class="hover:bg-muted/50"
          >
            <TableCell
              v-for="column in columns"
              :key="column.name"
              :class="getColumnWidth(column)"
            >
              {{ formatCellValue(row.data[column.name], column) }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <div v-if="showPagination" class="flex items-center justify-between">
      <div class="text-sm text-muted-foreground">
        Showing {{ showingRange.start }} to {{ showingRange.end }} of {{ showingRange.total }} entries
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          <ChevronLeft class="w-4 h-4" />
        </Button>
        
        <div class="flex items-center gap-1">
          <Button
            v-for="page in Math.min(5, totalPages)"
            :key="page"
            variant="outline"
            size="sm"
            :class="{ 'bg-primary text-primary-foreground': page === currentPage }"
            @click="goToPage(page)"
          >
            {{ page }}
          </Button>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        >
          <ChevronRight class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </div>
</template>