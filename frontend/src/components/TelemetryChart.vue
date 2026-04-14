<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { init, use, graphic } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { ECharts } from 'echarts/core';
import type { Telemetry } from '../api';
import { useTheme } from '../composables/useTheme';

use([LineChart, GridComponent, TooltipComponent, TitleComponent, CanvasRenderer]);

const props = defineProps<{
  data: Telemetry[];
  title: string;
  field: 'temp' | 'humidity' | 'soil_moisture' | 'light'; // Restrict to valid numeric keys
  unit: string;
  color: string;
}>();

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: ECharts | null = null;
let resizeTimer: ReturnType<typeof setTimeout> | null = null;
const { effectiveTheme } = useTheme();

const readCssVar = (name: string, fallback: string) => {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return raw || fallback;
};

const getChartTokens = () => {
  return {
    titleColor: readCssVar('--chart-text', '#1f2f28'),
    axisColor: readCssVar('--chart-axis', '#617a6e'),
    gridColor: readCssVar('--chart-grid', 'rgba(38, 73, 57, 0.12)'),
    panelColor: readCssVar('--bg-card', '#ffffff'),
    tooltipBackground: readCssVar('--chart-tooltip-bg', 'rgba(251, 253, 252, 0.96)'),
    tooltipBorder: readCssVar('--chart-tooltip-border', 'rgba(45, 157, 120, 0.22)'),
  };
};

const handleResize = () => {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    chartInstance?.resize();
  }, 120);
};

const initChart = () => {
  if (chartContainer.value) {
    chartInstance = init(chartContainer.value);
    updateChart();
  }
};

const updateChart = () => {
  if (!chartInstance) return;
  const tokens = getChartTokens();

  // Process data: sort by timestamp ascending for chart
  const sortedData = [...props.data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  // Downsample large datasets to reduce chart rendering pressure
  const maxPoints = 500;
  const sampledData = sortedData.length > maxPoints
    ? sortedData.filter((_, idx) => idx % Math.ceil(sortedData.length / maxPoints) === 0)
    : sortedData;
  
  const dates = sampledData.map(item => {
    const d = new Date(item.timestamp);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
  });
  const values = sampledData.map(item => item[props.field]);

  const option = {
    backgroundColor: tokens.panelColor,
    animationDuration: 320,
    animationDurationUpdate: 240,
    title: { 
      text: props.title, 
      left: 'left',
      textStyle: { fontSize: 14, color: tokens.titleColor }
    },
    tooltip: { 
      trigger: 'axis',
      backgroundColor: tokens.tooltipBackground,
      borderColor: tokens.tooltipBorder,
      textStyle: { color: tokens.titleColor },
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
      data: dates,
      axisLine: { lineStyle: { color: tokens.gridColor } },
      axisLabel: { color: tokens.axisColor }
    },
    yAxis: { 
      type: 'value', 
      name: props.unit,
      nameTextStyle: { color: tokens.axisColor },
      axisLabel: { color: tokens.axisColor },
      splitLine: { show: true, lineStyle: { type: 'dashed', color: tokens.gridColor } }
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
        opacity: 0.2,
        color: new graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: props.color },
          { offset: 1, color: 'transparent' }
        ])
      }
    }]
  };
  
  chartInstance.setOption(option);
};

watch(() => props.data, updateChart, { deep: true });
watch(() => [props.title, props.field, props.unit, props.color], updateChart);
watch(effectiveTheme, updateChart);

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeTimer) clearTimeout(resizeTimer);
  chartInstance?.dispose();
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 300px;
  background: var(--bg-card);
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--shadow-soft);
  padding: 10px;
  border-radius: 12px;
}
</style>
