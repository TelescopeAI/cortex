<script setup lang="ts">
import { computed } from 'vue'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const props = defineProps<{ columns: { name: string; type?: string }[]; rows: Record<string, any>[] }>()

const colNames = computed(() => props.columns.map(c => c.name))
</script>

<template>
  <div class="border rounded-md">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead v-for="c in columns" :key="c.name">{{ c.name }}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-if="rows.length === 0">
          <TableCell :colspan="columns.length" class="text-center py-6 text-muted-foreground">No data</TableCell>
        </TableRow>
        <TableRow v-for="(r, idx) in rows" :key="idx">
          <TableCell v-for="c in columns" :key="c.name">{{ r[c.name] ?? '-' }}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>


