<template>
  <div class="logs-page">
    <!-- 顶部导航 -->
    <div class="header">
      <div class="header-left">
        <h2>📋 操作日志</h2>
        <el-tag type="danger">管理员专用</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="$router.push('/')">🏠 返回工作台</el-button>
        <el-button @click="exportLogs" :loading="exporting" :disabled="exporting">
          <el-icon><Download /></el-icon> 导出日志
        </el-button>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 筛选区 -->
      <el-card class="filter-card" shadow="hover">
        <el-form :model="filterForm" inline>
          <el-form-item label="操作类型">
            <el-select v-model="filterForm.operation_type" placeholder="全部类型" clearable style="width: 150px">
              <el-option label="创建用户" value="create_user" />
              <el-option label="更新用户" value="update_user" />
              <el-option label="删除用户" value="delete_user" />
              <el-option label="重置密码" value="reset_password" />
              <el-option label="启用/禁用" value="toggle_active" />
              <el-option label="批量删除" value="batch_delete" />
              <el-option label="批量修改班级" value="batch_update_class" />
              <el-option label="批量重置密码" value="batch_reset_password" />
              <el-option label="导入用户" value="import_users" />
              <el-option label="AI 科学问答" value="ai_science" />
              <el-option label="AI 流式问答" value="ai_stream" />
              <el-option label="AI 作业点评" value="ai_feedback" />
              <el-option label="AI 内容润色" value="ai_polish" />
            </el-select>
          </el-form-item>
          <el-form-item label="操作员">
            <el-select v-model="filterForm.operator_id" placeholder="全部操作员" clearable style="width: 150px">
              <el-option
                v-for="user in operators"
                :key="user.id"
                :label="`${user.real_name} (${user.username})`"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="filterForm.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 240px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadLogs">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 统计卡片 -->
      <div class="stats-row" style="margin-top: 20px">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ total }}</div>
            <div class="stat-label">总记录数</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ todayCount }}</div>
            <div class="stat-label">今日操作</div>
          </div>
        </el-card>
        <el-card class="stat-card" shadow="hover">
          <div class="stat-item">
            <div class="stat-value">{{ uniqueOperators }}</div>
            <div class="stat-label">活跃管理员</div>
          </div>
        </el-card>
      </div>

      <!-- 日志表格 -->
      <el-card class="table-card" shadow="hover" style="margin-top: 20px">
        <template v-if="loading">
          <el-skeleton animated>
            <template #template>
              <div class="log-skeleton-row" v-for="idx in 8" :key="`log-skeleton-${idx}`">
                <el-skeleton-item variant="text" style="width: 7%" />
                <el-skeleton-item variant="text" style="width: 13%" />
                <el-skeleton-item variant="text" style="width: 12%" />
                <el-skeleton-item variant="text" style="width: 12%" />
                <el-skeleton-item variant="text" style="width: 30%" />
                <el-skeleton-item variant="text" style="width: 18%" />
              </div>
            </template>
          </el-skeleton>
        </template>

        <template v-else>
          <el-table :data="logs" style="width: 100%" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="操作类型" width="140">
              <template #default="{ row }">
                <el-tag :type="getOperationTypeTag(row.operation_type)">
                  {{ getOperationTypeName(row.operation_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作员" width="150">
              <template #default="{ row }">
                <span>{{ row.operator_name || `ID:${row.operator_id}` }}</span>
              </template>
            </el-table-column>
            <el-table-column label="目标用户" width="150">
              <template #default="{ row }">
                <span v-if="row.target_user_id">{{ row.target_user_name || `ID:${row.target_user_id}` }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="details" label="详情" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container" style="margin-top: 20px; text-align: right">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.page_size"
              :page-sizes="[20, 50, 100, 200]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handlePageSizeChange"
              @current-change="handlePageChange"
            />
          </div>
        </template>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Download } from 'lucide-vue-next';
import { exportOperationLogs, getOperationLogs, getUsers } from '../api';
import { getErrorMessage } from '../utils/error';
import { clearAuthSession } from '../utils/authSession';
import { usePagination } from '../composables/usePagination';

const router = useRouter();

// 状态
const loading = ref(false);
const exporting = ref(false);
const logs = ref<any[]>([]);
const operators = ref<any[]>([]);
const { pagination, resetPage, setTotal, changePageSize } = usePagination(1, 20);
const total = computed(() => pagination.total);

// 筛选
const filterForm = ref({
  operation_type: null as string | null,
  operator_id: null as number | null,
  date_range: null as [Date, Date] | null
});

// 计算属性
const todayCount = computed(() => {
  const today = new Date().toDateString();
  return logs.value.filter((log) => new Date(log.created_at).toDateString() === today).length;
});

const uniqueOperators = computed(() => {
  const ids = new Set(logs.value.map((log) => log.operator_id));
  return ids.size;
});

const toLocalDateString = (date: Date) => {
  const y = date.getFullYear();
  const m = `${date.getMonth() + 1}`.padStart(2, '0');
  const d = `${date.getDate()}`.padStart(2, '0');
  return `${y}-${m}-${d}`;
};

// 加载日志
const loadLogs = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    };

    if (filterForm.value.operation_type) {
      params.operation_type = filterForm.value.operation_type;
    }
    if (filterForm.value.operator_id) {
      params.operator_id = filterForm.value.operator_id;
    }
    if (filterForm.value.date_range) {
      params.start_date = toLocalDateString(filterForm.value.date_range[0]);
      params.end_date = toLocalDateString(filterForm.value.date_range[1]);
    }

    const data = await getOperationLogs(params);
    if (!Array.isArray(data.items) || typeof data.total !== 'number') {
      throw new Error('日志接口返回结构异常');
    }
    logs.value = data.items;
    setTotal(data.total);
  } catch (error: any) {
    ElMessage.error('加载日志失败：' + getErrorMessage(error, '请稍后重试'));
  } finally {
    loading.value = false;
  }
};

