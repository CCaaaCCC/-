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

        <div class="primary-actions">
          <el-button class="action-btn" type="success" plain @click="navigateTo('/assignments')">实验报告</el-button>
          <el-button class="action-btn" type="success" plain @click="navigateTo('/teaching')">教学资源</el-button>
          <el-button class="action-btn" type="primary" plain @click="navigateTo('/display')">数据大屏</el-button>
        </div>

        <el-dropdown class="more-menu" trigger="click" @command="handleShortcutCommand">
          <el-button class="action-btn" plain>
            更多功能
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="item in shortcutActions"
                :key="item.path"
                :command="item.path"
              >
                {{ item.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button class="action-btn" type="primary" plain @click="showExportDialog = true" :disabled="!selectedDeviceId">
          导出数据
        </el-button>
        <el-button class="action-btn action-btn--logout" type="danger" plain @click="handleLogout">退出登录</el-button>
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

    <div v-if="fetchErrorDetail && selectedDeviceId" class="retry-row mb-4">
      <el-button size="small" type="primary" plain @click="fetchData(true)">重试当前设备数据</el-button>
    </div>

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

      <!-- Control Card (Teacher/Admin Only) -->
      <el-card v-if="canControl" class="control-card mb-4" shadow="hover" header="远程控制">
        <div class="control-grid">
          <div class="control-item">
            <span>水泵</span>
            <el-switch
              v-model="pumpActive"
              @change="onPumpChange"
              :loading="controlLoading.pump"
              :disabled="isControlLocked"
              active-color="#13ce66" />
          </div>
          <div class="control-item">
            <span>排风扇</span>
            <el-switch
              v-model="fanActive"
              @change="onFanChange"
              :loading="controlLoading.fan"
              :disabled="isControlLocked"
              active-color="#409EFF" />
            <div class="control-level">
              <span class="level-label">风速 {{ fanSpeed }}%</span>
              <el-slider
                v-model="fanSpeed"
                :min="0"
                :max="100"
                :step="5"
                :show-input="true"
                :disabled="isControlLocked"
                @change="onFanSpeedChange" />
            </div>
          </div>
          <div class="control-item">
            <span>植物灯</span>
            <el-switch
              v-model="lightActive"
              @change="onLightChange"
              :loading="controlLoading.light"
              :disabled="isControlLocked"
              active-color="#E6A23C" />
            <div class="control-level">
              <span class="level-label">亮度 {{ lightBrightness }}%</span>
              <el-slider
                v-model="lightBrightness"
                :min="0"
                :max="100"
                :step="5"
                :show-input="true"
                :disabled="isControlLocked"
                @change="onLightBrightnessChange" />
            </div>
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
  streamScienceAssistant,
  createTelemetrySocket,
  type Device,
  type Telemetry,
  type TelemetryRealtimePayload
} from '../api';
import TelemetryChart from './TelemetryChart.vue';
import { Thermometer, Droplets, Sprout, Sun } from 'lucide-vue-next';
import { ArrowDown } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { getActionErrorMessage, getErrorMessage } from '../utils/error';
import { clearAuthSession } from '../utils/authSession';

type MetricKey = 'temp' | 'humidity' | 'soil_moisture' | 'light';
type ActuatorKey = 'pump' | 'fan' | 'light';

type AIRole = 'user' | 'assistant';

type AIMessageStatus = 'streaming' | 'done' | 'error';

type AIChatMessage = {
  id: number;
  role: AIRole;
  content: string;
  source?: string;
  status: AIMessageStatus;
};

type PromptCard = {
  title: string;
  desc: string;
  question: string;
};

type MetricStatus = {
  statusText: string;
  tagType: 'success' | 'warning' | 'danger' | 'info';
  stripColor: string;
};

type ShortcutAction = {
  label: string;
  path: string;
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
let aiAbortController: AbortController | null = null;
let wsReconnectAttempts = 0;
let isPageUnmounted = false;
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
const fanSpeed = ref(100);
const lightBrightness = ref(100);
const controlLoading = ref<Record<ActuatorKey, boolean>>({
  pump: false,
  fan: false,
  light: false,
});

const aiQuestion = ref('');
const aiMessages = ref<AIChatMessage[]>([]);
const aiLoading = ref(false);
const lastAskedQuestion = ref('');
const promptSetIndex = ref(0);
const aiChatWindowRef = ref<HTMLElement | null>(null);
const quickQuestions = [
  { label: '诊断：是否要浇水', question: '现在要不要浇水？为什么？' },
  { label: '实验：蒸腾作用', question: '温度变化会怎样影响植物蒸腾？' },
  { label: '调参：环境优化', question: '如何把环境调到更适合生长？' },
  { label: '课堂：给学生讲解', question: '请用适合五年级学生的话解释当前环境变化。' }
];

const promptSets: PromptCard[][] = [
  [
    {
      title: '实时风险诊断',
      desc: '快速判断当前环境是否存在风险并给出建议。',
      question: '请结合当前数据做一次风险诊断，并给出三条可执行建议。'
    },
    {
      title: '课堂讲解脚本',
      desc: '生成可直接讲给学生听的 1 分钟讲解稿。',
      question: '请把当前监测数据整理成 1 分钟课堂讲解稿，语言适合小学生。'
    },
    {
      title: '实验任务设计',
      desc: '基于当前环境生成可操作的探究任务。',
      question: '请基于当前环境设计 2 个可在课堂完成的探究任务，并说明观察指标。'
    }
  ],
  [
    {
      title: '异常排查路径',
      desc: '按优先级列出排查步骤，便于课堂演示。',
      question: '如果当前状态异常，请按优先级给出排查步骤和每一步的判据。'
    },
    {
      title: '学生提问应答',
      desc: '生成教师可直接使用的问答清单。',
      question: '请生成 5 个学生可能会问的问题，并给出简明回答。'
    },
    {
      title: '作业点评草稿',
      desc: '给出观察记录应包含的关键点。',
      question: '请给出本次观察作业的评分维度和高分示例要点。'
    }
  ],
  [
    {
      title: '对照实验建议',
      desc: '围绕温度/湿度/光照设计对照变量。',
      question: '请给出一个围绕温度和湿度的对照实验方案，包含步骤和注意事项。'
    },
    {
      title: '操作口令生成',
      desc: '将建议转成课堂可执行的短指令。',
      question: '请把当前环境调优建议写成 6 条简短操作口令。'
    },
    {
      title: '科普拓展问题',
      desc: '延伸到可讨论的科学原理问题。',
      question: '请给出 3 个和当前数据相关的科学拓展问题，并给简短提示。'
    }
  ]
];

const capabilityPresets = [
  { label: '大纲生成', prompt: '请为“当前大棚环境分析”生成一份课堂讲解大纲。' },
  { label: '代码生成', prompt: '请给出一个用于读取并可视化温湿度数据的 Python 示例代码。' },
  { label: '学术检索', prompt: '请列出与当前环境指标相关的 3 个科学关键词及检索方向。' },
  { label: '实验点评', prompt: '请给出本节课实验表现的点评模板（优点/改进建议）。' }
];

const activePromptSet = computed(() => {
  const idx = promptSetIndex.value % promptSets.length;
  return promptSets[idx];
});

const followUpQuestions = computed(() => {
  const latestAssistant = [...aiMessages.value].reverse().find((m) => m.role === 'assistant' && m.status !== 'streaming');
  if (!latestAssistant) return [] as string[];
  return [
    '如果要优先处理一个指标，应该先处理哪个？',
    '请把建议改写成学生可执行的三步任务。',
    '请告诉我如何在 10 分钟内验证这条结论。'
  ];
});

const canRegenerate = computed(() => Boolean(lastAskedQuestion.value));

const scrollAIToBottom = () => {
  requestAnimationFrame(() => {
    const el = aiChatWindowRef.value;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  });
};

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

const isControlLocked = computed(() => {
  return controlLoading.value.pump || controlLoading.value.fan || controlLoading.value.light;
});

const shortcutActions = computed<ShortcutAction[]>(() => {
  const actions: ShortcutAction[] = [
    { label: '个人中心', path: '/profile' },
    { label: '植物档案', path: '/plants' }
  ];
  if (canControl.value) {
    actions.push({ label: '教学分析', path: '/analytics' });
  }
  if (userRole.value === 'admin') {
    actions.push({ label: '用户管理', path: '/users' });
  }
  return actions;
});

const isStudent = computed(() => userRole.value === 'student');
const useFloatingAI = true;

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

const pushAIMessage = (role: AIRole, content: string, status: AIMessageStatus): number => {
  const id = Date.now() + Math.floor(Math.random() * 1000);
  aiMessages.value.push({ id, role, content, status });
  scrollAIToBottom();
  return id;
};

const updateAIMessage = (id: number, updater: (message: AIChatMessage) => void) => {
  const target = aiMessages.value.find((item) => item.id === id);
  if (!target) return;
  updater(target);
  scrollAIToBottom();
};

const clearAIChat = () => {
  aiMessages.value = [];
  lastAskedQuestion.value = '';
};

const copyAIMessage = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success('已复制到剪贴板');
  } catch {
    ElMessage.warning('复制失败，请手动复制');
  }
};

