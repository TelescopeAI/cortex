<script setup lang="ts">
import { ref } from 'vue';
import { toast } from 'vue-sonner';
import { Upload } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '~/components/ui/dialog';
import { FileUpload, FileUploadGrid } from '~/components/ui/file-upload';
import { useSpreadsheets } from '~/composables/useSpreadsheets';
import { useEnvironments } from '~/composables/useEnvironments';

const emit = defineEmits<{
  filesUploaded: [fileIds: string[]];
}>();

const { uploadFiles, loading: uploading, error } = useSpreadsheets();
const { selectedEnvironmentId } = useEnvironments();

const open = ref(false);
const selectedFiles = ref<File[]>([]);
const isUploading = ref(false);
const showOverwriteConfirm = ref(false);
const duplicateFiles = ref<string[]>([]);
const pendingFiles = ref<File[]>([]);

function handleFilesSelected(files: File[]) {
  selectedFiles.value = files.filter(f => f.type === 'text/csv' || f.name.endsWith('.csv'));
  
  if (files.length !== selectedFiles.value.length) {
    toast.warning('Only CSV files are supported');
  }
}

async function handleUpload(overwrite = false) {
  if (selectedFiles.value.length === 0) {
    toast.error('Please select at least one CSV file');
    return;
  }

  if (!selectedEnvironmentId.value) {
    toast.error('No environment selected');
    return;
  }

  isUploading.value = true;

  try {
    const result = await uploadFiles(selectedFiles.value, selectedEnvironmentId.value, overwrite);
    toast.success(`Successfully uploaded ${result.file_ids.length} file(s)`);
    
    emit('filesUploaded', result.file_ids);
    
    selectedFiles.value = [];
    open.value = false;
    showOverwriteConfirm.value = false;
  } catch (err: any) {
    if (err.type === 'StorageFileAlreadyExists') {
      // Show confirmation dialog
      duplicateFiles.value = [err.filename];
      pendingFiles.value = selectedFiles.value;
      showOverwriteConfirm.value = true;
    } else {
      toast.error('Failed to upload files');
    }
  } finally {
    isUploading.value = false;
  }
}

function confirmOverwrite() {
  showOverwriteConfirm.value = false;
  handleUpload(true);  // Retry with overwrite=true
}

function cancelOverwrite() {
  showOverwriteConfirm.value = false;
  duplicateFiles.value = [];
  pendingFiles.value = [];
}

function resetDialog() {
  selectedFiles.value = [];
}
</script>

<template>
  <!-- Main upload dialog -->
  <Dialog v-model:open="open" @update:open="(isOpen) => { if (!isOpen) resetDialog() }">
    <DialogTrigger as-child>
      <Button variant="outline" size="sm">
        <Upload class="w-4 h-4 mr-2" />
        Upload
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[600px]">
      <DialogHeader>
        <DialogTitle>Upload CSV Files</DialogTitle>
        <DialogDescription>
          Drag and drop CSV files or click to browse
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4">
        <FileUpload @onChange="handleFilesSelected" class="border rounded-lg p-4">
          <FileUploadGrid class="h-32" />
        </FileUpload>

        <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">
          {{ error }}
        </div>

        <div v-if="selectedFiles.length > 0" class="space-y-2">
          <p class="text-sm font-medium">Selected files: {{ selectedFiles.length }}</p>
          <ul class="text-sm space-y-1">
            <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${index}`" class="text-muted-foreground">
              • {{ file.name }} ({{ (file.size / 1024).toFixed(1) }} KB)
            </li>
          </ul>
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="open = false" :disabled="isUploading">
          Cancel
        </Button>
        <Button @click="handleUpload(false)" :disabled="selectedFiles.length === 0 || isUploading"
                class="cursor-pointer">
          <span v-if="isUploading">Uploading...</span>
          <span v-else>Upload</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- Overwrite confirmation dialog -->
  <Dialog v-model:open="showOverwriteConfirm">
    <DialogContent>
      <DialogHeader>
        <DialogTitle>File Already Exists</DialogTitle>
        <DialogDescription>
          The following file already exists: <strong>{{ duplicateFiles[0] }}</strong>
          <br />
          Do you want to overwrite it?
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" @click="cancelOverwrite">
          Cancel
        </Button>
        <Button variant="destructive" @click="confirmOverwrite">
          Overwrite
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
