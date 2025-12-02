<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card'
import { Button } from '~/components/ui/button'
import { Badge } from '~/components/ui/badge'
import { Input } from '~/components/ui/input'
import { Label } from '~/components/ui/label'
import { Textarea } from '~/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '~/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs'
import { Separator } from '~/components/ui/separator'
import { Filter, Plus, MoreHorizontal, Edit, Settings, Users, UserPlus, ChevronDown, Loader2 } from 'lucide-vue-next'
import ExpandableSearch from '~/components/ExpandableSearch.vue'
import { toast } from 'vue-sonner'
import { useDateFormat, useTimeAgo, useNavigatorLanguage } from '@vueuse/core'

// Page metadata
definePageMeta({
  title: 'Consumers Management',
  layout: 'default'
})

// Use composables for data management
const { consumers, loading: consumersLoading, fetchConsumers, createConsumer, updateConsumer, deleteConsumer } = useConsumers()
const { consumerGroups, loading: groupsLoading, fetchConsumerGroups, createConsumerGroup, updateConsumerGroup, deleteConsumerGroup } = useConsumerGroups()

// Component state
const searchQuery = ref('')
const selectedStatus = ref<string | undefined>(undefined)

// Dialog states
const showCreateConsumerDialog = ref(false)
const showCreateGroupDialog = ref(false)
const isCreatingConsumer = ref(false)
const isCreatingGroup = ref(false)

// View state
const currentView = ref<'consumers' | 'groups'>('consumers')

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

// Computed properties
const filteredConsumers = computed(() => {
  if (!consumers.value || consumers.value.length === 0) return []
  
  return consumers.value.filter(consumer => {
    const matchesSearch = !searchQuery.value ||
      consumer.first_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      consumer.last_name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      consumer.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      consumer.organization?.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    return matchesSearch
  })
})

const filteredGroups = computed(() => {
  if (!consumerGroups.value || consumerGroups.value.length === 0) return []
  
  return consumerGroups.value.filter(group => {
    const matchesSearch = !searchQuery.value ||
      group.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      group.description?.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      group.alias?.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    return matchesSearch
  })
})

// Event handlers
const onViewChange = (view: string) => {
  currentView.value = view as 'consumers' | 'groups'
}

const onConsumerClick = (consumerId: string) => {
  navigateTo(`/consumers/${consumerId}`)
}

const onGroupClick = (groupId: string) => {
  navigateTo(`/consumers/groups/${groupId}`)
}

const onCreateConsumer = () => {
  showCreateConsumerDialog.value = true
}

const onCreateGroup = () => {
  showCreateGroupDialog.value = true
}

const onConsumerCreated = async (consumer: any) => {
  await fetchConsumers()
  toast.success('Consumer created successfully')
}

const onGroupCreated = async (group: any) => {
  await fetchConsumerGroups()
  toast.success('Consumer group created successfully')
}

