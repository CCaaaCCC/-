<template>
  <div class="dashboard-container">
    <div class="header app-glass-card">
      <div class="header-left">
        <h2 class="app-page-title">大棚监控</h2>
        <el-tag :type="roleTagType">{{ userRoleText }}</el-tag>
        <el-tag :type="wsConnected ? 'success' : 'warning'" effect="dark">
          {{ wsConnected ? '实时已连接' : '实时重连中' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-select v-model="selectedDeviceId" class="device-select" placeholder="选择设备" @change="handleDeviceChange">
          <el-option
            v-for="device in devices"
            :key="device.id"
            :label="device.device_name"
            :value="device.id"
          />
        </el-select>
        <el-button class="action-btn" type="primary" plain @click="$router.push('/display')">📊 数据大屏</el-button>
        <el-button class="action-btn" type="info" plain @click="$router.push('/profile')">👤 个人中心</el-button>
        <el-button class="action-btn" type="success" plain @click="$router.push('/assignments')">📝 实验报告</el-button>
        <el-button class="action-btn" type="info" plain @click="$router.push('/plants')">🌱 植物档案</el-button>
        <el-button class="action-btn" type="success" plain @click="$router.push('/teaching')">📚 教学资源</el-button>
        <el-button class="action-btn" type="primary" plain @click="$router.push('/analytics')" v-if="canControl">📈 教学分析</el-button>
        <el-button class="action-btn" type="warning" plain @click="$router.push('/users')" v-if="userRole === 'admin'">👤 用户管理</el-button>
        <el-button class="action-btn" type="primary" plain @click="showExportDialog = true" :disabled="!selectedDeviceId">导出数据</el-button>
        <el-button class="action-btn" type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="导出数据"
      width="400px"
    >
      <el-form :model="exportForm" label-width="80px" label-position="left">
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="exportForm.startDate"
            type="date"
            placeholder="选择开始日期"
            style="width: 100%"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="exportForm.endDate"
            type="date"
            placeholder="选择结束日期"
            style="width: 100%"
            :disabled-date="disabledDate"
          />
        </el-form-item>
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="xlsx">Excel</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">导出</el-button>
      </template>
    </el-dialog>

    <el-alert
      v-if="!selectedDeviceId && devices.length > 0"
      title="请选择设备查看数据"
      type="info"
      show-icon
      class="mb-4"
    />

    <el-alert
      v-if="devices.length === 0"
      title="没有设备，请管理员创建"
      type="warning"
      show-icon
      class="mb-4"
    />

    <el-alert
      v-if="fetchErrorDetail"
      :title="fetchErrorDetail"
      type="error"
      show-icon
      class="mb-4"
    />

    <div v-if="selectedDeviceId" class="content">
      <!-- Status Cards -->
      <div class="cards-grid">
        <div
          v-for="card in sensorCards"
          :key="card.key"
          class="sensor-card app-glass-card"
          :style="{ '--strip-color': card.stripColor }"
        >
          <div class="sensor-card-header">
            <div class="sensor-label">
              <component :is="card.icon" :class="['icon', card.iconClass]" />
              <span>{{ card.label }}</span>
            </div>
            <el-tag size="small" :type="card.tagType" effect="light">{{ card.statusText }}</el-tag>
          </div>

          <el-skeleton v-if="dataLoading && !latestReading" animated :rows="1" />

          <div
            v-else
            class="sensor-value-wrap"
            :class="{ 'is-pulse': pulseFlags[card.key] }"
          >
            <span class="sensor-value">{{ card.value }}</span>
            <span class="sensor-unit">{{ card.unit }}</span>
          </div>
        </div>
      </div>

      <div class="role-panels">
        <el-card class="ai-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>AI 科学助手（Qwen）</span>
              <el-tag size="small" type="info">STEAM</el-tag>
            </div>
          </template>
          <div class="ai-input-row">
            <el-input
              v-model="aiQuestion"
              placeholder="例如：为什么现在土壤湿度低，植物叶片会下垂？"
              @keyup.enter="askAI"
            />
            <el-button type="primary" :loading="aiLoading" @click="askAI">提问</el-button>
          </div>
          <div class="ai-answer" v-if="aiAnswer">
            {{ aiAnswer }}
          </div>
          <div class="ai-hint" v-else>
            你可以基于当前实时数据提问，AI 会给出中小学生可理解的解释和建议。
          </div>
        </el-card>

        <el-card v-if="isStudent" class="student-missions" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>今日探究任务</span>
              <el-tag type="success" size="small">闯关模式</el-tag>
            </div>
          </template>
          <div class="mission-item" v-for="m in studentMissions" :key="m.title">
            <div>
              <div class="mission-title">{{ m.title }}</div>
              <div class="mission-desc">{{ m.desc }}</div>
            </div>
            <el-tag :type="m.done ? 'success' : 'warning'">{{ m.done ? '已完成' : '待完成' }}</el-tag>
          </div>
        </el-card>

        <el-card v-else class="teacher-panel" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>教师诊断提示</span>
              <el-tag type="warning" size="small">班级视图</el-tag>
            </div>
          </template>
          <div class="teacher-tip" v-for="tip in teacherTips" :key="tip">• {{ tip }}</div>
        </el-card>
      </div>

      <el-card v-if="canControl" class="demo-scene-card mb-4" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>课堂演示一键场景</span>
            <el-tag size="small" type="danger">答辩快捷</el-tag>
          </div>
        </template>
        <div class="demo-btns">
          <el-button :loading="scenarioLoading === 'drought'" @click="runScenario('drought')">干旱胁迫</el-button>
          <el-button :loading="scenarioLoading === 'heatwave'" @click="runScenario('heatwave')">高温应激</el-button>
          <el-button :loading="scenarioLoading === 'low_light'" @click="runScenario('low_light')">低光照</el-button>
          <el-button type="success" :loading="scenarioLoading === 'healthy'" @click="runScenario('healthy')">恢复健康态</el-button>
        </div>
      </el-card>

      <!-- Control Card (Teacher/Admin Only) -->
      <el-card v-if="canControl" class="control-card mb-4" shadow="hover" header="远程控制">
        <div class="control-grid">
          <div class="control-item">
            <span>水泵</span>
            <el-switch
              v-model="pumpActive"
              @change="onPumpChange"
              active-color="#13ce66" />
          </div>
          <div class="control-item">
            <span>排风扇</span>
            <el-switch
              v-model="fanActive"
              @change="onFanChange"
              active-color="#409EFF" />
          </div>
          <div class="control-item">
            <span>植物灯</span>
            <el-switch
              v-model="lightActive"
              @change="onLightChange"
              active-color="#E6A23C" />
          </div>
        </div>
      </el-card>

      <!-- Charts -->
      <div class="charts-grid">
        <TelemetryChart
          :data="history"
          title="温度历史"
          field="temp"
          unit="°C"
          color="#ff7c7c"
        />
        <TelemetryChart
          :data="history"
          title="湿度历史"
          field="humidity"
          unit="%"
          color="#409EFF"
        />
        <TelemetryChart
          :data="history"
          title="土壤湿度历史"
          field="soil_moisture"
          unit="%"
          color="#67C23A"
        />
        <TelemetryChart
          :data="history"
          title="光照历史"
          field="light"
          unit="Lx"
          color="#E6A23C"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import {
  getDevices,
  getHistory,
  controlDevice,
  exportTelemetry,
  askScienceAssistant,
  triggerDemoScenario,
  createTelemetrySocket,
  type DemoScenario,
  type Device,
  type Telemetry,
  type TelemetryRealtimePayload
} from '../api';
import TelemetryChart from './TelemetryChart.vue';
import { Thermometer, Droplets, Sprout, Sun } from 'lucide-vue-next';
import { ElMessage } from 'element-plus';

type MetricKey = 'temp' | 'humidity' | 'soil_moisture' | 'light';

type MetricStatus = {
  statusText: string;
  tagType: 'success' | 'warning' | 'danger' | 'info';
  stripColor: string;
};

const router = useRouter();
const devices = ref<Device[]>([]);
const selectedDeviceId = ref<number | null>(null);
const history = ref<Telemetry[]>([]);
const dataLoading = ref(false);
const userRole = ref(localStorage.getItem('role') || 'student');
let timer: ReturnType<typeof setInterval> | null = null;
let ws: WebSocket | null = null;
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null;
const wsConnected = ref(false);
const fetchErrorDetail = ref('');
const pulseFlags = ref<Record<MetricKey, boolean>>({
  temp: false,
  humidity: false,
  soil_moisture: false,
  light: false
});
const pulseTimers: Partial<Record<MetricKey, ReturnType<typeof setTimeout>>> = {};

// Control States
const pumpActive = ref(false);
const fanActive = ref(false);
const lightActive = ref(false);

const aiQuestion = ref('为什么现在的环境会影响植物生长？');
const aiAnswer = ref('');
const aiLoading = ref(false);
const scenarioLoading = ref<DemoScenario | ''>('');

// Export States
const showExportDialog = ref(false);
const exporting = ref(false);
const exportForm = ref({
  startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 默认 7 天前
  endDate: new Date(),
  format: 'csv' as 'csv' | 'xlsx'
});

const toLocalDateString = (date: Date) => {
  const y = date.getFullYear();
  const m = `${date.getMonth() + 1}`.padStart(2, '0');
  const d = `${date.getDate()}`.padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const disabledDate = (date: Date) => {
  // 不能选择超过 31 天前的日期，也不能选择未来日期
  const thirtyOneDaysAgo = new Date();
  thirtyOneDaysAgo.setDate(thirtyOneDaysAgo.getDate() - 31);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return date < thirtyOneDaysAgo || date >= tomorrow;
};

const roleTagType = computed(() => {
  if (userRole.value === 'admin') return 'danger';
  if (userRole.value === 'teacher') return 'warning';
  return 'success';
});

const userRoleText = computed(() => {
  if (userRole.value === 'admin') return '管理员';
  if (userRole.value === 'teacher') return '教师';
  return '学生';
});

const canControl = computed(() => {
  return ['teacher', 'admin'].includes(userRole.value);
});

const isStudent = computed(() => userRole.value === 'student');

const studentMissions = computed(() => {
  const soil = Number(latest.value.soil_moisture);
  const light = Number(latest.value.light);
  const temp = Number(latest.value.temp);
  return [
    {
      title: '任务1：判断是否需要浇水',
      desc: '观察土壤湿度是否低于 25%',
      done: !Number.isNaN(soil) && soil < 25
    },
    {
      title: '任务2：分析光合作用条件',
      desc: '观察光照是否达到 3000Lx 以上',
      done: !Number.isNaN(light) && light >= 3000
    },
    {
      title: '任务3：温度舒适度判断',
      desc: '目标温度区间 18-30°C',
      done: !Number.isNaN(temp) && temp >= 18 && temp <= 30
    }
  ];
});

const teacherTips = computed(() => {
  const tips: string[] = [];
  const soil = Number(latest.value.soil_moisture);
  const temp = Number(latest.value.temp);
  if (!Number.isNaN(soil) && soil < 20) tips.push('土壤湿度偏低，建议组织学生进行“蒸腾与补水”观察实验。');
  if (!Number.isNaN(temp) && temp > 32) tips.push('温度偏高，可开启风扇并引导学生讨论温度对酶活性的影响。');
  if (tips.length === 0) tips.push('当前环境稳定，适合布置连续观察记录任务。');
  return tips;
});

const latest = computed(() => {
  if (history.value.length === 0) {
    return { temp: '--', humidity: '--', soil_moisture: '--', light: '--' };
  }
  const last = history.value[0]; 
  return {
    temp: last.temp.toFixed(1),
    humidity: last.humidity.toFixed(1),
    soil_moisture: last.soil_moisture.toFixed(1),
    light: last.light.toFixed(0)
  };
});

const latestReading = computed<Telemetry | null>(() => {
  return history.value.length > 0 ? history.value[0] : null;
});

const statusTemp = (value: number | null): MetricStatus => {
  if (value === null) return { statusText: '等待数据', tagType: 'info', stripColor: 'var(--el-color-info)' };
  if (value > 35 || value < 12) return { statusText: '异常 ⚠️', tagType: 'danger', stripColor: 'var(--el-color-danger)' };
  if (value >= 20 && value <= 30) return { statusText: '舒适', tagType: 'success', stripColor: 'var(--el-color-success)' };
  return { statusText: '轻微偏离', tagType: 'warning', stripColor: 'var(--el-color-danger)' };
};

const statusHumidity = (value: number | null): MetricStatus => {
  if (value === null) return { statusText: '等待数据', tagType: 'info', stripColor: 'var(--el-color-info)' };
  if (value < 25 || value > 90) return { statusText: '异常 ⚠️', tagType: 'danger', stripColor: 'var(--el-color-danger)' };
  if (value >= 45 && value <= 75) return { statusText: '正常', tagType: 'success', stripColor: 'var(--el-color-success)' };
  return { statusText: '需关注', tagType: 'warning', stripColor: 'var(--el-color-danger)' };
};

const statusSoil = (value: number | null): MetricStatus => {
  if (value === null) return { statusText: '等待数据', tagType: 'info', stripColor: 'var(--el-color-info)' };
  if (value < 20) return { statusText: '偏干 ⚠️', tagType: 'danger', stripColor: 'var(--el-color-danger)' };
  if (value > 85) return { statusText: '过湿 ⚠️', tagType: 'danger', stripColor: 'var(--el-color-danger)' };
  if (value >= 30 && value <= 70) return { statusText: '适宜', tagType: 'success', stripColor: 'var(--el-color-success)' };
  return { statusText: '波动中', tagType: 'warning', stripColor: 'var(--el-color-danger)' };
};

const statusLight = (value: number | null): MetricStatus => {
  if (value === null) return { statusText: '等待数据', tagType: 'info', stripColor: 'var(--el-color-info)' };
  if (value < 800 || value > 25000) return { statusText: '异常 ⚠️', tagType: 'danger', stripColor: 'var(--el-color-danger)' };
  if (value >= 3000 && value <= 15000) return { statusText: '充足', tagType: 'success', stripColor: 'var(--el-color-success)' };
  return { statusText: '偏弱/偏强', tagType: 'warning', stripColor: 'var(--el-color-danger)' };
};

const sensorCards = computed(() => {
  const row = latestReading.value;
  const temp = row?.temp ?? null;
  const humidity = row?.humidity ?? null;
  const soil = row?.soil_moisture ?? null;
  const light = row?.light ?? null;

  return [
    {
      key: 'temp' as const,
      icon: Thermometer,
      iconClass: 'temp-icon',
      label: '温度',
      value: temp === null ? '--' : temp.toFixed(1),
      unit: '°C',
      ...statusTemp(temp)
    },
    {
      key: 'humidity' as const,
      icon: Droplets,
      iconClass: 'humidity-icon',
      label: '空气湿度',
      value: humidity === null ? '--' : humidity.toFixed(1),
      unit: '%',
      ...statusHumidity(humidity)
    },
    {
      key: 'soil_moisture' as const,
      icon: Sprout,
      iconClass: 'soil-icon',
      label: '土壤湿度',
      value: soil === null ? '--' : soil.toFixed(1),
      unit: '%',
      ...statusSoil(soil)
    },
    {
      key: 'light' as const,
      icon: Sun,
      iconClass: 'light-icon',
      label: '光照强度',
      value: light === null ? '--' : light.toFixed(0),
      unit: 'Lx',
      ...statusLight(light)
    }
  ];
});

const triggerValuePulse = (key: MetricKey) => {
  if (pulseTimers[key]) {
    clearTimeout(pulseTimers[key]);
  }
  pulseFlags.value[key] = false;
  requestAnimationFrame(() => {
    pulseFlags.value[key] = true;
    pulseTimers[key] = setTimeout(() => {
      pulseFlags.value[key] = false;
    }, 220);
  });
};

const hasValueChanged = (prev: Telemetry | undefined, next: Telemetry, key: MetricKey) => {
  if (!prev) return false;
  const prevValue = prev[key];
  const nextValue = next[key];
  const epsilon = key === 'light' ? 1 : 0.05;
  return Math.abs(Number(prevValue) - Number(nextValue)) >= epsilon;
};

const fetchData = async () => {
  if (!selectedDeviceId.value) return;
  dataLoading.value = true;
  fetchErrorDetail.value = '';
  try {
    history.value = await getHistory(selectedDeviceId.value);
  } catch (error: any) {
    fetchErrorDetail.value = error.response?.data?.detail || '实时数据加载失败，请稍后重试';
  } finally {
    dataLoading.value = false;
  }
};

const applyRealtimePayload = (payload: TelemetryRealtimePayload) => {
  if (!payload.telemetry) return;
  const previous = history.value[0];
  const telemetry = payload.telemetry;
  const realtime: Telemetry = {
    id: Date.now(),
    device_id: payload.device_id,
    temp: telemetry.temp ?? 0,
    humidity: telemetry.humidity ?? 0,
    soil_moisture: telemetry.soil_moisture ?? 0,
    light: telemetry.light ?? 0,
    timestamp: payload.timestamp || new Date().toISOString()
  };
  history.value = [realtime, ...history.value].slice(0, 200);
  if (hasValueChanged(previous, realtime, 'temp')) triggerValuePulse('temp');
  if (hasValueChanged(previous, realtime, 'humidity')) triggerValuePulse('humidity');
  if (hasValueChanged(previous, realtime, 'soil_moisture')) triggerValuePulse('soil_moisture');
  if (hasValueChanged(previous, realtime, 'light')) triggerValuePulse('light');
  pumpActive.value = payload.actuators.pump_state === 1;
  fanActive.value = payload.actuators.fan_state === 1;
  lightActive.value = payload.actuators.light_state === 1;
};

const clearWs = () => {
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
  wsConnected.value = false;
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer);
    wsReconnectTimer = null;
  }
};

const connectRealtime = () => {
  if (!selectedDeviceId.value) return;
  clearWs();
  ws = createTelemetrySocket(
    selectedDeviceId.value,
    (payload) => {
      wsConnected.value = true;
      applyRealtimePayload(payload);
    },
    () => {
      wsConnected.value = false;
      wsReconnectTimer = setTimeout(connectRealtime, 2000);
    }
  );
  ws.onopen = () => {
    wsConnected.value = true;
  };
};

const askAI = async () => {
  if (!aiQuestion.value.trim()) {
    ElMessage.warning('请先输入问题');
    return;
  }
  aiLoading.value = true;
  try {
    const res = await askScienceAssistant({
      question: aiQuestion.value.trim(),
      device_id: selectedDeviceId.value || undefined
    });
    aiAnswer.value = res.answer;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'AI 助手暂时不可用');
  } finally {
    aiLoading.value = false;
  }
};

