<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Skeleton } from '~/components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '~/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from '~/components/ui/alert-dialog';
import { FileSpreadsheet, Upload, Database, ArrowLeft, Trash2, AlertTriangle } from 'lucide-vue-next';
import UploadFilesDialog from '~/components/UploadFilesDialog.vue';
import { useSpreadsheets } from '~/composables/useSpreadsheets';
import { useEnvironments } from '~/composables/useEnvironments';
import { useFiles } from '~/composables/useFiles';
import { toast } from 'vue-sonner';
import type { FileDependenciesError } from '~/types';

const router = useRouter();
const { listUploadedFiles, loading } = useSpreadsheets();
const { selectedEnvironmentId } = useEnvironments();
const { deleteFile } = useFiles();

// Delete dialog state
const showDeleteDialog = ref(false);
const showCascadeDialog = ref(false);
const fileToDelete = ref<string | null>(null);
const fileNameToDelete = ref<string>('');
const dependenciesToDelete = ref<FileDependenciesError | null>(null);
const isDeleting = ref(false);

const uploadedFiles = ref<Array<{
  id: string;
  name: string;
  extension: string;
  size: number;
  mime_type: string;
  hash: string;
  created_at: string;
  updated_at: string;
}>>([]);

onMounted(async () => {
  if (selectedEnvironmentId.value) {
    try {
      const files = await listUploadedFiles(selectedEnvironmentId.value);
      uploadedFiles.value = files;
    } catch (err) {
      console.error('Failed to load files:', err);
    }
  }
});

function handleFilesUploaded(fileIds: string[]) {
  // Refresh file list
  if (selectedEnvironmentId.value) {
    listUploadedFiles(selectedEnvironmentId.value).then(files => {
      uploadedFiles.value = files;
    });
  }
}

function createDataSourceFromFile(fileId: string, fileName: string) {
  // Navigate to create data source with pre-filled file ID and name
  // The file_name will be used to auto-generate the data source name
  router.push({
    path: '/data/sources',
    query: { create: 'spreadsheet', file_id: fileId, file_name: fileName },
  });
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString();
}

