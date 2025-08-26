# Chart Components

This directory contains individual chart wrapper components for the nuxt-charts library. Each component is designed to be a clean, type-safe wrapper around the corresponding nuxt-charts component.

## Components

### ChartSelector.vue
The main chart selector component that provides:
- Chart type selection (Bar, Line, Area, Donut)
- X-axis and Y-axis field selection
- Data validation and preparation
- Debug information display

### Individual Chart Components

#### LineChart.vue
Wrapper for `LineChart` with props:
- `data`: Array of data objects
- `height`: Chart height in pixels (required)
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `xFormatter`: Function that formats x-axis tick labels
- `yLabel`: Optional label for the y-axis
- `xNumTicks`, `yNumTicks`: Number of ticks on axes
- `curveType`: Type of curve for line charts
- `legendPosition`: Position of the legend
- `hideLegend`: If true, hides the chart legend
- `yGridLine`: If true, displays grid lines along the y-axis

#### BarChart.vue
Wrapper for `BarChart` with props:
- `data`: Array of data objects
- `height`: Chart height in pixels (required)
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `yAxis`: Array of property keys from the data object to be used for y-axis values (required)
- `xFormatter`: Function that formats x-axis tick labels (required)
- `yFormatter`: Optional function that formats y-axis tick labels
- `xNumTicks`: Number of ticks on x-axis
- `radius`: Corner radius of bars in pixels
- `yGridLine`: If true, displays grid lines along the y-axis
- `legendPosition`: Position of the legend
- `hideLegend`: If true, hides the chart legend

#### AreaChart.vue
Wrapper for `AreaChart` with similar props to LineChart (excluding curveType).

#### DonutChart.vue
Wrapper for `DonutChart` with props:
- `data`: Array of numeric values (required)
- `height`: Chart height in pixels (required)
- `radius`: Radius of the donut in pixels (required)
- `labels`: Array of objects with `name` and `color` properties (required)
- `type`: Type of donut chart to render (optional)
- `hideLegend`: If true, hides the chart legend (optional)

### Stacked Chart Components

#### StackedBarChart.vue
Wrapper for stacked bar charts with props similar to `BarChart`:
- `data`: Array of data objects
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `yAxis`: Array of property keys from the data object to be used for y-axis values
- `xFormatter`: Function that formats x-axis tick labels
- Automatically enables stacking with `stack: 'total'` in ECharts

#### StackedLineChart.vue
Wrapper for stacked line charts with props similar to `LineChart`:
- `data`: Array of data objects
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `xFormatter`: Function that formats x-axis tick labels
- Automatically enables stacking with `stack: 'total'` in ECharts
- Includes subtle area styling for better visual separation

#### NormalStackedArea.vue
Wrapper for stacked area charts with props similar to `AreaChart`:
- `data`: Array of data objects
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `xFormatter`: Function that formats x-axis tick labels
- Automatically enables stacking with `stack: 'total'` in ECharts
- Uses solid area styling for clear data representation

#### GradientStackedArea.vue
Wrapper for gradient stacked area charts with enhanced visual appeal:
- `data`: Array of data objects
- `categories`: Record mapping category keys to `BulletLegendItemInterface` objects
- `xFormatter`: Function that formats x-axis tick labels
- Automatically enables stacking with `stack: 'total'` in ECharts
- Includes gradient area styling from solid color to transparent for modern aesthetics

## Usage

### Basic Usage
```vue
<template>
  <ChartSelector :data="chartData" />
</template>

<script setup>
import { ChartSelector } from '@/components/charts'

const chartData = [
  { name: 'Category A', value: 100 },
  { name: 'Category B', value: 200 },
  { name: 'Category C', value: 150 }
]
</script>
```

### Individual Chart Usage
```vue
<template>
  <BarChart
    :data="chartData"
    :height="300"
    :categories="categories"
    :y-axis="['desktop']"
    :x-formatter="xFormatter"
    :y-formatter="yFormatter"
    :x-num-ticks="6"
    :radius="4"
    :y-grid-line="true"
    :legend-position="'top'"
    :hide-legend="false"
  />
</template>

<script setup>
import { BarChart } from '@/components/charts'

const chartData = [
  { month: 'January', desktop: 186, mobile: 80 },
  { month: 'February', desktop: 305, mobile: 200 },
  { month: 'March', desktop: 237, mobile: 120 }
]

const categories = {
  desktop: { name: 'Desktop', color: '#22c55e' }
}

const xFormatter = (i) => chartData[i].month
const yFormatter = (i) => i
</script>
```

### Donut Chart Usage
```vue
<template>
  <DonutChart
    :data="donutData.map((i) => i.value)"
    :height="275"
    :radius="0"
    :labels="donutData"
    :hide-legend="true"
  >
    <div class="absolute text-center">
      <div class="font-semibold">Label</div>
      <div class="text-muted">2 seconds ago</div>
    </div>
  </DonutChart>
</template>

<script setup>
import { DonutChart } from '@/components/charts'

const donutData = [
  {
    color: '#3b82f6',
    name: 'Blue',
    value: 50,
  },
  {
    color: '#a855f7',
    name: 'Gray',
    value: 20,
  },
  {
    color: '#22c55e',
    name: 'Green',
    value: 30,
  },
]
</script>
```

## Features

- **Type Safety**: All components use TypeScript interfaces for props
- **Default Values**: Sensible defaults for all optional props
- **Flexible Styling**: Support for custom colors, heights, and grid options
- **Data Validation**: Automatic detection of numeric fields for Y-axis
- **Responsive Design**: Built-in responsive behavior
- **Debug Information**: Optional debug panel for troubleshooting
- **Automatic Stacking**: ChartWidget.vue automatically selects stacked variants when `ChartConfig.stack_bars` is enabled
- **Seamless Integration**: Stacked charts work with existing data structures without requiring changes to backend processes

## Dependencies

- nuxt-charts (auto-imported)
- Vue 3 Composition API
- TypeScript
- Tailwind CSS (for styling) 