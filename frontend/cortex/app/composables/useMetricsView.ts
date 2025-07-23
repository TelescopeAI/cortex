import { ref, computed, watch } from 'vue'
import type { ModelFilters } from './useDataModels'
import type { MetricFilters } from './useMetrics'

export type ViewType = 'models' | 'metrics'

export const useMetricsView = () => {
  const route = useRoute()
  const router = useRouter()

  // Initialize view from URL query param or default to 'models'
  const currentView = ref<ViewType>((route.query.view as ViewType) || 'models')

  // Filter states
  const modelFilters = ref<ModelFilters>({
    search: '',
    dataSource: '',
    status: undefined,
    sortBy: 'updated',
    sortOrder: 'desc'
  })

  const metricFilters = ref<MetricFilters>({
    search: '',
    model: '',
    status: undefined,
    public: undefined,
    sortBy: 'updated',
    sortOrder: 'desc'
  })

  // Local storage key for user preferences
  const STORAGE_KEY = 'cortex_metrics_view_preferences'

  // Load preferences from localStorage
  const loadPreferences = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const preferences = JSON.parse(stored)
        if (preferences.defaultView && !route.query.view) {
          currentView.value = preferences.defaultView
        }
        if (preferences.modelFilters) {
          Object.assign(modelFilters.value, preferences.modelFilters)
        }
        if (preferences.metricFilters) {
          Object.assign(metricFilters.value, preferences.metricFilters)
        }
      }
    } catch (error) {
      console.warn('Failed to load metrics view preferences:', error)
    }
  }

  // Save preferences to localStorage
  const savePreferences = () => {
    try {
      const preferences = {
        defaultView: currentView.value,
        modelFilters: { ...modelFilters.value },
        metricFilters: { ...metricFilters.value }
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
    } catch (error) {
      console.warn('Failed to save metrics view preferences:', error)
    }
  }

  // Switch between views
  const switchView = (view: ViewType) => {
    currentView.value = view
    updateURL()
    savePreferences()
  }

  // Update URL with current view and filters
  const updateURL = () => {
    const query: Record<string, string> = {
      view: currentView.value
    }

    // Add relevant filters to URL based on current view
    if (currentView.value === 'models') {
      if (modelFilters.value.search) {
        query.search = modelFilters.value.search
      }
      if (modelFilters.value.dataSource) {
        query.dataSource = modelFilters.value.dataSource
      }
      if (modelFilters.value.status) {
        query.status = modelFilters.value.status
      }
    } else if (currentView.value === 'metrics') {
      if (metricFilters.value.search) {
        query.search = metricFilters.value.search
      }
      if (metricFilters.value.model) {
        query.model = metricFilters.value.model
      }
      if (metricFilters.value.status) {
        query.status = metricFilters.value.status
      }
      if (metricFilters.value.public !== undefined) {
        query.public = String(metricFilters.value.public)
      }
    }

    // Only update URL if query has changed to avoid unnecessary navigation
    const currentQuery = route.query
    const hasChanged = Object.keys(query).some(key => query[key] !== currentQuery[key]) ||
                     Object.keys(currentQuery).some(key => currentQuery[key] && !query[key])

    if (hasChanged) {
      router.replace({ query })
    }
  }

  // Sync URL changes back to local state
  const syncFromURL = () => {
    const query = route.query
    
    // Update view
    if (query.view && (query.view === 'models' || query.view === 'metrics')) {
      currentView.value = query.view
    }

    // Update filters based on current view
    if (currentView.value === 'models') {
      if (query.search) {
        modelFilters.value.search = String(query.search)
      }
      if (query.dataSource) {
        modelFilters.value.dataSource = String(query.dataSource)
      }
      if (query.status && ['valid', 'invalid', 'pending'].includes(String(query.status))) {
        modelFilters.value.status = String(query.status) as 'valid' | 'invalid' | 'pending'
      }
    } else if (currentView.value === 'metrics') {
      if (query.search) {
        metricFilters.value.search = String(query.search)
      }
      if (query.model) {
        metricFilters.value.model = String(query.model)
      }
      if (query.status && ['valid', 'invalid', 'pending'].includes(String(query.status))) {
        metricFilters.value.status = String(query.status) as 'valid' | 'invalid' | 'pending'
      }
      if (query.public !== undefined) {
        metricFilters.value.public = query.public === 'true'
      }
    }
  }

  // Reset filters for current view
  const resetFilters = () => {
    if (currentView.value === 'models') {
      modelFilters.value = {
        search: '',
        dataSource: '',
        status: undefined,
        sortBy: 'updated',
        sortOrder: 'desc'
      }
    } else if (currentView.value === 'metrics') {
      metricFilters.value = {
        search: '',
        model: '',
        status: undefined,
        public: undefined,
        sortBy: 'updated',
        sortOrder: 'desc'
      }
    }
    updateURL()
    savePreferences()
  }

  // Get active filters count for UI badges
  const activeFiltersCount = computed(() => {
    if (currentView.value === 'models') {
      let count = 0
      if (modelFilters.value.search) count++
      if (modelFilters.value.dataSource) count++
      if (modelFilters.value.status) count++
      return count
    } else if (currentView.value === 'metrics') {
      let count = 0
      if (metricFilters.value.search) count++
      if (metricFilters.value.model) count++
      if (metricFilters.value.status) count++
      if (metricFilters.value.public !== undefined) count++
      return count
    }
    return 0
  })

  // Watch for URL changes and sync
  watch(() => route.query, syncFromURL, { immediate: true })

  // Watch for filter changes and update URL
  watch([modelFilters, metricFilters], updateURL, { deep: true })

  // Initialize on mount
  onMounted(() => {
    loadPreferences()
    syncFromURL()
  })

  return {
    currentView: readonly(currentView),
    modelFilters,
    metricFilters,
    activeFiltersCount,
    switchView,
    resetFilters,
    updateURL,
    syncFromURL
  }
} 