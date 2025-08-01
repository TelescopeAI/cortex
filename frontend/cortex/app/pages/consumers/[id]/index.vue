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
import { ArrowLeft, Edit, Settings, Users, MoreHorizontal, Loader2, ArrowRight, Trash2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import EditConsumerDialog from '~/components/EditConsumerDialog.vue'
import AddConsumerToGroupDialog from '~/components/AddConsumerToGroupDialog.vue'
import PropertiesDisplay from '~/components/PropertiesDisplay.vue'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Consumer Details',
  layout: 'default'
})

// Get consumer ID from route
const route = useRoute()
const consumerId = route.params.id as string

// Use composables
const { getConsumer, updateConsumer, deleteConsumer } = useConsumers()
const { getEnvironment } = useEnvironments()
const { removeConsumerFromGroup } = useConsumerGroups()

// Component state
const consumer = ref<any>(null)
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
  if (consumer.value?.environment_id) {
    navigateTo(`/environments/${consumer.value.environment_id}`)
  }
}

const handleConsumerUpdated = (updatedConsumer: any) => {
  // Update the local consumer data with the updated data
  console.log('Consumer updated, new data:', updatedConsumer)
  consumer.value = { ...consumer.value, ...updatedConsumer }
  toast.success('Consumer updated successfully')
}

// Add to group dialog state
const showAddToGroupDialog = ref(false)

const onAddToGroup = () => {
  showAddToGroupDialog.value = true
}

const handleAddedToGroup = () => {
  // Refresh the consumer data to show the new group membership
  loadConsumer()
  toast.success('Consumer added to group successfully')
}

// Remove from group dialog state
const showRemoveFromGroupDialog = ref(false)
const groupToRemove = ref<any>(null)

const onRemoveFromGroup = (group: any) => {
  groupToRemove.value = group
  showRemoveFromGroupDialog.value = true
}

const handleRemovedFromGroup = async () => {
  if (!groupToRemove.value) return
  
  try {
    await removeConsumerFromGroup(groupToRemove.value.id, consumerId)
    // Refresh the consumer data to show the updated group membership
    loadConsumer()
    toast.success('Consumer removed from group successfully')
  } catch (error) {
    console.error('Failed to remove consumer from group:', error)
    toast.error('Failed to remove consumer from group')
  } finally {
    groupToRemove.value = null
  }
}

const onGroupClick = (groupId: string) => {
  navigateTo(`/consumers/groups/${groupId}`)
}

// Data loading
const loadConsumer = async () => {
  try {
    consumer.value = await getConsumer(consumerId)
    if (!consumer.value) {
      throw createError({
        statusCode: 404,
        statusMessage: 'Consumer not found'
      })
    }
  } catch (error) {
    console.error('Failed to load consumer:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Failed to load consumer'
    })
  }
}

