<script setup lang="ts">
import { ref, computed } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Separator } from '~/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '~/components/ui/table'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '~/components/ui/alert-dialog'
import { ArrowLeft, Edit, Settings, Users, MoreHorizontal, Loader2, UserPlus, Trash2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import EditConsumerGroupDialog from '~/components/EditConsumerGroupDialog.vue'
import AddMemberToGroupDialog from '~/components/AddMemberToGroupDialog.vue'
import PropertiesDisplay from '~/components/PropertiesDisplay.vue'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Consumer Group Details',
  layout: 'default'
})

// Get group ID from route
const route = useRoute()
const groupId = route.params.id as string

// Use composables
const { getConsumerGroup, updateConsumerGroup, deleteConsumerGroup, removeConsumerFromGroup } = useConsumerGroups()
const { getEnvironment } = useEnvironments()

// Component state
const group = ref<any>(null)
const environment = ref<any>(null)
const loading = ref(true)

// Get user's locale from browser
const { language } = useNavigatorLanguage()

// Helper function to convert UTC date string to local timezone
const convertUTCToLocal = (dateString: string): Date => {
  // Parse the UTC date string and convert to local timezone
  const utcDate = new Date(dateString)
  return new Date(utcDate.getTime() - (utcDate.getTimezoneOffset() * 60000))
}

// Format relative time using VueUse
const formatRelativeTime = (date: string | Date) => {
  // Convert UTC to local timezone before passing to useTimeAgo
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useTimeAgo(localDate, { 
    updateInterval: 1000 // Update every second for real-time updates
  })
}

// Format absolute date using VueUse
const formatAbsoluteDate = (date: string | Date) => {
  // Convert UTC to local timezone before passing to useDateFormat
  const localDate = typeof date === 'string' ? convertUTCToLocal(date) : date
  return useDateFormat(localDate, 'MMM D, YYYY', { 
    locales: language.value || 'en-US' 
  })
}

// Event handlers
const onBack = () => {
  navigateTo('/consumers')
}

const onEnvironmentClick = () => {
  if (group.value?.environment_id) {
    navigateTo(`/environments/${group.value.environment_id}`)
  }
}

const onConsumerClick = (consumerId: string) => {
  navigateTo(`/consumers/${consumerId}`)
}

const handleGroupUpdated = (updatedGroup: any) => {
  // Update the local group data with the updated data
  console.log('Group updated, new data:', updatedGroup)
  group.value = { ...group.value, ...updatedGroup }
  toast.success('Consumer group updated successfully')
}

// Add member dialog state
const showAddMemberDialog = ref(false)

const onAddMember = () => {
  showAddMemberDialog.value = true
}

const handleMemberAdded = () => {
  // Refresh the group data to show the new member
  loadGroup()
  toast.success('Member added to group successfully')
}

// Remove member dialog state
const showRemoveMemberDialog = ref(false)
const consumerToRemove = ref<any>(null)

const onRemoveMember = (consumer: any) => {
  consumerToRemove.value = consumer
  showRemoveMemberDialog.value = true
}

const handleRemovedMember = async () => {
  if (!consumerToRemove.value) return
  
  try {
    await removeConsumerFromGroup(groupId, consumerToRemove.value.id)
    // Refresh the group data to show the updated member list
    loadGroup()
    toast.success('Member removed from group successfully')
  } catch (error) {
    console.error('Failed to remove member from group:', error)
    toast.error('Failed to remove member from group')
  } finally {
    consumerToRemove.value = null
  }
}

// Data loading
const loadGroup = async () => {
  try {
    group.value = await getConsumerGroup(groupId)
    if (!group.value) {
      throw createError({
        statusCode: 404,
        statusMessage: 'Consumer group not found'
      })
    }
  } catch (error) {
    console.error('Failed to load consumer group:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to load consumer group'
    })
  }
}