const regenerateLastAnswer = async () => {
  if (!lastAskedQuestion.value || aiLoading.value) {
    return;
  }
  await askAI(lastAskedQuestion.value, false);
};

const rotatePromptSet = () => {
  promptSetIndex.value = (promptSetIndex.value + 1) % promptSets.length;
};

const applyCapabilityPrompt = (prompt: string) => {
  aiQuestion.value = prompt;
};

const askRecommended = async (question: string) => {
  if (aiLoading.value) return;
  await askAI(question, true);
};

const fetchData = async (force = false) => {
  if (!selectedDeviceId.value) return;
  if (!force && wsConnected.value && history.value.length > 0) {
    return;
  }

  const showLoading = force || history.value.length === 0;
  if (showLoading) {
    dataLoading.value = true;
  }
  fetchErrorDetail.value = '';
  try {
    history.value = await getHistory(selectedDeviceId.value);
  } catch (error: any) {
    fetchErrorDetail.value = getActionErrorMessage(error, {
      action: '加载实时数据',
      fallback: '实时数据加载失败，请稍后重试',
      networkErrorMessage: '实时数据连接失败，请检查后端服务状态',
    });
  } finally {
    if (showLoading) {
      dataLoading.value = false;
    }
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
  fanSpeed.value = Number(payload.actuators.fan_speed ?? 100);
  lightActive.value = payload.actuators.light_state === 1;
  lightBrightness.value = Number(payload.actuators.light_brightness ?? 100);
};

const clearWs = (resetAttempts = true) => {
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
  if (resetAttempts) {
    wsReconnectAttempts = 0;
  }
};

const scheduleWsReconnect = () => {
  if (isPageUnmounted || !selectedDeviceId.value) {
    return;
  }

  wsReconnectAttempts += 1;
  const delay = Math.min(20000, 1000 * (2 ** Math.min(4, wsReconnectAttempts)));
  wsReconnectTimer = setTimeout(() => {
    connectRealtime();
  }, delay);
};

const connectRealtime = () => {
  if (!selectedDeviceId.value || isPageUnmounted) return;
  clearWs(false);
  ws = createTelemetrySocket(
    selectedDeviceId.value,
    (payload) => {
      wsConnected.value = true;
      wsReconnectAttempts = 0;
      applyRealtimePayload(payload);
    },
    () => {
      wsConnected.value = false;
      scheduleWsReconnect();
    }
  );
  ws.onopen = () => {
    wsConnected.value = true;
    wsReconnectAttempts = 0;
  };
};

const askAI = async (questionOverride?: string, appendUserMessage = true) => {
  const question = (questionOverride ?? aiQuestion.value).trim();
  if (!question) {
    ElMessage.warning('请先输入问题');
    return;
  }

  if (appendUserMessage) {
    pushAIMessage('user', question, 'done');
  }
  lastAskedQuestion.value = question;
  if (!questionOverride) {
    aiQuestion.value = '';
  }

  const assistantMessageId = pushAIMessage('assistant', '', 'streaming');

  aiLoading.value = true;

  if (aiAbortController) {
    aiAbortController.abort();
  }
  const currentController = new AbortController();
  aiAbortController = currentController;
  let streamedAnyToken = false;

  try {
    await streamScienceAssistant(
      {
        question,
        device_id: selectedDeviceId.value || undefined
      },
      (text) => {
        streamedAnyToken = true;
        updateAIMessage(assistantMessageId, (message) => {
          message.content += text;
          message.status = 'streaming';
        });
      },
      (meta) => {
        if (meta?.source) {
          updateAIMessage(assistantMessageId, (message) => {
            message.source = meta.source;
          });
        }
      },
      { signal: currentController.signal }
    );

    if (!streamedAnyToken) {
      const res = await askScienceAssistant({
        question,
        device_id: selectedDeviceId.value || undefined
      });
      updateAIMessage(assistantMessageId, (message) => {
        message.content = res.answer;
        message.source = res.source;
        message.status = 'done';
      });
    } else {
      updateAIMessage(assistantMessageId, (message) => {
        message.status = 'done';
      });
    }
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      updateAIMessage(assistantMessageId, (message) => {
        if (!message.content) {
          message.content = '已停止生成';
        }
        message.status = 'done';
      });
      return;
    }

    const status = Number(error?.status || error?.response?.status || 0);
    if (status === 401 || status === 403) {
      updateAIMessage(assistantMessageId, (message) => {
        message.content = '登录状态已失效，请重新登录。';
        message.status = 'error';
      });
      ElMessage.error(getErrorMessage(error, '登录状态已失效，请重新登录'));
      clearAuthSession();
      router.push('/login');
      return;
    }

    if (streamedAnyToken) {
      updateAIMessage(assistantMessageId, (message) => {
        message.status = 'done';
      });
      ElMessage.warning('连接中断，已保留已生成内容');
      return;
    }

    try {
      const res = await askScienceAssistant({
        question,
        device_id: selectedDeviceId.value || undefined
      });
      updateAIMessage(assistantMessageId, (message) => {
        message.content = res.answer;
        message.source = res.source;
        message.status = 'done';
      });
    } catch (fallbackError: any) {
      const errMsg = getActionErrorMessage(fallbackError, {
        action: 'AI 问答',
        fallback: 'AI 助手暂时不可用，请稍后重试',
      });
      updateAIMessage(assistantMessageId, (message) => {
        message.content = errMsg;
        message.source = 'error';
        message.status = 'error';
      });
      ElMessage.error(getActionErrorMessage(error, {
        action: 'AI 问答',
        fallback: errMsg,
      }));
    }
  } finally {
    if (aiAbortController === currentController) {
      aiAbortController = null;
    }
    aiLoading.value = false;
  }
};