// 加载操作员列表
const loadOperators = async () => {
  try {
    const response = await getUsers({ role: 'admin', page: 1, page_size: 200 });
    operators.value = response.items || [];
  } catch (error: any) {
    ElMessage.error('加载操作员列表失败：' + getErrorMessage(error, '请稍后重试'));
  }
};

// 重置筛选
const resetFilter = () => {
  filterForm.value = {
    operation_type: null,
    operator_id: null,
    date_range: null
  };
  resetPage();
  loadLogs();
};

const handlePageSizeChange = (size: number) => {
  changePageSize(size);
  loadLogs();
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadLogs();
};

// 导出日志
const exportLogs = async () => {
  exporting.value = true;
  try {
    const params: { start_date?: string; end_date?: string } = {};
    if (filterForm.value.date_range) {
      params.start_date = toLocalDateString(filterForm.value.date_range[0]);
      params.end_date = toLocalDateString(filterForm.value.date_range[1]);
    }

    const { blob, filename } = await exportOperationLogs(params);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `操作日志_${toLocalDateString(new Date())}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    ElMessage.success('导出成功');
  } catch (error: any) {
    ElMessage.error('导出失败：' + getErrorMessage(error, '请稍后重试'));
  } finally {
    exporting.value = false;
  }
};

// 辅助函数
const getOperationTypeName = (type: string) => {
  const map: Record<string, string> = {
    create_user: '创建用户',
    update_user: '更新用户',
    delete_user: '删除用户',
    reset_password: '重置密码',
    toggle_active: '启用/禁用',
    batch_delete: '批量删除',
    batch_update_class: '批量修改班级',
    batch_reset_password: '批量重置密码',
    import_users: '导入用户',
    ai_science: 'AI 科学问答',
    ai_stream: 'AI 流式问答',
    ai_feedback: 'AI 作业点评',
    ai_polish: 'AI 内容润色',
  };
  return map[type] || type;
};

const getOperationTypeTag = (type: string) => {
  const map: Record<string, string> = {
    create_user: 'success',
    update_user: 'primary',
    delete_user: 'danger',
    reset_password: 'warning',
    toggle_active: 'info',
    batch_delete: 'danger',
    batch_update_class: 'primary',
    batch_reset_password: 'warning',
    import_users: 'success',
    ai_science: 'warning',
    ai_stream: 'warning',
    ai_feedback: 'primary',
    ai_polish: 'success',
  };
  return map[type] || '';
};

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
};

const handleLogout = () => {
  clearAuthSession();
  router.push('/login');
};

onMounted(() => {
  loadLogs();
  loadOperators();
});
</script>

<style scoped>
.logs-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 8% 0, var(--layout-glow-left), transparent 28%),
    linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-page) 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: var(--glass-bg-strong);
  padding: 16px 24px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--shadow-soft);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  color: var(--text-main);
}

.header-right {
  display: flex;
  gap: 12px;
}

.main-container {
  max-width: var(--layout-wide-max-width);
  margin: 0 auto;
}

.filter-card {
  background: var(--glass-bg-strong);
  border: 1px solid var(--el-border-color-light);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: var(--glass-bg-strong);
  border: 1px solid var(--el-border-color-light);
}

.stat-item {
  text-align: center;
  padding: 20px 0;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: var(--text-main);
}

.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.table-card {
  background: var(--glass-bg-strong);
  border: 1px solid var(--el-border-color-light);
}

.log-skeleton-row {
  display: grid;
  grid-template-columns: 0.7fr 1.2fr 1.1fr 1.1fr 2.5fr 1.6fr;
  gap: 12px;
  padding: 10px 0;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 12px;
  }

  .header-left,
  .header-right {
    width: 100%;
    justify-content: center;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
