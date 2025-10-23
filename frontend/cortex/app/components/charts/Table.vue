<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  FlexRender,
  getCoreRowModel,
  getPaginationRowModel,
  useVueTable,
  type ColumnDef,
} from '@tanstack/vue-table'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const props = defineProps<{ columns: { name: string; type?: string }[]; rows: Record<string, any>[] }>()

// Convert columns to TanStack Table format
const tableColumns = computed<ColumnDef<Record<string, any>>[]>(() => 
  props.columns.map(col => ({
    accessorKey: col.name,
    header: col.name,
    cell: ({ row }) => row.getValue(col.name) ?? '-',
  }))
)

// Create table instance with pagination
const table = useVueTable({
  get data() {
    return props.rows
  },
  get columns() {
    return tableColumns.value
  },
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  initialState: {
    pagination: {
      pageSize: 10, // Default page size
    },
  },
})
</script>

<template>
  <div class="space-y-4">
    <div class="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead v-for="header in headerGroup.headers" :key="header.id">
              <FlexRender
                v-if="!header.isPlaceholder"
                :render="header.column.columnDef.header"
                :props="header.getContext()"
              />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-if="table.getRowModel().rows?.length">
            <TableRow
              v-for="row in table.getRowModel().rows"
              :key="row.id"
              :data-state="row.getIsSelected() && 'selected'"
            >
              <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
          </template>
          <TableRow v-else>
            <TableCell :colspan="columns.length" class="h-24 text-center">
              No data
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination Controls -->
    <div class="flex items-center justify-between px-2">
      <div class="flex-1 text-sm text-muted-foreground">
        Showing {{ table.getRowModel().rows.length }} of {{ table.getFilteredRowModel().rows.length }} row(s)
      </div>
      <div class="flex items-center space-x-6 lg:space-x-8">
        <div class="flex items-center space-x-2">
          <p class="text-sm font-medium">
            Rows per page
          </p>
          <Select
            :model-value="`${table.getState().pagination.pageSize}`"
            @update:model-value="(value) => table.setPageSize(Number(value))"
          >
            <SelectTrigger class="h-8 w-[70px]">
              <SelectValue :placeholder="`${table.getState().pagination.pageSize}`" />
            </SelectTrigger>
            <SelectContent side="top">
              <SelectItem v-for="pageSize in [5, 10, 20, 30, 50]" :key="pageSize" :value="`${pageSize}`">
                {{ pageSize }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="flex w-[100px] items-center justify-center text-sm font-medium">
          Page {{ table.getState().pagination.pageIndex + 1 }} of
          {{ table.getPageCount() }}
        </div>
        <div class="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="!table.getCanPreviousPage()"
            @click="table.previousPage()"
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            :disabled="!table.getCanNextPage()"
            @click="table.nextPage()"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>