const runScenario = async (scenario: DemoScenario) => {
  if (!selectedDeviceId.value) {
    ElMessage.warning('请先选择设备');
    return;
  }
  scenarioLoading.value = scenario;
  try {
    const res = await triggerDemoScenario(selectedDeviceId.value, scenario);
    ElMessage.success(res.message || '场景切换成功');
    await fetchData();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '场景切换失败');
  } finally {
    scenarioLoading.value = '';
  }
};

const fetchDevices = async () => {
  try {
    devices.value = await getDevices();
    if (devices.value.length > 0) {
      selectedDeviceId.value = devices.value[0].id;
      // Initialize control states from device data if available
      const dev = devices.value[0];
      pumpActive.value = dev.pump_state === 1;
      fanActive.value = dev.fan_state === 1;
      lightActive.value = dev.light_state === 1;
      fetchData();
      connectRealtime();
    } else {
      selectedDeviceId.value = null;
      clearWs();
    }
  } catch (error) {
    console.error("Failed to fetch devices", error);
  }
};

const handleDeviceChange = () => {
  history.value = [];
  fetchData();
  // Update control states for new device
  const dev = devices.value.find(d => d.id === selectedDeviceId.value);
  if (dev) {
    pumpActive.value = dev.pump_state === 1;
    fanActive.value = dev.fan_state === 1;
    lightActive.value = dev.light_state === 1;
  }
  connectRealtime();
};