const applyQuickQuestion = (question: string) => {
  aiQuestion.value = question;
};

const navigateTo = (path: string) => {
  router.push(path);
};

const handleShortcutCommand = (path: string | number | object) => {
  if (typeof path === 'string') {
    navigateTo(path);
  }
};

const stopAI = () => {
  if (aiAbortController) {
    aiAbortController.abort();
  }
};

const syncControlStateFromDevice = (device: Device) => {
  pumpActive.value = device.pump_state === 1;
  fanActive.value = device.fan_state === 1;
  fanSpeed.value = Number(device.fan_speed ?? 100);
  lightActive.value = device.light_state === 1;
  lightBrightness.value = Number(device.light_brightness ?? 100);
};

const patchSelectedDeviceState = (
  deviceId: number,
  nextState: {
    pump_state: number;
    fan_state: number;
    fan_speed: number;
    light_state: number;
    light_brightness: number;
  }
) => {
  const target = devices.value.find((item) => item.id === deviceId);
  if (!target) return;
  target.pump_state = nextState.pump_state;
  target.fan_state = nextState.fan_state;
  target.fan_speed = nextState.fan_speed;
  target.light_state = nextState.light_state;
  target.light_brightness = nextState.light_brightness;
};

const fetchDevices = async () => {
  try {
    const currentDeviceId = selectedDeviceId.value;
    devices.value = await getDevices();
    if (devices.value.length > 0) {
      const nextDevice = devices.value.find((item) => item.id === currentDeviceId) || devices.value[0];
      const deviceChanged = selectedDeviceId.value !== nextDevice.id;
      selectedDeviceId.value = nextDevice.id;
      syncControlStateFromDevice(nextDevice);

      if (deviceChanged || history.value.length === 0) {
        await fetchData(true);
        connectRealtime();
      }
    } else {
      selectedDeviceId.value = null;
      clearWs();
    }
  } catch (error: any) {
    fetchErrorDetail.value = getActionErrorMessage(error, {
      action: '加载设备列表',
      fallback: '设备加载失败，请稍后重试',
      networkErrorMessage: '设备列表加载失败：无法连接后端服务',
    });
    console.error("Failed to fetch devices", error);
  }
};

