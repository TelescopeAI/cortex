<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <Label>Database File Path</Label>
      <Input
        v-if="!disabled"
        id="database"
        v-model="localConfig.database"
        placeholder="/path/to/database.db"
        :disabled="disabled"
        required
        @update:model-value="updateConfig"
      />
      <div v-else class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.database || 'Not configured' }}</div>
      <p v-if="!disabled" class="text-xs text-muted-foreground">
        Full path to the SQLite database file
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'

interface SQLiteConfig {
  database: string
  dialect: string
}

interface Props {
  modelValue: any
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  modelValue: () => ({
    database: '',
    dialect: 'sqlite'
  })
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const localConfig = reactive<SQLiteConfig>({ ...props.modelValue })

watch(() => props.modelValue, (newValue) => {
  Object.assign(localConfig, newValue)
}, { deep: true })

const updateConfig = () => {
  localConfig.dialect = 'sqlite'
  emit('update:modelValue', { ...localConfig })
}
</script>