const handleControlChange = async (type: string, newValue: boolean) => {
  if (!selectedDeviceId.value) return;

  // 保存旧状态
  const pumpOld = pumpActive.value;
  const fanOld = fanActive.value;
  const lightOld = lightActive.value;

  // 更新当前状态
  if (type === 'pump') pumpActive.value = newValue;
  else if (type === 'fan') fanActive.value = newValue;
  else if (type === 'light') lightActive.value = newValue;

  try {
    await controlDevice(selectedDeviceId.value, {
      pump_state: pumpActive.value ? 1 : 0,
      fan_state: fanActive.value ? 1 : 0,
      light_state: lightActive.value ? 1 : 0
    });
    // 成功后刷新 devices
    await fetchDevices();
    ElMessage.success('控制成功');
  } catch (error: any) {
    // 恢复旧状态
    pumpActive.value = pumpOld;
    fanActive.value = fanOld;
    lightActive.value = lightOld;
    ElMessage.error('控制失败，已恢复');
  }
};

const onPumpChange = (val: string | number | boolean) => {
  handleControlChange('pump', Boolean(val));
};

const onFanChange = (val: string | number | boolean) => {
  handleControlChange('fan', Boolean(val));
};

const onLightChange = (val: string | number | boolean) => {
  handleControlChange('light', Boolean(val));
};

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  clearWs();
  if (timer) clearInterval(timer);
  router.push('/login');
};