const handleDeviceChange = () => {
  history.value = [];
  fetchErrorDetail.value = '';
  fetchData(true);
  // Update control states for new device
  const dev = devices.value.find(d => d.id === selectedDeviceId.value);
  if (dev) {
    syncControlStateFromDevice(dev);
  }
  connectRealtime();
};

const getActuatorLabel = (type: ActuatorKey) => {
  if (type === 'pump') return '水泵';
  if (type === 'fan') return '排风扇';
  return '植物灯';
};

const handleControlChange = async (type: ActuatorKey, newValue: boolean) => {
  if (!selectedDeviceId.value) return;
  if (isControlLocked.value && !controlLoading.value[type]) return;

  controlLoading.value[type] = true;

  // 保存旧状态
  const pumpOld = pumpActive.value;
  const fanOld = fanActive.value;
  const lightOld = lightActive.value;
  const fanSpeedOld = fanSpeed.value;
  const lightBrightnessOld = lightBrightness.value;

  // 更新当前状态
  if (type === 'pump') pumpActive.value = newValue;
  else if (type === 'fan') fanActive.value = newValue;
  else if (type === 'light') lightActive.value = newValue;

  try {
    const nextState = {
      pump_state: pumpActive.value ? 1 : 0,
      fan_state: fanActive.value ? 1 : 0,
      fan_speed: Number(fanSpeed.value),
      light_state: lightActive.value ? 1 : 0,
      light_brightness: Number(lightBrightness.value),
    };

    await controlDevice(selectedDeviceId.value, nextState);
    patchSelectedDeviceState(selectedDeviceId.value, nextState);
    ElMessage.success(`${getActuatorLabel(type)}已${newValue ? '开启' : '关闭'}`);
  } catch (error: any) {
    // 恢复旧状态
    pumpActive.value = pumpOld;
    fanActive.value = fanOld;
    lightActive.value = lightOld;
    fanSpeed.value = fanSpeedOld;
    lightBrightness.value = lightBrightnessOld;
    ElMessage.error(getActionErrorMessage(error, {
      action: `${getActuatorLabel(type)}控制`,
      fallback: '控制失败，已恢复到修改前状态',
    }));
  } finally {
    controlLoading.value[type] = false;
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

const onFanSpeedChange = async (value: number | [number, number]) => {
  if (!selectedDeviceId.value) return;
  if (Array.isArray(value)) return;
  if (isControlLocked.value && !controlLoading.value.fan) return;

  const nextSpeed = Math.max(0, Math.min(100, Number(value)));
  const oldSpeed = fanSpeed.value;
  fanSpeed.value = nextSpeed;
  controlLoading.value.fan = true;

  try {
    const nextState = {
      pump_state: pumpActive.value ? 1 : 0,
      fan_state: fanActive.value ? 1 : 0,
      fan_speed: nextSpeed,
      light_state: lightActive.value ? 1 : 0,
      light_brightness: Number(lightBrightness.value),
    };
    await controlDevice(selectedDeviceId.value, nextState);
    patchSelectedDeviceState(selectedDeviceId.value, nextState);
    ElMessage.success(`风速已设置为 ${nextSpeed}%`);
  } catch (error: any) {
    fanSpeed.value = oldSpeed;
    ElMessage.error(getActionErrorMessage(error, {
      action: '风速调节',
      fallback: '风速设置失败，已恢复到修改前状态',
    }));
  } finally {
    controlLoading.value.fan = false;
  }
};

const onLightBrightnessChange = async (value: number | [number, number]) => {
  if (!selectedDeviceId.value) return;
  if (Array.isArray(value)) return;
  if (isControlLocked.value && !controlLoading.value.light) return;

  const nextBrightness = Math.max(0, Math.min(100, Number(value)));
  const oldBrightness = lightBrightness.value;
  lightBrightness.value = nextBrightness;
  controlLoading.value.light = true;

  try {
    const nextState = {
      pump_state: pumpActive.value ? 1 : 0,
      fan_state: fanActive.value ? 1 : 0,
      fan_speed: Number(fanSpeed.value),
      light_state: lightActive.value ? 1 : 0,
      light_brightness: nextBrightness,
    };
    await controlDevice(selectedDeviceId.value, nextState);
    patchSelectedDeviceState(selectedDeviceId.value, nextState);
    ElMessage.success(`补光亮度已设置为 ${nextBrightness}%`);
  } catch (error: any) {
    lightBrightness.value = oldBrightness;
    ElMessage.error(getActionErrorMessage(error, {
      action: '补光亮度调节',
      fallback: '亮度设置失败，已恢复到修改前状态',
    }));
  } finally {
    controlLoading.value.light = false;
  }
};

const handleLogout = () => {
  clearAuthSession();
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
    const detail = getErrorMessage(error, '导出失败，请重试');
    if (error.response?.status === 404) {
      ElMessage.error(detail || '所选日期范围内没有数据');
    } else if (error.response?.status === 400) {
      ElMessage.error(detail || '请求参数错误');
    } else {
      ElMessage.error(getActionErrorMessage(error, {
        action: '导出数据',
        fallback: detail || '导出失败，请重试',
        forbiddenMessage: '没有权限导出该设备数据',
      }));
    }
  } finally {
    exporting.value = false;
  }
};

onMounted(async () => {
  isPageUnmounted = false;
  await fetchDevices();
  timer = setInterval(() => {
    void fetchData();
  }, 5000);
});

onUnmounted(() => {
  isPageUnmounted = true;
  if (aiAbortController) {
    aiAbortController.abort();
    aiAbortController = null;
  }
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
  padding: var(--layout-gutter);
  max-width: var(--layout-max-width);
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  border-radius: 16px;
  padding: var(--space-3);
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
  gap: var(--space-2);
  justify-content: flex-end;
  align-items: center;
}

.primary-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.device-select {
  width: 220px;
}

.action-btn {
  border-radius: 999px;
  padding-inline: 14px;
}

.action-btn--logout {
  margin-left: 4px;
}

.more-menu {
  display: inline-flex;
}

.mb-4 {
  margin-bottom: 16px;
}

.retry-row {
  display: flex;
  justify-content: flex-end;
}

.role-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.ai-toolbar-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.ai-floating-mode-hint {
  border: 1px dashed #bcdcc9;
}

.ai-hint-panel {
  color: #4b6b5a;
  line-height: 1.7;
  font-size: 13px;
}

.ai-reco-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #4b5d53;
  font-size: 13px;
  font-weight: 600;
}

.ai-reco-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.ai-reco-card {
  border: 1px solid #dbeadd;
  border-radius: 10px;
  background: #f8fcf9;
  padding: 8px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s ease;
}

.ai-reco-card:hover {
  border-color: #7ac497;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(86, 145, 112, 0.12);
}

.ai-reco-card:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.ai-reco-title {
  font-size: 13px;
  font-weight: 700;
  color: #2f5a44;
}

.ai-reco-desc {
  font-size: 12px;
  color: #6c8678;
  line-height: 1.4;
}

.ai-capability-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.ai-capability-tag {
  cursor: pointer;
}

.ai-capability-tag:hover {
  border-color: #5cae7b;
  color: #2f7d4f;
}

.ai-input-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}

