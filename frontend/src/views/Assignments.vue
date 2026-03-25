<template>
  <div class="assignments-page">
    <!-- 顶部导航 -->
    <div class="header">
      <div class="header-left">
        <h2>📝 实验报告</h2>
        <el-tag :type="roleTagType">{{ userRoleText }}</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="$router.push('/')">🏠 返回大棚监控</el-button>
        <el-button @click="$router.push('/teaching')">📚 教学资源</el-button>
        <el-button type="primary" @click="showAssignmentDialog = true" v-if="isTeacher">
          <el-icon><Plus /></el-icon> 布置任务
        </el-button>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 左侧筛选 -->
      <div class="sidebar">
        <el-card class="filter-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Filter /></el-icon>
              <span>筛选</span>
            </div>
          </template>
          <el-form :model="filterForm" label-position="top" size="default">
            <el-form-item label="班级">
              <el-select v-model="filterForm.class_id" placeholder="全部班级" clearable style="width: 100%">
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.class_name"
                  :value="cls.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="状态" v-if="!isTeacher">
              <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 100%">
                <el-option label="全部" value="all" />
                <el-option label="未提交" value="pending" />
                <el-option label="已提交" value="submitted" />
                <el-option label="已批改" value="graded" />
              </el-select>
            </el-form-item>
            <el-button type="primary" style="width: 100%" @click="loadAssignments">
              <el-icon><Search /></el-icon> 查询
            </el-button>
          </el-form>
        </el-card>

        <!-- 统计卡片 -->
        <el-card class="stats-card mt-4" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>我的统计</span>
            </div>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value primary">{{ stats.total }}</div>
              <div class="stat-label">总任务数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value warning">{{ stats.submitted }}</div>
              <div class="stat-label">已提交</div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">{{ stats.graded }}</div>
              <div class="stat-label">已批改</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧任务列表 -->
      <div class="content-area">
        <!-- 任务列表 -->
        <div class="assignment-list" v-loading="loading">
          <el-card
            v-for="assignment in assignments"
            :key="assignment.id"
            class="assignment-card"
            shadow="hover"
            @click="viewAssignment(assignment)"
          >
            <div class="assignment-header">
              <h3 class="assignment-title">{{ assignment.title }}</h3>
              <el-tag :type="getStatusType(assignment)" size="small">
                {{ getStatusText(assignment) }}
              </el-tag>
            </div>
            <p class="assignment-description">{{ assignment.description || '暂无描述' }}</p>
            <div class="assignment-meta">
              <span v-if="assignment.device_name">🔬 {{ assignment.device_name }}</span>
              <span v-if="assignment.class_name">👥 {{ assignment.class_name }}</span>
              <span v-if="assignment.due_date">📅 截止：{{ formatDate(assignment.due_date) }}</span>
            </div>
            <div class="assignment-footer">
              <span class="submission-count">📝 {{ assignment.submission_count }} 人已提交</span>
              <span class="created-at">{{ formatDate(assignment.created_at) }}</span>
            </div>
          </el-card>

          <!-- 空状态 -->
          <el-empty v-if="!loading && assignments.length === 0" description="暂无实验任务" />
        </div>
      </div>
    </div>

    <!-- 布置任务对话框 -->
    <el-dialog
      v-model="showAssignmentDialog"
      title="布置实验任务"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="assignmentForm" label-width="100px" ref="assignmentFormRef">
        <el-form-item label="任务标题" required>
          <el-input v-model="assignmentForm.title" placeholder="如：观察温度对植物生长的影响" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="assignmentForm.description"
            type="textarea"
            :rows="3"
            placeholder="任务描述和要求..."
          />
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select v-model="assignmentForm.device_id" placeholder="选择设备" clearable style="width: 100%">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.device_name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="布置班级">
          <el-select v-model="assignmentForm.class_id" placeholder="选择班级" style="width: 100%">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.class_name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="实验要求">
          <el-input
            v-model="assignmentForm.requirement"
            type="textarea"
            :rows="4"
            placeholder="详细实验步骤和要求..."
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="assignmentForm.start_date"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止时间">
              <el-date-picker
                v-model="assignmentForm.due_date"
                type="datetime"
                placeholder="选择截止时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="发布">
          <el-switch v-model="assignmentForm.is_published" active-text="立即发布" inactive-text="暂存" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignmentDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAssignment" :loading="submitting">发布</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="currentAssignment?.title || '任务详情'"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentAssignment" class="assignment-detail">
        <!-- 任务信息 -->
        <div class="detail-section">
          <h4>📋 任务信息</h4>
          <p><strong>描述：</strong>{{ currentAssignment.description || '无' }}</p>
          <p><strong>设备：</strong>{{ currentAssignment.device_name || '无' }}</p>
          <p><strong>班级：</strong>{{ currentAssignment.class_name || '无' }}</p>
          <p><strong>截止：</strong>{{ formatDate(currentAssignment.due_date) }}</p>
          <div v-if="currentAssignment.requirement" class="requirement">
            <strong>实验要求：</strong>
            <p>{{ currentAssignment.requirement }}</p>
          </div>
        </div>

        <!-- 学生：提交报告 -->
        <div v-if="!isTeacher" class="detail-section">
          <h4>📝 我的实验报告</h4>
          <el-form :model="submissionForm" label-width="100px">
            <el-form-item label="实验日期">
              <el-date-picker
                v-model="submissionForm.experiment_date"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="观察记录">
              <el-input
                v-model="submissionForm.observations"
                type="textarea"
                :rows="4"
                placeholder="记录你的观察发现..."
              />
            </el-form-item>
            <el-form-item label="实验结论">
              <el-input
                v-model="submissionForm.conclusion"
                type="textarea"
                :rows="3"
                placeholder="你的结论是什么？"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitReport" :loading="submitting">提交报告</el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 教师：查看提交 -->
        <div v-if="isTeacher" class="detail-section">
          <h4>📊 学生提交情况</h4>
          <el-table :data="submissions" style="width: 100%">
            <el-table-column prop="student_name" label="学生" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getSubmissionStatusType(row.status)" size="small">
                  {{ getSubmissionStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="submitted_at" label="提交时间" width="180">
              <template #default="{ row }">
                {{ row.submitted_at ? formatDate(row.submitted_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="分数" width="80">
              <template #default="{ row }">
                {{ row.score !== null ? row.score : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="viewSubmission(row)">查看</el-button>
                <el-button size="small" type="primary" @click="showGradeDialog(row)" v-if="row.status === 'submitted'">
                  批改
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 批改对话框 -->
    <el-dialog v-model="showGradeDialogVisible" title="批改实验报告" width="500px">
      <el-form :model="gradeForm" label-width="100px">
        <el-form-item label="分数" required>
          <el-input-number v-model="gradeForm.score" :min="0" :max="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="评语">
          <el-input
            v-model="gradeForm.teacher_comment"
            type="textarea"
            :rows="4"
            placeholder="写下你的评语..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGradeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitGrade" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, Filter, Search, DataLine } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { FormInstance } from 'element-plus';
import {
  getAssignments,
  createAssignment,
  getSubmissions,
  submitAssignment,
  gradeAssignment,
  getMySubmission,
  getClasses,
  getDevices,
  type Assignment,
  type AssignmentSubmission
} from '../api';

const router = useRouter();
const userRole = ref(localStorage.getItem('role') || 'student');

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
const isTeacher = computed(() => ['teacher', 'admin'].includes(userRole.value));

// 数据
const assignments = ref<Assignment[]>([]);
const classes = ref<any[]>([]);
const devices = ref<any[]>([]);
const loading = ref(false);
const submitting = ref(false);

// 统计
const stats = ref({
  total: 0,
  submitted: 0,
  graded: 0
});

// 筛选
const filterForm = ref({
  class_id: undefined as number | undefined,
  status: undefined as string | undefined
});

// 对话框
const showAssignmentDialog = ref(false);
const showDetailDialog = ref(false);
const showGradeDialogVisible = ref(false);
const assignmentFormRef = ref<FormInstance>();
const currentAssignment = ref<Assignment | null>(null);
const submissions = ref<AssignmentSubmission[]>([]);
const currentSubmission = ref<AssignmentSubmission | null>(null);

// 表单
const assignmentForm = ref({
  title: '',
  description: '',
  device_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  start_date: undefined as string | undefined,
  due_date: undefined as string | undefined,
  requirement: '',
  is_published: true
});

const submissionForm = ref({
  experiment_date: new Date().toISOString().split('T')[0],
  observations: '',
  conclusion: ''
});

const gradeForm = ref({
  score: 80,
  teacher_comment: ''
});

// 加载数据
const loadClasses = async () => {
  try {
    classes.value = await getClasses({ is_active: true });
  } catch (error) {
    console.error('加载班级失败:', error);
  }
};

const loadDevices = async () => {
  try {
    devices.value = await getDevices();
  } catch (error) {
    console.error('加载设备失败:', error);
  }
};

const loadAssignments = async () => {
  loading.value = true;
  try {
    const params: any = { is_published: true };
    if (filterForm.value.class_id) params.class_id = filterForm.value.class_id;
    if (!isTeacher.value && filterForm.value.status) {
      params.status = filterForm.value.status;
    }
    assignments.value = await getAssignments(params);
    stats.value.total = assignments.value.length;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载任务失败');
  } finally {
    loading.value = false;
  }
};

// 查看任务详情
const viewAssignment = async (assignment: Assignment) => {
  currentAssignment.value = assignment;
  showDetailDialog.value = true;

  if (isTeacher.value) {
    // 教师查看提交情况
    try {
      submissions.value = await getSubmissions(assignment.id);
    } catch (error) {
      console.error('加载提交失败:', error);
    }
  } else {
    // 学生查看自己的提交
    try {
      const submission = await getMySubmission(assignment.id);
      if (submission) {
        submissionForm.value.observations = submission.observations || '';
        submissionForm.value.conclusion = submission.conclusion || '';
        submissionForm.value.experiment_date = submission.experiment_date
          ? submission.experiment_date.split('T')[0]
          : new Date().toISOString().split('T')[0];
      }
    } catch (error) {
      // 未找到提交记录，正常
    }
  }
};

// 提交任务
const submitAssignment = async () => {
  if (!assignmentFormRef.value) return;
  if (!assignmentForm.value.title) {
    ElMessage.warning('请输入任务标题');
    return;
  }

  submitting.value = true;
  try {
    await createAssignment(assignmentForm.value);
    ElMessage.success('任务发布成功');
    showAssignmentDialog.value = false;
    loadAssignments();
    assignmentForm.value = {
      title: '',
      description: '',
      device_id: undefined,
      class_id: undefined,
      start_date: undefined,
      due_date: undefined,
      requirement: '',
      is_published: true
    };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发布失败');
  } finally {
    submitting.value = false;
  }
};

// 提交报告
const submitReport = async () => {
  if (!currentAssignment.value) return;

  submitting.value = true;
  try {
    await submitAssignment(currentAssignment.value.id, submissionForm.value);
    ElMessage.success('报告提交成功');
    showDetailDialog.value = false;
    loadAssignments();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败');
  } finally {
    submitting.value = false;
  }
};

// 显示批改对话框
const showGradeDialog = (submission: AssignmentSubmission) => {
  currentSubmission.value = submission;
  gradeForm.value.score = 80;
  gradeForm.value.teacher_comment = '';
  showGradeDialogVisible.value = true;
};

// 提交批改
const submitGrade = async () => {
  if (!currentAssignment.value || !currentSubmission.value) return;

  submitting.value = true;
  try {
    await gradeAssignment(currentAssignment.value.id, currentSubmission.value.id, gradeForm.value);
    ElMessage.success('批改完成');
    showGradeDialogVisible.value = false;
    viewAssignment(currentAssignment.value);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '批改失败');
  } finally {
    submitting.value = false;
  }
};

// 查看学生提交
const viewSubmission = (submission: AssignmentSubmission) => {
  ElMessageBox.alert(
    `<div style="max-height: 400px; overflow-y: auto;">
      <p><strong>观察记录：</strong></p>
      <p>${submission.observations || '无'}</p>
      <p><strong>实验结论：</strong></p>
      <p>${submission.conclusion || '无'}</p>
      ${submission.temp_records ? `<p><strong>温度记录：</strong>${submission.temp_records}</p>` : ''}
      ${submission.humidity_records ? `<p><strong>湿度记录：</strong>${submission.humidity_records}</p>` : ''}
    </div>`,
    `${submission.student_name} 的实验报告`,
    { dangerouslyUseHTMLString: true }
  );
};

// 辅助函数
const getStatusType = (assignment: Assignment) => {
  if (!assignment.is_published) return 'info';
  const now = new Date();
  const due = new Date(assignment.due_date || '');
  if (due < now) return 'danger';
  return 'success';
};

const getStatusText = (assignment: Assignment) => {
  if (!assignment.is_published) return '未发布';
  const now = new Date();
  const due = new Date(assignment.due_date || '');
  if (due < now) return '已截止';
  return '进行中';
};

const getSubmissionStatusType = (status: string) => {
  const map: Record<string, any> = {
    draft: 'info',
    submitted: 'warning',
    graded: 'success'
  };
  return map[status] || '';
};

const getSubmissionStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    submitted: '已提交',
    graded: '已批改'
  };
  return map[status] || status;
};

const formatDate = (dateStr?: string | null) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  router.push('/login');
};

onMounted(() => {
  loadClasses();
  loadDevices();
  loadAssignments();
});
</script>

<style scoped>
.assignments-page {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 24px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.main-container {
  display: flex;
  padding: 20px;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.filter-card,
.stats-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.mt-4 {
  margin-top: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
}

.stat-value.primary { color: #409EFF; }
.stat-value.warning { color: #E6A23C; }
.stat-value.success { color: #67C23A; }

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.assignment-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.assignment-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.assignment-card:hover {
  transform: translateY(-4px);
}

.assignment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.assignment-title {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.assignment-description {
  color: #606266;
  font-size: 14px;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.assignment-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.assignment-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.submission-count {
  color: #409EFF;
}

.assignment-detail {
  max-height: 500px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.requirement {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}
</style>
