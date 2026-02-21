<template>
  <div v-if="schema && schema.tables" class="border rounded-lg p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold">Database Schema</h3>
      <Badge variant="outline">{{ schema.tables.length }} table{{ schema.tables.length !== 1 ? 's' : '' }}</Badge>
    </div>
    
    <Accordion type="single" collapsible class="w-full">
      <AccordionItem
        v-for="table in schema.tables"
        :key="table.name"
        :value="table.name"
        class="border-b"
      >
        <AccordionTrigger class="hover:no-underline">
          <div class="flex items-center gap-2">
            <Database class="w-4 h-4 text-muted-foreground" />
            <span class="font-medium">{{ table.name }}</span>
            <Badge variant="secondary" class="ml-2">
              {{ table.columns.length }} column{{ table.columns.length !== 1 ? 's' : '' }}
            </Badge>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div class="pt-2 space-y-4">
            <Tabs default-value="schema" v-if="dataSourceId">
              <TabsList>
                <TabsTrigger value="schema">Schema</TabsTrigger>
                <TabsTrigger value="data">Data</TabsTrigger>
              </TabsList>
              <TabsContent value="schema">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Column Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Nullable</TableHead>
                      <TableHead>Primary Key</TableHead>
                      <TableHead>Foreign Key</TableHead>
                      <TableHead>Default</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="column in table.columns" :key="column.name">
                      <TableCell class="font-medium">{{ column.name }}</TableCell>
                      <TableCell>
                        <code class="text-xs bg-muted px-1.5 py-0.5 rounded">{{ column.type }}</code>
                      </TableCell>
                      <TableCell>
                        <Badge v-if="column.nullable" variant="outline">Yes</Badge>
                        <Badge v-else variant="secondary">No</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge v-if="isPrimaryKey(table, column.name)" variant="default">PK</Badge>
                        <span v-else class="text-muted-foreground">-</span>
                      </TableCell>
                      <TableCell>
                        <div v-if="getForeignKeyInfo(table, column.name)" class="flex flex-col gap-1">
                          <Badge
                            v-for="(fk, index) in getForeignKeyInfo(table, column.name)"
                            :key="`${fk.referenced_table}-${fk.referenced_column}-${index}`"
                            variant="outline"
                            class="text-xs"
                          >
                            → {{ fk.referenced_table }}.{{ fk.referenced_column }}
                          </Badge>
                        </div>
                        <span v-else class="text-muted-foreground">-</span>
                      </TableCell>
                      <TableCell>
                        <code v-if="column.default_value !== null && column.default_value !== undefined" class="text-xs bg-muted px-1.5 py-0.5 rounded">
                          {{ String(column.default_value) }}
                        </code>
                        <span v-else class="text-muted-foreground">-</span>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TabsContent>
              <TabsContent value="data">
                <SourceTableContents
                  :data-source-id="dataSourceId"
                  :table-name="table.name"
                />
              </TabsContent>
            </Tabs>
            <!-- Fallback: no dataSourceId, show schema table directly -->
            <Table v-else>
              <TableHeader>
                <TableRow>
                  <TableHead>Column Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Nullable</TableHead>
                  <TableHead>Primary Key</TableHead>
                  <TableHead>Foreign Key</TableHead>
                  <TableHead>Default</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="column in table.columns" :key="column.name">
                  <TableCell class="font-medium">{{ column.name }}</TableCell>
                  <TableCell>
                    <code class="text-xs bg-muted px-1.5 py-0.5 rounded">{{ column.type }}</code>
                  </TableCell>
                  <TableCell>
                    <Badge v-if="column.nullable" variant="outline">Yes</Badge>
                    <Badge v-else variant="secondary">No</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge v-if="isPrimaryKey(table, column.name)" variant="default">PK</Badge>
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell>
                    <div v-if="getForeignKeyInfo(table, column.name)" class="flex flex-col gap-1">
                      <Badge
                        v-for="(fk, index) in getForeignKeyInfo(table, column.name)"
                        :key="`${fk.referenced_table}-${fk.referenced_column}-${index}`"
                        variant="outline"
                        class="text-xs"
                      >
                        → {{ fk.referenced_table }}.{{ fk.referenced_column }}
                      </Badge>
                    </div>
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                  <TableCell>
                    <code v-if="column.default_value !== null && column.default_value !== undefined" class="text-xs bg-muted px-1.5 py-0.5 rounded">
                      {{ String(column.default_value) }}
                    </code>
                    <span v-else class="text-muted-foreground">-</span>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  </div>
</template>

<script setup lang="ts">
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '~/components/ui/accordion';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Database } from 'lucide-vue-next';
import SourceTableContents from '~/components/SourceTableContents.vue';

interface ForeignKeyRelation {
  column: string;
  referenced_table: string;
  referenced_column: string;
}

interface ForeignKeySchema {
  table: string;
  relations: ForeignKeyRelation[];
}

interface ColumnSchema {
  name: string;
  type: string;
  max_length?: number;
  precision?: number;
  scale?: number;
  nullable?: boolean;
  default_value?: string;
}

interface TableSchema {
  name: string;
  columns: ColumnSchema[];
  primary_keys: string[];
  foreign_keys: ForeignKeySchema[];
}

interface DatabaseSchema {
  tables: TableSchema[];
}

interface Props {
  schema: DatabaseSchema | null;
  dataSourceId?: string;
}

const props = defineProps<Props>();

// Check if a column is a primary key
function isPrimaryKey(table: TableSchema, columnName: string): boolean {
  return table.primary_keys && table.primary_keys.includes(columnName);
}

// Get foreign key information for a column
function getForeignKeyInfo(table: TableSchema, columnName: string): ForeignKeyRelation[] | null {
  if (!table.foreign_keys || table.foreign_keys.length === 0) {
    return null;
  }
  
  // Find foreign keys where this column is involved
  const relations: ForeignKeyRelation[] = [];
  for (const fk of table.foreign_keys) {
    for (const relation of fk.relations) {
      if (relation.column === columnName) {
        relations.push(relation);
      }
    }
  }
  
  return relations.length > 0 ? relations : null;
}
</script>

