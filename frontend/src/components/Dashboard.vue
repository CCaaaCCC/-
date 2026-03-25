<template>
  <div class="dashboard-container">
    <div class="header">
      <div class="header-left">
        <h2>大棚监控</h2>
        <el-tag :type="roleTagType">{{ userRoleText }}</el-tag>
      </div>
      <div class="header-right">
        <el-select v-model="selectedDeviceId" placeholder="选择设备" @change="handleDeviceChange" style="width: 200px; margin-right: 20px">
          <el-option
            v-for="device in devices"
            :key="device.id"
            :label="device.device_name"
            :value="device.id"
          />
        </el-select>
        <el-button type="primary" plain @click="$router.push('/display')">📊 数据大屏</el-button>
        <el-button type="success" plain @click="$router.push('/assignments')">📝 实验报告</el-button>
        <el-button type="info" plain @click="$router.push('/plants')">🌱 植物档案</el-button>
        <el-button type="success" plain @click="$router.push('/teaching')">📚 教学资源</el-button>
        <el-button type="warning" plain @click="$router.push('/users')" v-if="userRole === 'admin'">👤 用户管理</el-button>
        <el-button type="primary" plain @click="showExportDialog = true" :disabled="!selectedDeviceId">导出数据</el-button>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
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

    <div v-if="selectedDeviceId" class="content">
      <!-- Status Cards -->
      <div class="cards-grid">
        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>温度</span>
              <component :is="Thermometer" class="icon temp-icon" />
            </div>
          </template>
          <div class="card-value">{{ latest.temp }} °C</div>
        </el-card>

        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>湿度</span>
              <component :is="Droplets" class="icon humidity-icon" />
            </div>
          </template>
          <div class="card-value">{{ latest.humidity }} %</div>
        </el-card>

        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>土壤湿度</span>
              <component :is="Sprout" class="icon soil-icon" />
            </div>
          </template>
          <div class="card-value">{{ latest.soil_moisture }} %</div>
        </el-card>

        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>光照强度</span>
              <component :is="Sun" class="icon light-icon" />
            </div>
          </template>
          <div class="card-value">{{ latest.light }} Lx</div>
        </el-card>
      </div>

      <!-- Control Card (Teacher/Admin Only) -->
      <el-card v-if="canControl" class="control-card mb-4" shadow="hover" header="远程控制">
        <div class="control-grid">
          <div class="control-item">
            <span>水泵</span>
            <el-switch
              v-model="pumpActive"
              @change="(val) => handleControlChange('pump', val)"
              active-color="#13ce66" />
          </div>
          <div class="control-item">
            <span>排风扇</span>
            <el-switch
              v-model="fanActive"
              @change="(val) => handleControlChange('fan', val)"
              active-color="#409EFF" />
          </div>
          <div class="control-item">
            <span>植物灯</span>
            <el-switch
              v-model="lightActive"
              @change="(val) => handleControlChange('light', val)"
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
import { getDevices, getHistory, controlDevice, exportTelemetry, type Device, type Telemetry } from '../api';
import TelemetryChart from './TelemetryChart.vue';
import { Thermometer, Droplets, Sprout, Sun } from 'lucide-vue-next';
import { ElMessage } from 'element-plus';

const router = useRouter();
const devices = ref<Device[]>([]);
const selectedDeviceId = ref<number | null>(null);
const history = ref<Telemetry[]>([]);
const userRole = ref(localStorage.getItem('role') || 'student');
let timer: ReturnType<typeof setInterval> | null = null;

// Control States
const pumpActive = ref(false);
const fanActive = ref(false);
const lightActive = ref(false);

// Export States
const showExportDialog = ref(false);
const exporting = ref(false);
const exportForm = ref({
  startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 默认 7 天前
  endDate: new Date(),
  format: 'csv' as 'csv' | 'xlsx'
});

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

const fetchData = async () => {
  if (!selectedDeviceId.value) return;
  try {
    history.value = await getHistory(selectedDeviceId.value);
  } catch (error) {
    // Error handling delegated to interceptor
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
    } else {
      selectedDeviceId.value = null;
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

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  if (timer) clearInterval(timer);
  router.push('/login');
};

const handleExport = async () => {
  if (!selectedDeviceId.value) {
    ElMessage.warning('请选择设备');
    return;
  }

  exporting.value = true;
  try {
    // 格式化日期为 YYYY-MM-DD
    const startDate = exportForm.value.startDate.toISOString().split('T')[0];
    const endDate = exportForm.value.endDate.toISOString().split('T')[0];

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
});
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.mb-4 {
  margin-bottom: 20px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #606266;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  color: #303133;
}

.icon {
  width: 24px;
  height: 24px;
}

.temp-icon { color: #f56c6c; }
.humidity-icon { color: #409eff; }
.soil-icon { color: #67c23a; }
.light-icon { color: #e6a23c; }

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
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
  .charts-grid {
    grid-template-columns: 1fr;
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
