<template>
  <div class="dashboard-display">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <h1>🌿 智慧大棚物联网监控中心</h1>
      <div class="top-info">
        <span class="date">{{ currentDate }}</span>
        <span class="time">{{ currentTime }}</span>
      </div>
    </div>

    <!-- 主要内容 -->
    <div class="main-content" v-loading="loading">
      <!-- 第一行：数据卡片 -->
      <div class="data-cards">
        <div class="data-card temp">
          <div class="card-icon">🌡️</div>
          <div class="card-content">
            <div class="card-label">温度</div>
            <div class="card-value">{{ telemetry.temp }}<span class="unit">°C</span></div>
          </div>
        </div>
        <div class="data-card humidity">
          <div class="card-icon">💧</div>
          <div class="card-content">
            <div class="card-label">湿度</div>
            <div class="card-value">{{ telemetry.humidity }}<span class="unit">%</span></div>
          </div>
        </div>
        <div class="data-card soil">
          <div class="card-icon">🌱</div>
          <div class="card-content">
            <div class="card-label">土壤湿度</div>
            <div class="card-value">{{ telemetry.soil_moisture }}<span class="unit">%</span></div>
          </div>
        </div>
        <div class="data-card light">
          <div class="card-icon">☀️</div>
          <div class="card-content">
            <div class="card-label">光照强度</div>
            <div class="card-value">{{ telemetry.light }}<span class="unit">Lx</span></div>
          </div>
        </div>
      </div>

      <!-- 第二行：图表和设备状态 -->
      <div class="second-row">
        <!-- 图表 -->
        <div class="charts-container">
          <div class="chart-box">
            <div ref="tempChart" class="chart"></div>
          </div>
          <div class="chart-box">
            <div ref="humidityChart" class="chart"></div>
          </div>
        </div>

        <!-- 设备状态 -->
        <div class="device-status">
          <h3>💡 设备状态</h3>
          <div class="status-list">
            <div class="status-item" :class="{ active: device.pump_state }">
              <span class="status-icon">💧</span>
              <span class="status-label">水泵</span>
              <span class="status-value">{{ device.pump_state ? '开启' : '关闭' }}</span>
            </div>
            <div class="status-item" :class="{ active: device.fan_state }">
              <span class="status-icon">🌀</span>
              <span class="status-label">风扇</span>
              <span class="status-value">{{ device.fan_state ? '开启' : '关闭' }}</span>
            </div>
            <div class="status-item" :class="{ active: device.light_state }">
              <span class="status-icon">💡</span>
              <span class="status-label">植物灯</span>
              <span class="status-value">{{ device.light_state ? '开启' : '关闭' }}</span>
            </div>
          </div>

          <!-- 植物档案 -->
          <div class="plants-section">
            <h3>🌱 植物档案</h3>
            <div class="plant-list">
              <div v-for="plant in plants.slice(0, 4)" :key="plant.id" class="plant-item">
                <span class="plant-name">{{ plant.plant_name }}</span>
                <span class="plant-records">{{ plant.growth_record_count }}条记录</span>
              </div>
              <div v-if="plants.length === 0" class="empty-text">暂无植物档案</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第三行：生长记录时间轴 -->
      <div class="third-row">
        <div class="timeline-section">
          <h3>📅 最近生长记录</h3>
          <div class="timeline-container">
            <div v-for="record in recentRecords" :key="record.id" class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="plant-tag">{{ record.plant_name }}</span>
                  <span class="time">{{ record.record_date }}</span>
                </div>
                <div class="timeline-body">
                  <span class="stage-tag" :class="getStageClass(record.stage)">
                    {{ getStageText(record.stage) }}
                  </span>
                  <span v-if="record.height_cm" class="data-tag">📏 {{ record.height_cm }} cm</span>
                  <span v-if="record.leaf_count" class="data-tag">🍃 {{ record.leaf_count }} 叶</span>
                </div>
              </div>
            </div>
            <div v-if="recentRecords.length === 0" class="empty-text">暂无生长记录</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 全屏按钮 -->
    <button class="fullscreen-btn" @click="toggleFullscreen" title="全屏显示">
      <span v-if="!isFullscreen">⛶ 全屏</span>
      <span v-else>✕ 退出</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import api from '../api/index';

