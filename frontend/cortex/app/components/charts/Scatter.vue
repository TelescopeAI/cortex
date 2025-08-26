<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ series: { name: string; data: { x: number | string; y: number }[] }[]; height?: number; dataZoom?: boolean }>()

const option = computed(() => ({
  tooltip: { trigger: 'item', formatter: (p:any) => `${p.seriesName}<br/>(${p.data[0]}, ${p.data[1]})` },
  xAxis: { type: 'category' },
  yAxis: { type: 'value' },
  grid: {
    left: '3%',
    right: '4%',
    bottom: props.dataZoom ? '20%' : '3%',
    top: '15%',
    containLabel: true
  },
  toolbox: {
    show: true,
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
    <VChart :option="option" autoresize class="h-full w-full min-h-[24rem]" />
  </div>
</template>


