<template>
  <div class="analytics-page">
    <div class="header">
      <div>
        <h2>教学分析中心</h2>
        <p>用于答辩展示教学闭环：布置 -> 参与 -> 反馈</p>
      </div>
      <div class="header-actions">
        <el-button @click="$router.push('/')">返回工作台</el-button>
        <el-button type="primary" @click="refreshData" :loading="loading">刷新数据</el-button>
      </div>
    </div>

    <el-alert
      v-if="!canView"
      type="warning"
      show-icon
      title="当前账号暂无权限查看教学分析"
      class="mb-4"
    />

    <template v-else>
      <div class="kpis">
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-value">{{ totalAssignments }}</div>
          <div class="kpi-label">实验任务总数</div>
        </el-card>
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-value">{{ totalSubmissions }}</div>
          <div class="kpi-label">报告提交总数</div>
        </el-card>
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-value">{{ gradedSubmissions }}</div>
          <div class="kpi-label">已批改数量</div>
        </el-card>
        <el-card class="kpi-card" shadow="hover">
          <div class="kpi-value">{{ avgScore }}</div>
          <div class="kpi-label">平均分</div>
        </el-card>
      </div>

      <div class="grid-two">
        <el-card shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>任务提交率排行</span>
              <el-tag type="success" size="small">Top 6</el-tag>
            </div>
          </template>
          <div v-if="rankedAssignments.length === 0">
            <el-empty description="暂无任务数据" />
          </div>
          <div v-else class="ranking-list">
            <div v-for="item in rankedAssignments" :key="item.id" class="ranking-item">
              <div class="ranking-title">{{ item.title }}</div>
              <el-progress :percentage="item.submitRate" :stroke-width="12" />
              <div class="ranking-meta">
                提交 {{ item.submitted }} / 估算应交 {{ item.expected }}
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>设备环境稳定度</span>
              <el-tag type="warning" size="small">近20条</el-tag>
            </div>
          </template>
          <div v-if="deviceHealth.length === 0">
            <el-empty description="暂无设备数据" />
          </div>
          <div v-else class="health-list">
            <div v-for="d in deviceHealth" :key="d.id" class="health-item">
              <div class="health-head">
                <span>{{ d.name }}</span>
                <el-tag :type="d.score >= 80 ? 'success' : d.score >= 60 ? 'warning' : 'danger'">
                  稳定度 {{ d.score }}
                </el-tag>
              </div>
              <div class="health-metrics">温度波动 {{ d.tempRange }}°C · 土壤波动 {{ d.soilRange }}%</div>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { getAssignments, getSubmissions, getDevices, getHistory } from '../api';

const router = useRouter();
const role = localStorage.getItem('role') || 'student';
const canView = computed(() => ['teacher', 'admin'].includes(role));

const loading = ref(false);
const assignments = ref<any[]>([]);
const submissionMap = ref<Record<number, any[]>>({});
const deviceHealth = ref<Array<{ id: number; name: string; score: number; tempRange: number; soilRange: number }>>([]);

const totalAssignments = computed(() => assignments.value.length);
const allSubmissions = computed(() => Object.values(submissionMap.value).flat());
const totalSubmissions = computed(() => allSubmissions.value.length);
const gradedSubmissions = computed(() => allSubmissions.value.filter((s: any) => s.status === 'graded').length);
const avgScore = computed(() => {
  const scores = allSubmissions.value
    .map((s: any) => Number(s.score))
    .filter((n: number) => !Number.isNaN(n) && n >= 0);
  if (scores.length === 0) return '--';
  return (scores.reduce((a: number, b: number) => a + b, 0) / scores.length).toFixed(1);
});

const rankedAssignments = computed(() => {
  return assignments.value
    .map((a: any) => {
      const subs = submissionMap.value[a.id] || [];
      const submitted = subs.filter((s: any) => s.status === 'submitted' || s.status === 'graded').length;
      const expected = Math.max(submitted, a.submission_count || 0, 1);
      const submitRate = Math.min(100, Math.round((submitted / expected) * 100));
      return {
        id: a.id,
        title: a.title,
        submitted,
        expected,
        submitRate
      };
    })
    .sort((x, y) => y.submitRate - x.submitRate)
    .slice(0, 6);
});

const calcRange = (values: number[]) => {
  if (values.length === 0) return 0;
  const max = Math.max(...values);
  const min = Math.min(...values);
  return Number((max - min).toFixed(1));
};

const calcStabilityScore = (tempRange: number, soilRange: number) => {
  const score = 100 - tempRange * 2 - soilRange * 1.2;
  return Math.max(0, Math.min(100, Math.round(score)));
};

const refreshData = async () => {
  if (!canView.value) {
    router.push('/');
    return;
  }

  loading.value = true;
  try {
    const taskList = await getAssignments({ is_published: true });
    assignments.value = taskList;

    const map: Record<number, any[]> = {};
    await Promise.all(
      taskList.slice(0, 10).map(async (a: any) => {
        try {
          map[a.id] = await getSubmissions(a.id);
        } catch {
          map[a.id] = [];
        }
      })
    );
    submissionMap.value = map;

    const devices = await getDevices();
    const healthData = await Promise.all(
      devices.slice(0, 6).map(async (d: any) => {
        const rows = await getHistory(d.id);
        const tempRange = calcRange(rows.map((r: any) => Number(r.temp)).filter((v: number) => !Number.isNaN(v)));
        const soilRange = calcRange(rows.map((r: any) => Number(r.soil_moisture)).filter((v: number) => !Number.isNaN(v)));
        return {
          id: d.id,
          name: d.device_name,
          tempRange,
          soilRange,
          score: calcStabilityScore(tempRange, soilRange)
        };
      })
    );
    deviceHealth.value = healthData;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载教学分析数据失败');
  } finally {
    loading.value = false;
  }
};

onMounted(refreshData);
</script>

<style scoped>
.analytics-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f6fbff 0%, #f7f9fc 100%);
  padding: 20px;
}

.header {
  max-width: 1280px;
  margin: 0 auto 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header h2 {
  margin: 0;
}

.header p {
  margin: 6px 0 0;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.mb-4 {
  margin-bottom: 16px;
}

.kpis {
  max-width: 1280px;
  margin: 0 auto 16px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
}

.kpi-card {
  border-radius: 12px;
}

.kpi-value {
  font-size: 30px;
  color: #1f78d1;
  font-weight: 700;
}

.kpi-label {
  margin-top: 4px;
  color: #7a8795;
}

.grid-two {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr 1fr;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ranking-item {
  padding: 10px 0;
  border-bottom: 1px dashed #e7ebf0;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.ranking-meta {
  margin-top: 5px;
  font-size: 12px;
  color: #7a8795;
}

.health-item {
  padding: 10px 0;
  border-bottom: 1px dashed #e7ebf0;
}

.health-item:last-child {
  border-bottom: none;
}

.health-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.health-metrics {
  color: #7a8795;
  font-size: 12px;
}

@media (max-width: 900px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }

  .grid-two {
    grid-template-columns: 1fr;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
