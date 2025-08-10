export interface Dashboard {
  id: string
  alias?: string
  environment_id: string
  name: string
  description?: string
  type: DashboardType
  views: DashboardView[]
  default_view: string
  tags?: string[]
  created_by: string
  created_at: string
  updated_at: string
  last_viewed_at?: string
}

export interface DashboardView {
  alias: string
  title: string
  description?: string
  sections: DashboardSection[]
  context_id?: string
  layout?: DashboardLayout
  created_at: string
  updated_at: string
}

export interface DashboardSection {
  alias: string
  title?: string
  description?: string
  position: number
  widgets: DashboardWidget[]
}

export interface DashboardWidget {
  alias: string
  section_alias: string
  metric_id: string
  position: number
  grid_config: WidgetGridConfig
  title: string
  description?: string
  visualization: VisualizationConfig
  metric_overrides?: MetricExecutionOverrides
}

export interface DashboardLayout {
  layout_type?: string
  frontend_config?: Record<string, any>
}

export interface WidgetGridConfig {
  columns: number
  rows: number
  min_columns?: number
  min_rows?: number
}

export interface VisualizationConfig {
  type: VisualizationType
  data_mapping: DataMapping
  single_value_config?: SingleValueConfig
  gauge_config?: GaugeConfig
  show_legend?: boolean
  show_grid?: boolean
  show_axes_labels?: boolean
  color_scheme?: ColorScheme
  custom_colors?: string[]
}

export interface DataMapping {
  x_axis: { field: string; type: string }
  y_axis: { field: string; type: string }
  series?: { split_by?: string; value_field?: string }
  category?: string
  value_field?: string
}

export interface SingleValueConfig {
  number_format: NumberFormat
  prefix?: string
  suffix?: string
  show_comparison?: boolean
  show_trend?: boolean
  trend_period?: string
  show_sparkline?: boolean
  show_title?: boolean
  show_description?: boolean
  compact_mode?: boolean
}

export interface GaugeConfig {
  min_value: number
  max_value: number
  target_value?: number
  color_ranges?: Array<{ min: number; max: number; color: string }>
  show_value?: boolean
  show_target?: boolean
  gauge_type?: string
  thickness?: number
}

export interface MetricExecutionOverrides {
  context_id?: string
  filters?: Record<string, any>
  parameters?: Record<string, any>
  limit?: number
}

export interface StandardChartData {
  raw: Record<string, any>
  processed: ProcessedChartData
  metadata: ChartMetadata
}

export interface ProcessedChartData {
  series?: ChartSeries[]
  categories?: CategoryData[]
  table?: TableData
  value?: any
  totals?: Record<string, number>
  averages?: Record<string, number>
}

export interface ChartSeries {
  name: string
  data: ChartDataPoint[]
  type?: string
  color?: string
  metadata?: Record<string, any>
}

export interface ChartDataPoint {
  x: any
  y: any
  label?: string
  category?: string
  metadata?: Record<string, any>
}

export interface CategoryData {
  name: string
  value: any
  percentage?: number
  color?: string
  metadata?: Record<string, any>
}

export interface TableData {
  columns: TableColumn[]
  rows: TableRow[]
  total_rows?: number
}

export interface TableColumn {
  name: string
  type: string
  format?: string
}

export interface TableRow {
  data: Record<string, any>
}

export interface ChartMetadata {
  title?: string
  description?: string
  x_axis_title?: string
  y_axis_title?: string
  data_types: Record<string, string>
  formatting: Record<string, string>
  ranges?: Record<string, number[]>
}

// Enums
export enum DashboardType {
  EXECUTIVE = 'executive',
  OPERATIONAL = 'operational',
  ANALYTICAL = 'analytical',
  TACTICAL = 'tactical'
}

export enum VisualizationType {
  SINGLE_VALUE = 'single_value',
  GAUGE = 'gauge',
  BAR_CHART = 'bar_chart',
  LINE_CHART = 'line_chart',
  AREA_CHART = 'area_chart',
  PIE_CHART = 'pie_chart',
  DONUT_CHART = 'donut_chart',
  SCATTER_PLOT = 'scatter_plot',
  HEATMAP = 'heatmap',
  TABLE = 'table'
}

export enum ColorScheme {
  DEFAULT = 'default',
  BLUE = 'blue',
  GREEN = 'green',
  RED = 'red',
  PURPLE = 'purple',
  ORANGE = 'orange',
  CATEGORICAL = 'categorical',
  SEQUENTIAL = 'sequential',
  DIVERGING = 'diverging'
}

export enum NumberFormat {
  INTEGER = 'integer',
  DECIMAL = 'decimal',
  PERCENTAGE = 'percentage',
  CURRENCY = 'currency',
  ABBREVIATED = 'abbreviated',
  SCIENTIFIC = 'scientific'
}