const handleExport = async () => {
  if (!selectedDeviceId.value) {
    ElMessage.warning('请选择设备');
    return;
  }

  if (exportForm.value.startDate > exportForm.value.endDate) {
    ElMessage.warning('开始日期不能晚于结束日期');
    return;
  }

  exporting.value = true;
  try {
    // 格式化日期为 YYYY-MM-DD
    const startDate = toLocalDateString(exportForm.value.startDate);
    const endDate = toLocalDateString(exportForm.value.endDate);

    // 调用导出 API
    const blob = await exportTelemetry(
      selectedDeviceId.value,
      startDate,
      endDate,
      exportForm.value.format
    );

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    link.download = `传感器数据_${selectedDeviceId.value}_${timestamp}.${exportForm.value.format === 'xlsx' ? 'xlsx' : 'csv'}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    ElMessage.success('导出成功');
    showExportDialog.value = false;
  } catch (error: any) {
    console.error('Export error:', error);
    // 从后端响应中获取详细错误信息
    const detail = error.response?.data?.detail;
    if (error.response?.status === 404) {
      ElMessage.error(detail || '所选日期范围内没有数据');
    } else if (error.response?.status === 400) {
      ElMessage.error(detail || '请求参数错误');
    } else if (error.response?.status === 403) {
      ElMessage.error(detail || '没有权限导出该设备数据');
    } else {
      ElMessage.error(detail || '导出失败，请重试');
    }
  } finally {
    exporting.value = false;
  }
};

onMounted(async () => {
  await fetchDevices();
  timer = setInterval(fetchData, 5000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
  clearWs();
  (Object.keys(pulseTimers) as MetricKey[]).forEach((key) => {
    const timerId = pulseTimers[key];
    if (timerId) clearTimeout(timerId);
  });
});
</script>

<style scoped>
.dashboard-container {
  padding: 22px;
  max-width: 1280px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  border-radius: 16px;
  padding: 14px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
}

.header-right {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.device-select {
  width: 210px;
}

.action-btn {
  border-radius: 10px;
}

.mb-4 {
  margin-bottom: 16px;
}

.role-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.ai-input-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.ai-answer {
  border-radius: 8px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  color: #2c3e50;
  padding: 10px 12px;
  line-height: 1.6;
}

.ai-hint {
  color: #909399;
  font-size: 13px;
}

.mission-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed #ebeef5;
}

.mission-item:last-child {
  border-bottom: none;
}

.mission-title {
  font-weight: 600;
  color: #303133;
}

.mission-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.teacher-tip {
  padding: 8px 0;
  color: #5c6b77;
  line-height: 1.6;
}

.demo-scene-card {
  border: 1px solid #fde2e2;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.sensor-card,
.ai-panel,
.student-missions,
.teacher-panel,
.demo-scene-card,
.control-card {
  border-radius: 14px;
}

.sensor-card {
  position: relative;
  padding: 14px 14px 16px;
  overflow: hidden;
  border: 1px solid rgba(44, 106, 73, 0.15);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.sensor-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--strip-color, var(--el-color-success));
  transition: background-color 0.2s ease;
}

.sensor-card:hover {
  transform: translateY(-3px);
}

.sensor-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.sensor-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #4a6156;
}

.sensor-value-wrap {
  margin-top: 12px;
  display: flex;
  align-items: baseline;
  gap: 6px;
  transform-origin: left center;
}

.sensor-value-wrap.is-pulse {
  animation: valuePulse 0.22s ease-out;
}

.sensor-value {
  font-size: 36px;
  line-height: 1;
  font-weight: 800;
  color: #1f3327;
}

.sensor-unit {
  font-size: 14px;
  color: #688073;
}

.icon {
  width: 24px;
  height: 24px;
}

.temp-icon { color: #f56c6c; }
.humidity-icon { color: #409eff; }
.soil-icon { color: #67c23a; }
.light-icon { color: #e6a23c; }

.demo-btns {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@keyframes valuePulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 14px;
}

.control-grid {
  display: flex;
  justify-content: space-around;
  padding: 10px 0;
}

.control-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  font-weight: bold;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
  }

  .header-left {
    width: 100%;
    justify-content: space-between;
  }

  .header-right {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-start;
  }

  .header-right .action-btn {
    flex: 1 1 auto;
    min-width: calc(50% - 8px);
    padding: 8px 12px;
    font-size: 13px;
  }

  .device-select {
    width: 100%;
  }

  .cards-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .sensor-value {
    font-size: 30px;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .control-grid {
    flex-direction: column;
    gap: 16px;
  }

  .control-item {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 8px;
  }

  .role-panels {
    grid-template-columns: 1fr;
  }

  .ai-input-row {
    flex-direction: column;
  }

  .demo-btns .el-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sensor-value {
    font-size: 24px;
  }

  .header-right .action-btn {
    width: 100%;
  }
}
</style>
