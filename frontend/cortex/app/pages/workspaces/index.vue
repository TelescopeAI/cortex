<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useRouter } from 'vue-router';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from '~/components/ui/card';
import CreateWorkspaceDialog from '~/components/CreateWorkspaceDialog.vue';
import { Calendar } from 'lucide-vue-next';
import { Button } from '~/components/ui/button';

const { workspaces, loading, error, selectWorkspace } = useWorkspaces();
const router = useRouter();

function handleSelect(id: string) {
  selectWorkspace(id);
  router.push('/environments');
}
</script>

<template>
  <div class="p-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Workspaces</h1>
      <CreateWorkspaceDialog />
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">Error loading workspaces</div>
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="workspace in workspaces" :key="workspace.id" class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900">{{ workspace.name }}</h3>
              <p v-if="workspace.description" class="text-gray-600 mt-1">{{ workspace.description }}</p>
              <div class="flex items-center gap-2 mt-2 text-sm text-gray-500">
                <Calendar class="w-4 h-4" />
                <span>Created {{ new Date(workspace.created_at).toLocaleDateString() }}</span>
              </div>
            </div>
            <Button variant="outline" size="sm" @click="router.push(`/workspaces/${workspace.id}`)">
              View Details
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 