// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: {
    enabled: true,

    timeline: {
      enabled: true
    }
  },
  modules: [
    'shadcn-nuxt',
    '@vueuse/nuxt',
    'nuxt-charts',
    'nuxt-shiki',
    'nuxt-echarts',
    '@nuxt/image'
  ],
  css: [
    './app/assets/css/tailwind.css',
    './app/assets/css/global.css'
  ],
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:9002'
    }
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  shadcn: {
    /**
     * Prefix for all the imported component
     */
    prefix: '',
    /**
     * Directory that the component lives in.
     * @default ".app//components/ui"
     */
    componentDir: './components/ui'
  },
  echarts: {
    /**
     * Chart types used in the application
     */
    charts: ['BarChart', 'LineChart', 'PieChart', 'GaugeChart', 'ScatterChart'],
    /**
     * Components used by charts
     */
    components: [
      'TitleComponent',
      'TooltipComponent', 
      'LegendComponent',
      'GridComponent',
      'DatasetComponent',
      'TransformComponent',
      'DataZoomComponent',
      'ToolboxComponent'
    ],
    /**
     * Features to include
     */
    features: ['LabelLayout', 'UniversalTransition']
  },
  shiki: {
    /**
     * Bundled languages to include
     */
    bundledLangs: ['sql', 'javascript', 'typescript', 'json', 'html', 'css'],
    /**
     * Default language
     */
    defaultLang: 'sql',
    /**
     * Bundled themes to include
     */
    bundledThemes: ['aurora-x', 'andromeeda', 'night-owl', 'one-light'],
    defaultTheme: 'one-light'
  },
  image: {
    dir: 'assets/images'
  },
})