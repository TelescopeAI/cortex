<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '~/components/ui/dialog';
import { FileSpreadsheet, Upload, Database, ArrowLeft } from 'lucide-vue-next';
import UploadFilesDialog from '~/components/UploadFilesDialog.vue';
import { useSpreadsheets } from '~/composables/useSpreadsheets';
import { useEnvironments } from '~/composables/useEnvironments';

const router = useRouter();
const { listUploadedFiles, loading } = useSpreadsheets();
const { selectedEnvironmentId } = useEnvironments();

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
  // Navigate to create data source with pre-filled file ID
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
    <div v-if="loading" class="text-center py-12">
      <p class="text-muted-foreground">Loading files...</p>
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
              class="flex-1"
              @click="createDataSourceFromFile(file.id, file.name)"
            >
              <Database class="w-4 h-4 mr-2" />
              Create Data Source
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
