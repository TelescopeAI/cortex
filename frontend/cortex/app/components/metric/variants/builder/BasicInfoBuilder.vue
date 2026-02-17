<template>
  <div class="space-y-4">
    <div class="grid gap-4">
      <!-- Name -->
      <div class="space-y-2">
        <Label for="variant-name">
          Name
          <span class="text-destructive">*</span>
        </Label>
        <Input
          id="variant-name"
          :model-value="modelValue.name"
          @update:model-value="updateField('name', $event)"
          placeholder="Enter variant name"
          :class="{ 'border-destructive': errors?.name }"
        />
        <p v-if="errors?.name" class="text-sm text-destructive">
          {{ errors.name }}
        </p>
      </div>

      <!-- Alias -->
      <div class="space-y-2">
        <Label for="variant-alias">
          Alias
        </Label>
        <Input
          id="variant-alias"
          :model-value="modelValue.alias"
          @update:model-value="updateField('alias', $event)"
          placeholder="Optional alias for SQL generation"
        />
        <p class="text-xs text-muted-foreground">
          Used as table alias in generated SQL queries
        </p>
      </div>

      <!-- Description -->
      <div class="space-y-2">
        <Label for="variant-description">
          Description
        </Label>
        <Textarea
          id="variant-description"
          :model-value="modelValue.description"
          @update:model-value="updateField('description', $event)"
          placeholder="Describe what makes this variant different"
          rows="3"
        />
      </div>

      <!-- Public Toggle -->
      <div class="flex items-center justify-between space-x-2 rounded-lg border p-4">
        <div class="space-y-0.5">
          <Label for="variant-public" class="text-base">
            Public Variant
          </Label>
          <p class="text-sm text-muted-foreground">
            Make this variant visible to all users in the environment
          </p>
        </div>
        <Switch
          id="variant-public"
          :checked="modelValue.public"
          @update:checked="updateField('public', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Switch } from '~/components/ui/switch'

interface BasicInfo {
  name: string
  alias: string
  description: string
  public: boolean
}

interface Props {
  modelValue: BasicInfo
  errors?: Record<string, string>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: BasicInfo]
}>()

const updateField = (field: keyof BasicInfo, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}
</script>
