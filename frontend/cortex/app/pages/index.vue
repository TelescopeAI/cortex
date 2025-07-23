<script setup lang="ts">
import { useWorkspaces } from '~/composables/useWorkspaces';
import { useEnvironments } from '~/composables/useEnvironments';

const { selectedWorkspaceId } = useWorkspaces();
const { selectedEnvironmentId } = useEnvironments();
const router = useRouter();

// Check if both workspace and environment are configured
if (!selectedWorkspaceId.value || !selectedEnvironmentId.value) {
  router.replace('/config/workspaces');
} else {
  router.replace('/workspaces');
}
</script>

<template>
  <div />
</template> 