const loadEnvironment = async () => {
  if (!consumer.value?.environment_id) return
  
  try {
    environment.value = await getEnvironment(consumer.value.environment_id)
  } catch (error) {
    console.error('Failed to load environment:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    await loadConsumer()
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
    <div v-else-if="consumer" class="space-y-6">
      <!-- Header -->
      <div class="flex flex-col space-y-4">
        <Button variant="ghost" size="sm" @click="onBack" class="w-fit">
          <ArrowLeft class="h-4 w-4 mr-2" />
          Back to Consumers
        </Button>
        
        <div class="flex flex-col gap-y-4 items-start justify-between">
          <div class="space-y-1">
            <h1 class="text-2xl font-semibold tracking-tight">
              {{ consumer.first_name }} {{ consumer.last_name }}
            </h1>
            <p class="text-sm text-muted-foreground">
              {{ consumer.email }}
            </p>
          </div>
          <div class="flex flex-col space-y-2">
            <EditConsumerDialog
              :consumer="consumer"
              @updated="handleConsumerUpdated"
            />
          </div>
        </div>
      </div>

      <!-- Main Content Tabs -->
      <Tabs default-value="overview" class="w-full">
        <TabsList class="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="groups">Groups</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <!-- Overview Tab -->
        <TabsContent value="overview" class="space-y-6">
          <!-- Basic Information -->
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
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

              <!-- Contact Information -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Email</div>
                  <div class="text-sm font-mono bg-muted p-2 rounded">{{ consumer.email }}</div>
                </div>
                <div v-if="consumer.organization" class="space-y-2">
                  <div class="text-sm font-medium text-muted-foreground">Organization</div>
                  <div class="text-sm bg-muted p-2 rounded">{{ consumer.organization }}</div>
                </div>
              </div>

              <!-- Properties -->
              <PropertiesDisplay 
                :properties="consumer.properties"
                :is-loading="loading"
              />

              <!-- Timestamps -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="space-y-1">
                  <div class="text-muted-foreground">Created</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(consumer.created_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(consumer.created_at) }}</div>
                  </div>
                </div>
                <div class="space-y-1">
                  <div class="text-muted-foreground">Last Updated</div>
                  <div class="space-y-1">
                    <div>{{ formatAbsoluteDate(consumer.updated_at) }}</div>
                    <div class="text-xs text-muted-foreground">{{ formatRelativeTime(consumer.updated_at) }}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Groups Tab -->
        <TabsContent value="groups" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Consumer Groups</CardTitle>
            </CardHeader>
            <CardContent>
              <div v-if="!consumer.groups || consumer.groups.length === 0" class="text-center py-8">
                <Users class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 class="text-lg font-medium text-muted-foreground mb-2">No groups found</h3>
                <p class="text-sm text-muted-foreground mb-4">
                  This consumer is not a member of any groups yet.
                </p>
                <Button variant="outline" @click="onAddToGroup">
                  <Users class="h-4 w-4 mr-2" />
                  Add to Group
                </Button>
              </div>
              
              <div v-else class="space-y-4">
                <div class="flex justify-between items-center">
                  <h3 class="text-lg font-medium">Member of {{ consumer.groups.length }} group{{ consumer.groups.length !== 1 ? 's' : '' }}</h3>
                  <Button variant="outline" @click="onAddToGroup">
                    <Users class="h-4 w-4 mr-2" />
                    Add to Group
                  </Button>
                </div>
                
                <div class="grid gap-4">
                  <div 
                    v-for="group in consumer.groups" 
                    :key="group.id" 
                    class="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div class="flex justify-between items-start">
                      <div 
                        class="space-y-1 flex-1 cursor-pointer"
                        @click="onGroupClick(group.id)"
                      >
                        <h4 class="font-medium">{{ group.name }}</h4>
                        <p v-if="group.description" class="text-sm text-muted-foreground">{{ group.description }}</p>
                      </div>
                      <div class="flex items-center space-x-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          @click="onGroupClick(group.id)"
                        >
                          <ArrowRight class="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          @click.stop="onRemoveFromGroup(group)"
                          class="text-destructive hover:text-destructive"
                        >
                          <Trash2 class="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
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
                  Activity history will appear here as the consumer interacts with the system.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>

    <!-- Error state -->
    <div v-else class="text-center py-12">
      <h3 class="text-lg font-medium text-muted-foreground mb-2">Consumer not found</h3>
      <p class="text-sm text-muted-foreground mb-4">
        The requested consumer could not be found or you don't have permission to view it.
      </p>
      <Button @click="onBack">
        <ArrowLeft class="h-4 w-4 mr-2" />
        Back to Consumers
      </Button>
    </div>

    <!-- Add to Group Dialog -->
    <AddConsumerToGroupDialog
      :open="showAddToGroupDialog"
      :consumer="consumer"
      @update:open="showAddToGroupDialog = $event"
      @added="handleAddedToGroup"
    />

    <!-- Remove from Group Alert Dialog -->
    <AlertDialog :open="showRemoveFromGroupDialog" @update:open="showRemoveFromGroupDialog = $event">
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Remove from Group</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to remove {{ consumer?.first_name }} {{ consumer?.last_name }} from 
            <strong>{{ groupToRemove?.name }}</strong>? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction @click="handleRemovedFromGroup">Remove</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </div>
</template> 