.ai-chat-window {
  max-height: 260px;
  overflow: auto;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  padding: 10px;
  background: var(--glass-bg);
  margin-bottom: 10px;
}

.ai-empty-state {
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.6;
}

.ai-message {
  margin-bottom: 10px;
}

.ai-message:last-child {
  margin-bottom: 0;
}

.ai-msg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.ai-message.is-user .ai-msg-meta {
  justify-content: flex-end;
}

.ai-message.is-assistant .ai-msg-meta {
  justify-content: flex-start;
}

.ai-msg-bubble {
  border-radius: 10px;
  padding: 9px 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-message.is-user .ai-msg-bubble {
  background: color-mix(in srgb, var(--el-color-primary) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-color-primary) 28%, transparent);
  margin-left: 28px;
}

.ai-message.is-assistant .ai-msg-bubble {
  background: var(--bg-card);
  border: 1px solid var(--el-border-color-light);
  margin-right: 28px;
}

.ai-msg-bubble.is-error {
  background: color-mix(in srgb, var(--el-color-danger) 12%, transparent);
  border-color: color-mix(in srgb, var(--el-color-danger) 28%, transparent);
}

.ai-quick-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.ai-followup-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.ai-followup-label {
  color: var(--text-tertiary);
  font-size: 12px;
}