// Initialize data
onMounted(() => {
  fetchConsumers()
  fetchConsumerGroups()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-5xl font-bold tracking-tight">Consumers</h1>
      </div>
      
      <div class="flex items-center gap-4">
        <!-- Search -->
        <ExpandableSearch
          v-model="searchQuery"
          :placeholder="['Search by name', 'Search by email', 'Search by organization']"
          default-mode="minimal"
          full-width="350px"
          :expand-on-focus="true"
          expand-to="full"
        />
        
        <!-- Create New Dropdown -->
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button>
              <Plus class="h-4 w-4 mr-2" />
              Add
              <ChevronDown class="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem @click="onCreateConsumer" class="cursor-pointer">
              <UserPlus class="h-4 w-4 mr-2" />
              Consumer
            </DropdownMenuItem>
            <DropdownMenuItem @click="onCreateGroup" class="cursor-pointer">
              <Users class="h-4 w-4 mr-2" />
              Consumer Group
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- View Toggle -->
    <Tabs :value="currentView" @update:value="onViewChange" default-value="consumers" class="w-full">
      <TabsList class="grid w-full grid-cols-2">
        <TabsTrigger value="consumers" class="flex items-center space-x-2">
          <UserPlus class="h-4 w-4" />
          <span>Consumers</span>
          <Badge variant="secondary" class="ml-2">{{ consumers?.length || 0 }}</Badge>
        </TabsTrigger>
        <TabsTrigger value="groups" class="flex items-center space-x-2">
          <Users class="h-4 w-4" />
          <span>Consumer Groups</span>
          <Badge variant="secondary" class="ml-2">{{ consumerGroups?.length || 0 }}</Badge>
        </TabsTrigger>
      </TabsList>

      <!-- Consumers View -->
      <TabsContent value="consumers" class="space-y-4">
        <div v-if="consumersLoading" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card v-for="i in 6" :key="i" class="animate-pulse">
            <CardHeader>
              <div class="h-4 bg-muted rounded w-3/4"></div>
              <div class="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <div class="h-3 bg-muted rounded"></div>
                <div class="h-3 bg-muted rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div v-else-if="!consumers || consumers.length === 0" class="text-center py-12">
          <UserPlus class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No consumers found</h3>
          <p class="text-muted-foreground mb-4">
            Create your first consumer to get started
          </p>
          <Button @click="onCreateConsumer">
            <Plus class="w-4 h-4 mr-2" />
            Add
          </Button>
        </div>

        <div v-else-if="filteredConsumers.length === 0" class="text-center py-12">
          <UserPlus class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No consumers match your filters</h3>
          <p class="text-muted-foreground mb-4">
            Try adjusting your search criteria
          </p>
          <Button variant="outline" @click="searchQuery = ''">
            Clear Filters
          </Button>
        </div>

        <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card 
            v-for="consumer in filteredConsumers" 
            :key="consumer.id" 
            class="cursor-pointer hover:shadow-md transition-shadow"
            @click="onConsumerClick(consumer.id)"
          >
            <CardHeader class="pb-3">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <CardTitle class="text-lg mb-1">
                    {{ consumer.first_name }} {{ consumer.last_name }}
                  </CardTitle>
                  <p class="text-sm text-muted-foreground">
                    {{ consumer.email }}
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child @click.stop>
                    <Button variant="ghost" size="icon" class="h-8 w-8">
                      <MoreHorizontal class="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem @click.stop="onConsumerClick(consumer.id)">
                      <Edit class="w-4 h-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem @click.stop>
                      <Settings class="w-4 h-4 mr-2" />
                      Settings
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            
            <CardContent class="pt-0">
              <div class="space-y-3">
                <div class="flex items-center gap-2">
                  <Badge variant="outline">Active</Badge>
                  <Badge v-if="consumer.organization" variant="secondary">
                    {{ consumer.organization }}
                  </Badge>
                </div>
                
                <div class="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Updated {{ formatRelativeTime(consumer.updated_at) }}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <!-- Groups View -->
      <TabsContent value="groups" class="space-y-4">
        <div v-if="groupsLoading" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card v-for="i in 6" :key="i" class="animate-pulse">
            <CardHeader>
              <div class="h-4 bg-muted rounded w-3/4"></div>
              <div class="h-3 bg-muted rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div class="space-y-2">
                <div class="h-3 bg-muted rounded"></div>
                <div class="h-3 bg-muted rounded w-2/3"></div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div v-else-if="!consumerGroups || consumerGroups.length === 0" class="text-center py-12">
          <Users class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No consumer groups found</h3>
          <p class="text-muted-foreground mb-4">
            Create your first consumer group to get started
          </p>
          <Button @click="onCreateGroup">
            <Plus class="w-4 h-4 mr-2" />
            Add
          </Button>
        </div>

        <div v-else-if="filteredGroups.length === 0" class="text-center py-12">
          <Users class="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">No groups match your filters</h3>
          <p class="text-muted-foreground mb-4">
            Try adjusting your search criteria
          </p>
          <Button variant="outline" @click="searchQuery = ''">
            Clear Filters
          </Button>
        </div>

        <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card 
            v-for="group in filteredGroups" 
            :key="group.id" 
            class="cursor-pointer hover:shadow-md transition-shadow"
            @click="onGroupClick(group.id)"
          >
            <CardHeader class="pb-3">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <CardTitle class="text-lg mb-1">{{ group.name }}</CardTitle>
                  <p v-if="group.description" class="text-sm text-muted-foreground line-clamp-2">
                    {{ group.description }}
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger as-child @click.stop>
                    <Button variant="ghost" size="icon" class="h-8 w-8">
                      <MoreHorizontal class="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem @click.stop="onGroupClick(group.id)">
                      <Edit class="w-4 h-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem @click.stop>
                      <Settings class="w-4 h-4 mr-2" />
                      Settings
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            
            <CardContent class="pt-0">
              <div class="space-y-3">
                <div class="flex items-center gap-2">
                  <Badge variant="outline">Active</Badge>
                  <Badge variant="secondary">
                    {{ group.consumers?.length || 0 }} members
                  </Badge>
                  <Badge v-if="group.alias" variant="outline">#{{ group.alias }}</Badge>
                </div>
                
                <div class="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Updated {{ formatRelativeTime(group.updated_at) }}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>

    <!-- Create Consumer Dialog -->
    <CreateConsumerDialog
      :open="showCreateConsumerDialog"
      @update:open="showCreateConsumerDialog = $event"
      @created="onConsumerCreated"
    />

    <!-- Create Group Dialog -->
    <CreateConsumerGroupDialog
      :open="showCreateGroupDialog"
      @update:open="showCreateGroupDialog = $event"
      @created="onGroupCreated"
    />
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 