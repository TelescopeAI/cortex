<script setup lang="ts">
import { computed } from 'vue'
import { useChartTheme } from '~/composables/useChartTheme'
import { getShadcnTooltipConfig } from '~/config/echartShadCNTooltip'

interface ScatterProps {
  series: {
    name: string
    data: { x: number | string; y: number }[]
  }[]
  height?: number
  hideLegend?: boolean
  hideToolbar?: boolean
  xGridLine?: boolean
  yGridLine?: boolean
  dataZoom?: boolean
  legendPosition?: string
  xLabel?: string
  yLabel?: string
}

const props = withDefaults(defineProps<ScatterProps>(), {
  hideLegend: false,
  hideToolbar: true,
  xGridLine: false,
  yGridLine: false,
  dataZoom: true,
  legendPosition: 'top',
  xLabel: '',
  yLabel: ''
})

const { chartTheme } = useChartTheme()

const option = computed(() => ({
  tooltip: {
    ...getShadcnTooltipConfig({
      categorySize: props.series.reduce((acc, s) => acc + s.data.length, 0)
    }),
    trigger: 'item',
    axisPointer: {
      type: 'none'
    }
  },
  legend: {
    show: !props.hideLegend,
    [props.legendPosition]: 10,
    data: props.series.map(s => s.name)
  },
  xAxis: {
    type: 'category',
    name: props.xLabel,
    splitLine: {
      show: props.xGridLine
    }
  },
  yAxis: {
    type: 'value',
    name: props.yLabel,
    splitLine: {
      show: props.yGridLine
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: props.hideLegend ? '3%' : '15%',
    containLabel: true
  },
  toolbox: {
    show: !props.hideToolbar,
    feature: {
      dataZoom: {
        show: true,
        title: {
          zoom: 'Zoom',
          back: 'Reset Zoom'
        }
      },
      restore: {
        show: true,
        title: 'Restore'
      },
      saveAsImage: {
        show: true,
        title: 'Save as Image'
      }
    },
    right: '5%',
    top: '5%'
  },
  dataZoom: props.dataZoom ? [
    {
      type: 'inside',
      xAxisIndex: [0],
      filterMode: 'none'
    },
    {
      type: 'slider',
      xAxisIndex: [0],
      bottom: '5%',
      height: '12%',
      filterMode: 'none',
      show: false,
      showDetail: false,
      showDataShadow: true,
      handleSize: '110%',
      handleStyle: {
        color: '#fff',
        shadowBlur: 3,
        shadowColor: 'rgba(0,0,0,0.6)',
        shadowOffsetX: 2,
        shadowOffsetY: 2
      }
    }
  ] : undefined,
  series: props.series.map(s => ({ name: s.name, type: 'scatter', data: s.data.map(p => [p.x, p.y]) }))
}))
</script>

<template>
  <div class="h-full w-full">
    <VChart :option="option" :theme="chartTheme" autoresize class="h-full w-full min-h-[24rem]" />
  </div>
</template>