const loadEnvironment = async () => {
  if (!group.value?.environment_id) return
  
  try {
    environment.value = await getEnvironment(group.value.environment_id)
  } catch (error) {
    console.error('Failed to load environment:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    await loadGroup()
    await loadEnvironment()
  } finally {
    loading.value = false
  }
}

// Initialize
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="container mx-auto py-6 space-y-6">
    <!-- Loading state -->
    <div v-if="loading" class="space-y-6">
      <div class="flex items-center space-x-4">
        <div class="h-8 w-8 bg-muted rounded animate-pulse"></div>
        <div class="h-8 w-64 bg-muted rounded animate-pulse"></div>
      </div>
      <Card>
        <CardContent class="pt-6">
          <div class="space-y-4 min-w-0">
            <div class="h-6 bg-muted rounded w-1/4 animate-pulse"></div>
            <div class="h-32 bg-muted rounded animate-pulse"></div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Content -->
    <div v-else-if="group" class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col space-y-4">
        <Button variant="ghost" size="sm" @click="onBack" class="w-fit">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Consumers
        </Button>
        
        <div class="flex flex-col gap-y-4 items-start justify-between">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight">
              👥 {{ group.name }}
            </h1>
            <p class="text-sm text-muted-foreground">
              {{ group.description || 'No description available' }}
            </p>
          </div>
          <div class="flex flex-col space-y-2">
            <EditConsumerGroupDialog
              :group="group"
              @updated="handleGroupUpdated"
            />
          </div>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="members">Members</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-6">
          <!-- Basic Information -->
          <Card>
            <CardHeader>
              <CardTitle>Group Information</CardTitle>
            </CardHeader>
            <CardContent class="space-y-6">
              <!-- Status and Environment -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Status</div>
                  <Badge variant="default">
                    ✅ Active
                  </Badge>
                </div>
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Environment</div>
                  <Button 
                    variant="link" 
                    class="p-0 h-auto text-sm justify-start"
                    @click="onEnvironmentClick"
                  >
                    🌍 {{ environment?.name || 'Unknown Environment' }}
                  </Button>
                </div>
              </div>

              <Separator />

              <!-- Group Details -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Name</div>
                  <div class="text-sm font-mono bg-muted p-2 rounded">{{ group.name }}</div>
                </div>
                <div v-if="group.alias" class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Alias</div>
                  <div class="text-sm font-mono bg-muted p-2 rounded">{{ group.alias }}</div>
                </div>
              </div>

              <!-- Description -->
              <div v-if="group.description" class="space-y-2">
                <div class="text-sm font-medium text-muted-foreground">Description</div>
                <p class="text-sm">{{ group.description }}</p>
              </div>

              <!-- Properties -->
              <PropertiesDisplay 
                :properties="group.properties"
                :is-loading="loading"
              />

              <!-- Timestamps -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="space-y-1">
                  <div class="text-muted-foreground">Created</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(group.created_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(group.created_at) }}</div>
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="text-muted-foreground">Last Updated</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(group.updated_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(group.updated_at) }}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Members Tab -->
        <TabsContent value="members" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Group Members</CardTitle>
            </CardHeader>
            <CardContent>
              <div v-if="!group.consumers || group.consumers.length === 0" class="text-center py-8">
                <Users class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No members found</h3>
                <p class="text-sm text-muted-foreground mb-4">
                  This group doesn't have any members yet. Add consumers to get started.
                </p>
                <Button @click="onAddMember">
                  <UserPlus class="h-4 w-4 mr-2" />
                  Add Member
                </Button>
              </div>
              
              <div v-else class="space-y-4">
                <div class="flex justify-between items-center">
                  <h3 class="text-lg font-medium">{{ group.consumers.length }} member{{ group.consumers.length !== 1 ? 's' : '' }}</h3>
                  <Button @click="onAddMember">
                    <UserPlus class="h-4 w-4 mr-2" />
                    Add Member
                  </Button>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Organization</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead class="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="consumer in group.consumers" :key="consumer.id" class="cursor-pointer" @click="onConsumerClick(consumer.id)">
                      <TableCell class="font-medium">{{ consumer.first_name }} {{ consumer.last_name }}</TableCell>
                      <TableCell class="text-muted-foreground">{{ consumer.email }}</TableCell>
                      <TableCell class="text-muted-foreground">{{ consumer.organization || 'N/A' }}</TableCell>
                      <TableCell>{{ formatRelativeTime(consumer.created_at) }}</TableCell>
                      <TableCell class="text-right">
                        <div class="flex items-center justify-end space-x-2">
                          <Button variant="ghost" size="sm" @click.stop="onConsumerClick(consumer.id)">
                            <MoreHorizontal class="h-4 w-4" />
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            @click.stop="onRemoveMember(consumer)"
                            class="text-destructive hover:text-destructive"
                          >
                            <Trash2 class="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Activity Tab -->
        <TabsContent value="activity" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="text-center py-8">
                <Settings class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No activity found</h3>
                <p class="text-sm text-muted-foreground mb-4">
                  Activity history will appear here as group members interact with the system.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>

    <!-- Error state -->
    <div v-else class="text-center py-12">
      <h3 class="text-lg font-medium text-muted-foreground mb-2">Consumer group not found</h3>
      <p class="text-sm text-muted-foreground mb-4">
        The requested consumer group could not be found or you don't have permission to view it.
      </p>
      <Button @click="onBack">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Consumers
      </Button>
    </div>

    <!-- Add Member Dialog -->
    <AddMemberToGroupDialog
      :open="showAddMemberDialog"
      :group-id="groupId"
      :group="group"
      @update:open="showAddMemberDialog = $event"
      @added="handleMemberAdded"
    />

    <!-- Remove Member Alert Dialog -->
    <AlertDialog :open="showRemoveMemberDialog" @update:open="showRemoveMemberDialog = $event">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove Member</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to remove <strong>{{ consumerToRemove?.first_name }} {{ consumerToRemove?.last_name }}</strong> 
            from <strong>{{ group?.name }}</strong>? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction @click="handleRemovedMember">Remove</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template> 