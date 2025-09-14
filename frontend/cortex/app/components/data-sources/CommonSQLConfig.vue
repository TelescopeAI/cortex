<template>
  <div class="space-y-4">
    <div v-if="!disabled" class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <Label for="host">Host</Label>
        <Input
          id="host"
          v-model="localConfig.host"
          :placeholder="getPlaceholder('host')"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
      </div>

      <div class="space-y-2">
        <Label for="port">Port</Label>
        <Input
          id="port"
          v-model.number="localConfig.port"
          type="number"
          :placeholder="getPlaceholder('port')"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
      </div>
    </div>

    <div v-else class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <Label>Host</Label>
        <div class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.host || 'Not configured' }}</div>
      </div>

      <div class="space-y-2">
        <Label>Port</Label>
        <div class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.port || 'Not configured' }}</div>
      </div>
    </div>

    <div class="space-y-2">
      <Label>{{ getDatabaseLabel() }}</Label>
      <Input
        v-if="!disabled"
        id="database"
        v-model="localConfig.database"
        :placeholder="getPlaceholder('database')"
        :disabled="disabled"
        required
        @update:model-value="updateConfig"
      />
      <div v-else class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.database || 'Not configured' }}</div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-2">
        <Label>Username</Label>
        <Input
          v-if="!disabled"
          id="username"
          v-model="localConfig.username"
          :placeholder="getPlaceholder('username')"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
        <div v-else class="p-2 bg-gray-50 rounded border text-sm">{{ localConfig.username || 'Not configured' }}</div>
      </div>

      <div class="space-y-2">
        <Label>Password</Label>
        <Input
          v-if="!disabled"
          id="password"
          v-model="localConfig.password"
          type="password"
          placeholder="Enter password"
          :disabled="disabled"
          required
          @update:model-value="updateConfig"
        />
        <div v-else class="p-2 bg-gray-50 rounded border text-sm">
          {{ localConfig.password ? '••••••••' : 'Not configured' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'

type DatabaseType = 'oracle' | 'snowflake' | 'redshift'

interface CommonSQLConfig {
  host: string
  port: number
  username: string
  password: string
  database: string
  dialect: string
}

interface Props {
  modelValue: any
  databaseType: DatabaseType
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const localConfig = reactive<CommonSQLConfig>({ ...props.modelValue })

watch(() => props.modelValue, (newValue) => {
  Object.assign(localConfig, newValue)
}, { deep: true })

const updateConfig = () => {
  // Set the correct dialect based on database type
  localConfig.dialect = props.databaseType
  emit('update:modelValue', { ...localConfig })
}

const getPlaceholder = (field: string): string => {
  const placeholders = {
    oracle: {
      host: 'hostname.oracle.com',
      port: '1521',
      database: 'XE',
      username: 'hr'
    },
    snowflake: {
      host: 'account.snowflakecomputing.com',
      port: '443',
      database: 'MYDATABASE',
      username: 'myuser'
    },
    redshift: {
      host: 'cluster.region.redshift.amazonaws.com',
      port: '5439',
      database: 'dev',
      username: 'awsuser'
    }
  }
  
  return placeholders[props.databaseType][field as keyof typeof placeholders.oracle] || ''
}

const getDatabaseLabel = (): string => {
  const labels = {
    oracle: 'Database/Service Name',
    snowflake: 'Database',
    redshift: 'Database'
  }
  
  return labels[props.databaseType] || 'Database'
}
</script>
