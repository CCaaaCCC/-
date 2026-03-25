<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import type { Telemetry } from '../api';

const props = defineProps<{
  data: Telemetry[];
  title: string;
  field: 'temp' | 'humidity' | 'soil_moisture' | 'light'; // Restrict to valid numeric keys
  unit: string;
  color: string;
}>();

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const initChart = () => {
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value);
    updateChart();
  }
};

const updateChart = () => {
  if (!chartInstance) return;

  // Process data: sort by timestamp ascending for chart
  const sortedData = [...props.data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  
  const dates = sortedData.map(item => {
    const d = new Date(item.timestamp);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
  });
  const values = sortedData.map(item => item[props.field]);

  const option = {
    title: { 
      text: props.title, 
      left: 'left',
      textStyle: { fontSize: 14 }
    },
    tooltip: { 
      trigger: 'axis',
      formatter: function (params: any) {
        const param = params[0];
        return `${param.name}<br/>${param.marker}${props.title}: ${param.value} ${props.unit}`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: { 
      type: 'category', 
      boundaryGap: false,
      data: dates 
    },
    yAxis: { 
      type: 'value', 
      name: props.unit,
      splitLine: { show: true, lineStyle: { type: 'dashed' } }
    },
    series: [{
      name: props.title,
      data: values,
      type: 'line',
      smooth: true,
      showSymbol: false,
      itemStyle: { color: props.color },
      lineStyle: { width: 3 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: props.color },
          { offset: 1, color: 'rgba(255, 255, 255, 0)' }
        ])
      }
    }]
  };
  
  chartInstance.setOption(option);
};

watch(() => props.data, updateChart, { deep: true });

onMounted(() => {
  initChart();
  window.addEventListener('resize', () => chartInstance?.resize());
});

onUnmounted(() => {
  window.removeEventListener('resize', () => chartInstance?.resize());
  chartInstance?.dispose();
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 300px;
  background: #fff;
  padding: 10px;
  border-radius: 8px;
}
</style>
