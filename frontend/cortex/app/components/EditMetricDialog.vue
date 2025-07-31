<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Edit class="h-4 w-4 mr-2" />
        Edit
      </Button>
    </DialogTrigger>
    <MetricDialog
      :open="open"
      :is-editing="true"
      :metric-to-edit="metric"
      @update:open="handleOpenChange"
      @updated="handleUpdated"
      @close="handleClose"
    />
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Dialog, DialogTrigger } from '~/components/ui/dialog'
import { Button } from '~/components/ui/button'
import { Edit } from 'lucide-vue-next'
import MetricDialog from '~/components/MetricDialog.vue'

interface Props {
  metric: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  updated: [metric: any]
  close: []
}>()

const open = ref(false)

const handleOpenChange = (value: boolean) => {
  open.value = value
}

const handleUpdated = (metric: any) => {
  emit('updated', metric)
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