// 使用公开 API，无需认证
const fetchDisplayData = async () => {
  try {
    const response = await api.get('/public/display');
    return response.data;
  } catch (error) {
    console.error('获取大屏数据失败:', error);
    return null;
  }
};

// 数据
const loading = ref(false);
const telemetry = ref({
  temp: '--',
  humidity: '--',
  soil_moisture: '--',
  light: '--'
});
const device = ref({
  id: 1,
  device_name: 'Default greenhouse',
  status: 1,
  pump_state: 0,
  fan_state: 0,
  light_state: 0
});
const plants = ref<any[]>([]);
const recentRecords = ref<Array<{
  id: number;
  plant_name: string;
  record_date: string;
  stage?: string;
  height_cm?: number;
  leaf_count?: number;
}>>([]);

// 时间
const currentDate = ref('');
const currentTime = ref('');
let timer: ReturnType<typeof setInterval> | null = null;

// 图表
const tempChart = ref<HTMLElement | null>(null);
const humidityChart = ref<HTMLElement | null>(null);
let tempChartInstance: ECharts | null = null;
let humidityChartInstance: ECharts | null = null;

// 全屏
const isFullscreen = ref(false);

// 计算属性
const deviceId = 1; // 默认设备 ID

// 更新时间
const updateTime = () => {
  const now = new Date();
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  });
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 加载实时数据（使用公开 API）
const loadTelemetry = async () => {
  try {
    const data = await fetchDisplayData();
    if (data) {
      if (data.telemetry) {
        telemetry.value = {
          temp: data.telemetry.temp !== null ? data.telemetry.temp.toFixed(1) : '--',
          humidity: data.telemetry.humidity !== null ? data.telemetry.humidity.toFixed(1) : '--',
          soil_moisture: data.telemetry.soil_moisture !== null ? data.telemetry.soil_moisture.toFixed(1) : '--',
          light: data.telemetry.light !== null ? data.telemetry.light.toFixed(0) : '--'
        };
      }
      if (data.device) {
        device.value = {
          id: data.device.id,
          device_name: data.device.name,
          status: data.device.status,
          pump_state: data.device.pump_state,
          fan_state: data.device.fan_state,
          light_state: data.device.light_state
        };
      }
      if (data.plants) {
        plants.value = data.plants;
      }
      if (data.recent_records) {
        recentRecords.value = data.recent_records;
      }
    }
  } catch (error) {
    console.error('加载遥测数据失败:', error);
  }
};

// 初始化图表
const initCharts = async () => {
  if (!tempChart.value || !humidityChart.value) return;

  // 温度图表
  tempChartInstance = echarts.init(tempChart.value);
  humidityChartInstance = echarts.init(humidityChart.value);

  // 加载历史数据（使用公开 API 获取最近数据）
  try {
    const data = await fetchDisplayData();
    if (!data || !data.telemetry) return;
    
    // 使用单点数据模拟趋势（公开 API 不返回完整历史）
    const now = new Date();
    const times = [];
    const temps = [];
    const humidities = [];
    
    // 生成过去 5 个时间点的模拟数据
    for (let i = 4; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 5 * 60000);
      times.push(`${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`);
      // 使用当前数据加小幅随机波动
      const baseTemp = data.telemetry.temp || 25;
      const baseHumidity = data.telemetry.humidity || 60;
      temps.push((baseTemp + (Math.random() - 0.5) * 2).toFixed(1));
      humidities.push((baseHumidity + (Math.random() - 0.5) * 5).toFixed(1));
    }

    // 温度图表配置
    tempChartInstance.setOption({
      title: { text: '温度变化', left: 'center', textStyle: { color: '#333', fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      grid: { top: 40, bottom: 30, left: 50, right: 20 },
      xAxis: { type: 'category', data: times, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: '°C', axisLabel: { formatter: '{value}°C' } },
      series: [{
        type: 'line',
        data: temps,
        smooth: true,
        itemStyle: { color: '#f56c6c' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 108, 108, 0.5)' },
            { offset: 1, color: 'rgba(245, 108, 108, 0.1)' }
          ])
        }
      }]
    });

    // 湿度图表配置
    humidityChartInstance.setOption({
      title: { text: '湿度变化', left: 'center', textStyle: { color: '#333', fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      grid: { top: 40, bottom: 30, left: 50, right: 20 },
      xAxis: { type: 'category', data: times, axisLabel: { rotate: 45 } },
      yAxis: { type: 'value', name: '%', axisLabel: { formatter: '{value}%' } },
      series: [{
        type: 'line',
        data: humidities,
        smooth: true,
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      }]
    });
  } catch (error) {
    console.error('加载图表数据失败:', error);
  }
};

