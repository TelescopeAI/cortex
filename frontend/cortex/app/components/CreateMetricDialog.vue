<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child v-if="!hideInitialTrigger">
      <Button size="sm">
        <Plus class="h-4 w-4 mr-2" />
        Add Metric
      </Button>
    </DialogTrigger>
    <MetricDialog
      :open="open"
      :is-editing="false"
      :prefilled-data-model-id="prefilledDataModelId"
      :prefilled-data-model-name="prefilledDataModelName"
      @update:open="handleOpenChange"
      @created="handleCreated"
      @close="handleClose"
    />
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Dialog, DialogTrigger } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Plus } from 'lucide-vue-next'
import MetricDialog from '~/components/MetricDialog.vue'

interface Props {
  prefilledDataModelId?: string
  prefilledDataModelName?: string
  hideInitialTrigger?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  created: [metric: any]
  close: []
}>()

const open = ref(false)

const handleOpenChange = (value: boolean) => {
  open.value = value
}

const handleCreated = (metric: any) => {
  emit('created', metric)
}

const handleClose = () => {
  emit('close')
}

// Expose methods for external control
defineExpose({
  openDialog: () => { open.value = true },
  closeDialog: () => { open.value = false }
})
</script> 