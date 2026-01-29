<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PostgreSQL from '~/components/data-sources/display/PostgreSQL.vue'
import MySQL from '~/components/data-sources/display/MySQL.vue'
import SQLite from '~/components/data-sources/display/SQLite.vue'
import BigQuery from '~/components/data-sources/display/BigQuery.vue'
import Spreadsheet from '~/components/data-sources/display/Spreadsheet.vue'
import type { DataSource } from '~/types'

interface Props {
  dataSource: DataSource
  showDescription?: boolean
}

interface Emits {
  (e: 'click', dataSource: DataSource): void
}

const props = withDefaults(defineProps<Props>(), {
  showDescription: true
})

const emit = defineEmits<Emits>()

// Schema fetching
const { getDataSourceSchema } = useDataSources()

const schemaLoading = ref(false)
const schemaTables = ref<Array<{
  name: string
  columns: Array<{
    name: string
    type: string
    nullable?: boolean
    primary_key?: boolean
  }>
}>>([])

onMounted(async () => {
  try {
    schemaLoading.value = true
    const schema = await getDataSourceSchema(props.dataSource.id)
    schemaTables.value = schema.tables
  } catch (error) {
    console.error('Failed to fetch schema:', error)
  } finally {
    schemaLoading.value = false
  }
})

const handleClick = (dataSource: DataSource) => {
  emit('click', dataSource)
}
</script>

<template>
  <PostgreSQL
    v-if="dataSource.source_type === 'postgresql'"
    :data-source="dataSource"
    :show-description="showDescription"
    :schema-tables="schemaTables"
    :schema-loading="schemaLoading"
    @click="handleClick"
  >
    <template #actions>
      <slot name="actions" />
    </template>
  </PostgreSQL>

  <MySQL
    v-else-if="dataSource.source_type === 'mysql'"
    :data-source="dataSource"
    :show-description="showDescription"
    :schema-tables="schemaTables"
    :schema-loading="schemaLoading"
    @click="handleClick"
  >
    <template #actions>
      <slot name="actions" />
    </template>
  </MySQL>

  <SQLite
    v-else-if="dataSource.source_type === 'sqlite'"
    :data-source="dataSource"
    :show-description="showDescription"
    :schema-tables="schemaTables"
    :schema-loading="schemaLoading"
    @click="handleClick"
  >
    <template #actions>
      <slot name="actions" />
    </template>
  </SQLite>

  <BigQuery
    v-else-if="dataSource.source_type === 'bigquery'"
    :data-source="dataSource"
    :show-description="showDescription"
    :schema-tables="schemaTables"
    :schema-loading="schemaLoading"
    @click="handleClick"
  >
    <template #actions>
      <slot name="actions" />
    </template>
  </BigQuery>

  <Spreadsheet
    v-else-if="dataSource.source_type === 'spreadsheet'"
    :data-source="dataSource"
    :show-description="showDescription"
    :schema-tables="schemaTables"
    :schema-loading="schemaLoading"
    @click="handleClick"
  >
    <template #actions>
      <slot name="actions" />
    </template>
  </Spreadsheet>

  <!-- Default fallback -->
  <div v-else>
    <p class="text-sm text-muted-foreground">
      Unsupported data source type: {{ dataSource.source_type }}
    </p>
  </div>
</template>