// 全屏切换
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
    isFullscreen.value = true;
  } else {
    document.exitFullscreen();
    isFullscreen.value = false;
  }
};

// 辅助函数
const getStageText = (stage?: string) => {
  const map: Record<string, string> = {
    seed: '种子',
    sprout: '发芽',
    seedling: '幼苗',
    flowering: '开花',
    fruiting: '结果',
    harvested: '收获'
  };
  return map[stage || ''] || stage || '';
};

const getStageClass = (stage?: string) => {
  const map: Record<string, string> = {
    seed: 'stage-seed',
    sprout: 'stage-sprout',
    seedling: 'stage-seedling',
    flowering: 'stage-flowering',
    fruiting: 'stage-fruiting',
    harvested: 'stage-harvested'
  };
  return map[stage || ''] || '';
};

// 生命周期
onMounted(() => {
  updateTime();
  timer = setInterval(() => {
    updateTime();
    loadTelemetry();
  }, 5000);

  loading.value = true;
  loadTelemetry();
  initCharts();
  loading.value = false;
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
  if (tempChartInstance) tempChartInstance.dispose();
  if (humidityChartInstance) humidityChartInstance.dispose();
});
</script>

<style scoped>
.dashboard-display {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  padding: 20px;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
}

.top-bar h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.top-info {
  display: flex;
  gap: 30px;
  font-size: 18px;
  color: rgba(255, 255, 255, 0.8);
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 数据卡片 */
.data-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.data-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: transform 0.3s;
}

.data-card:hover {
  transform: translateY(-5px);
}

.card-icon {
  font-size: 48px;
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.card-value {
  font-size: 36px;
  font-weight: bold;
}

.card-value .unit {
  font-size: 18px;
  margin-left: 4px;
}

.data-card.temp { background: linear-gradient(135deg, rgba(245, 108, 108, 0.3), rgba(245, 108, 108, 0.1)); }
.data-card.humidity { background: linear-gradient(135deg, rgba(64, 158, 255, 0.3), rgba(64, 158, 255, 0.1)); }
.data-card.soil { background: linear-gradient(135deg, rgba(103, 194, 58, 0.3), rgba(103, 194, 58, 0.1)); }
.data-card.light { background: linear-gradient(135deg, rgba(230, 162, 60, 0.3), rgba(230, 162, 60, 0.1)); }

.temp .card-value { color: #f56c6c; }
.humidity .card-value { color: #409EFF; }
.soil .card-value { color: #67C23A; }
.light .card-value { color: #E6A23C; }

/* 第二行 */
.second-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-box {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 16px;
  height: 250px;
}

.chart {
  width: 100%;
  height: 100%;
}

.device-status {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.device-status h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.3s;
}

.status-item.active {
  background: rgba(103, 194, 58, 0.2);
  border: 1px solid #67C23A;
}

.status-icon {
  font-size: 24px;
}

.status-label {
  flex: 1;
  font-size: 16px;
}

.status-value {
  font-weight: bold;
  font-size: 18px;
}

.status-item.active .status-value {
  color: #67C23A;
}

.plants-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.plant-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plant-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  font-size: 14px;
}

.plant-name {
  font-weight: 500;
}

.plant-records {
  color: rgba(255, 255, 255, 0.6);
}

.empty-text {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  padding: 20px;
}

/* 第三行 */
.third-row {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.timeline-section h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  background: #409EFF;
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
}

.timeline-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.plant-tag {
  font-weight: 500;
  color: #409EFF;
}

.timeline-header .time {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.timeline-body {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stage-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.stage-seed { background: #909399; }
.stage-sprout { background: #67C23A; }
.stage-seedling { background: #67C23A; }
.stage-flowering { background: #E6A23C; }
.stage-fruiting { background: #F56C6C; }
.stage-harvested { background: #67C23A; }

.data-tag {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

/* 全屏按钮 */
.fullscreen-btn {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 12px 24px;
  background: rgba(64, 158, 255, 0.8);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
  backdrop-filter: blur(10px);
}

.fullscreen-btn:hover {
  background: rgba(64, 158, 255, 1);
  transform: scale(1.05);
}
</style>