function formatSize(bytes: number | null): string {
  if (!bytes) return 'Unknown';
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

function confirmDelete(fileId: string, fileName: string) {
  fileToDelete.value = fileId;
  fileNameToDelete.value = fileName;
  showDeleteDialog.value = true;
}

async function handleDelete(cascade: boolean = false) {
  if (!fileToDelete.value || !selectedEnvironmentId.value) return;
  isDeleting.value = true;

  try {
    await deleteFile(fileToDelete.value, selectedEnvironmentId.value, cascade);
    toast.success('File deleted successfully');
    showDeleteDialog.value = false;
    showCascadeDialog.value = false;

    // Refresh file list
    const files = await listUploadedFiles(selectedEnvironmentId.value);
    uploadedFiles.value = files;
  } catch (error: any) {
    console.error('Error deleting file:', error);

    if (error.error === 'FileHasDependencies') {
      dependenciesToDelete.value = error;
      showDeleteDialog.value = false;
      showCascadeDialog.value = true;
    } else {
      toast.error(error?.message || error?.data?.detail || 'Failed to delete file');
      showDeleteDialog.value = false;
    }
  } finally {
    isDeleting.value = false;
  }
}

function handleCancelDelete() {
  showDeleteDialog.value = false;
  showCascadeDialog.value = false;
  fileToDelete.value = null;
  fileNameToDelete.value = '';
  dependenciesToDelete.value = null;
}

async function handleCascadeDelete() {
  await handleDelete(true);
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" @click="router.push('/data/sources')">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div>
          <h1 class="text-5xl font-bold tracking-tight">Uploaded Files</h1>
          <p class="text-muted-foreground mt-1">Manage CSV files for creating spreadsheet data sources</p>
        </div>
      </div>

      <UploadFilesDialog @filesUploaded="handleFilesUploaded" />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid gap-6 md:grid-cols-2">
      <Card v-for="i in 4" :key="i">
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex-1 space-y-2">
              <Skeleton class="h-5 w-3/4" />
              <Skeleton class="h-4 w-1/2" />
            </div>
          </div>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Skeleton class="h-4 w-full" />
            <Skeleton class="h-4 w-full" />
          </div>
          <div class="flex gap-2 pt-2">
            <Skeleton class="h-9 flex-1" />
            <Skeleton class="h-9 w-9" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Empty State -->
    <div v-else-if="uploadedFiles.length === 0" class="text-center py-12">
      <FileSpreadsheet class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No files uploaded yet</h3>
      <p class="text-muted-foreground mb-4">Upload CSV files to get started creating spreadsheet data sources</p>
      <UploadFilesDialog @filesUploaded="handleFilesUploaded" />
    </div>

    <!-- Files Grid -->
    <div v-else class="grid gap-6 md:grid-cols-2">
      <Card v-for="file in uploadedFiles" :key="file.id" class="hover:shadow-md transition-shadow">
        <CardHeader class="pb-3">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <CardTitle class="text-lg flex items-center gap-2 mb-1">
                <FileSpreadsheet class="w-5 h-5 text-muted-foreground" />
                {{ file.name }}
              </CardTitle>
              <p class="text-sm text-muted-foreground">
                {{ file.extension.toUpperCase() }} • {{ formatSize(file.size) }}
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent class="space-y-4">
          <!-- File Info -->
          <div class="space-y-2">
            <div class="text-sm">
              <span class="text-muted-foreground">MIME Type:</span>
              <span class="ml-2 font-medium">{{ file.mime_type || 'Unknown' }}</span>
            </div>
            <div class="text-sm">
              <span class="text-muted-foreground">Uploaded:</span>
              <span class="ml-2 font-medium">{{ formatDate(file.created_at) }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-2 pt-2">
            <Button
              size="sm"
              variant="outline"
              class="flex-1 cursor-pointer"
              @click="createDataSourceFromFile(file.id, file.name)"
            >
              <Database class="w-4 h-4 mr-2" />
              Create Data Source
            </Button>
            <Button
              size="sm"
              variant="outline"
              class="text-red-600 hover:text-red-700"
              @click="confirmDelete(file.id, `${file.name}.${file.extension}`)"
            >
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Initial Delete Confirmation Dialog -->
    <AlertDialog :open="showDeleteDialog" @update:open="(val) => !val && handleCancelDelete()">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle class="flex items-center gap-2">
            <AlertTriangle class="w-5 h-5 text-destructive" />
            Delete File
          </AlertDialogTitle>
          <AlertDialogDescription class="space-y-2">
            <p>
              Are you sure you want to delete the file "<strong>{{ fileNameToDelete }}</strong>"?
            </p>
            <p class="text-sm text-muted-foreground">
              This action cannot be undone.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <Button variant="destructive" @click="() => handleDelete(false)" :disabled="isDeleting">
            {{ isDeleting ? 'Deleting...' : 'Delete File' }}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>

    <!-- Cascade Delete Confirmation Dialog -->
    <AlertDialog :open="showCascadeDialog" @update:open="(val) => !val && handleCancelDelete()">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle class="flex items-center gap-2">
            <AlertTriangle class="w-5 h-5 text-destructive" />
            Caution
          </AlertDialogTitle>
          <AlertDialogDescription class="space-y-3">
            <p>
              The file "<strong>{{ fileNameToDelete }}</strong>" cannot be deleted because other entities depend on it.
            </p>

            <div v-if="dependenciesToDelete" class="p-3 bg-destructive/10 border border-destructive/30 rounded-md space-y-2">
              <p class="text-destructive font-medium">⚠️ The following will be permanently deleted:</p>

              <!-- Data Sources with nested Metrics -->
              <div class="text-sm text-destructive">
                <p class="font-semibold mb-1">
                  {{ dependenciesToDelete.dependencies.data_sources.length }}
                  data source{{ dependenciesToDelete.dependencies.data_sources.length !== 1 ? 's' : '' }}
                  ({{ dependenciesToDelete.dependencies.data_sources.reduce((sum, ds) => sum + ds.metrics.length, 0) }} metric{{ dependenciesToDelete.dependencies.data_sources.reduce((sum, ds) => sum + ds.metrics.length, 0) !== 1 ? 's' : '' }}):
                </p>
                <ul class="space-y-2">
                  <li v-for="ds in dependenciesToDelete.dependencies.data_sources" :key="ds.id" class="ml-4">
                    <div class="font-medium">
                      • <a
                          :href="`/data/sources/${ds.id}`"
                          target="_blank"
                          class="text-destructive hover:underline"
                        >
                          {{ ds.name }}{{ ds.alias ? ` (${ds.alias})` : '' }}
                        </a>
                      <span v-if="ds.metrics.length > 0" class="text-xs opacity-80">
                        - {{ ds.metrics.length }} metric{{ ds.metrics.length !== 1 ? 's' : '' }}
                      </span>
                    </div>
                    <!-- Nested Metrics -->
                    <ul v-if="ds.metrics.length > 0" class="ml-6 mt-1 space-y-1">
                      <li v-for="metric in ds.metrics" :key="metric.id" class="text-xs">
                        ↳ <a
                            :href="`/metrics/${metric.id}`"
                            target="_blank"
                            class="text-destructive hover:underline"
                          >
                            {{ metric.name }}{{ metric.alias ? ` (${metric.alias})` : '' }}
                          </a>
                        <span v-if="metric.version_count > 0" class="opacity-80">
                          - {{ metric.version_count }} version{{ metric.version_count !== 1 ? 's' : '' }}
                        </span>
                      </li>
                    </ul>
                  </li>
                </ul>
              </div>
            </div>

            <p class="text-sm font-medium">
              Do you want to delete the file and all its dependent data sources and metrics?
            </p>
            <p class="text-sm text-muted-foreground">This action cannot be undone.</p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel @click="handleCancelDelete">Cancel</AlertDialogCancel>
          <Button variant="destructive" @click="handleCascadeDelete" :disabled="isDeleting">
            {{ isDeleting ? 'Deleting...' : 'Delete All' }}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template>