.ai-followup-tag {
  cursor: pointer;
}

.ai-quick-tag {
  cursor: pointer;
  user-select: none;
}

.ai-quick-tag:hover {
  border-color: var(--el-color-success);
  color: var(--el-color-success);
}

.typing-cursor {
  margin-left: 2px;
  animation: blink 1s step-start infinite;
  color: var(--el-color-success);
}

.ai-generating {
  color: var(--el-color-primary);
}

.ai-hint {
  color: var(--text-tertiary);
  font-size: 13px;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.mission-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed var(--el-border-color-light);
}

.mission-item:last-child {
  border-bottom: none;
}

.mission-title {
  font-weight: 600;
  color: var(--text-main);
}

.mission-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.teacher-tip {
  padding: 8px 0;
  color: var(--text-secondary);
  line-height: 1.6;
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
  color: var(--text-secondary);
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
  color: var(--text-main);
}

.sensor-unit {
  font-size: 14px;
  color: var(--text-tertiary);
}

.icon {
  width: 24px;
  height: 24px;
}

.temp-icon { color: var(--el-color-danger); }
.humidity-icon { color: var(--el-color-primary); }
.soil-icon { color: var(--el-color-success); }
.light-icon { color: var(--el-color-warning); }

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

.control-level {
  width: 210px;
}

.level-label {
  display: inline-block;
  margin-bottom: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-weight: 600;
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

  .header-right .action-btn,
  .primary-actions {
    flex: 1 1 auto;
    min-width: calc(50% - 6px);
  }

  .header-right .action-btn {
    padding: 8px 12px;
    font-size: 13px;
  }

  .primary-actions {
    width: 100%;
  }

  .more-menu {
    width: calc(50% - 6px);
  }

  .more-menu :deep(.el-button) {
    width: 100%;
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
    background: var(--el-fill-color-light);
    border-radius: 8px;
  }

  .control-level {
    width: 58%;
  }

  .role-panels {
    grid-template-columns: 1fr;
  }

  .ai-input-row {
    flex-direction: column;
  }

  .ai-reco-grid {
    grid-template-columns: 1fr;
  }

}

@media (max-width: 480px) {
  .cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sensor-value {
    font-size: 24px;
  }

  .header-right .action-btn,
  .more-menu {
    width: 100%;
  }
}
</style>
