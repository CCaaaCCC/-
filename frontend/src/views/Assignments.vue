<template>
  <div class="assignments-page" :class="{ 'student-view': !isTeacher, 'teacher-view': isTeacher }">
    <!-- 顶部导航 -->
    <AppTopBar title="📝 实验报告" :roleTagType="roleTagType" :roleText="userRoleText">
      <template #extra-actions>
        <el-button @click="router.push('/teaching')">📚 教学资源</el-button>
        <el-button type="primary" @click="showAssignmentDialog = true" v-if="isTeacher">
          <el-icon><Plus /></el-icon> 布置任务
        </el-button>
      </template>
    </AppTopBar>

    <div class="role-hero">
      <el-card shadow="never" class="hero-card">
        <div v-if="!isTeacher" class="hero-content">
          <div>
            <h3>🌟 我的探究进度</h3>
            <p>完成每个实验任务都能解锁一枚科学徽章，继续加油！</p>
          </div>
          <div class="hero-right">
            <el-progress :percentage="studentProgress" :stroke-width="10" />
            <el-tag :type="studentProgress >= 70 ? 'success' : 'warning'">当前完成度 {{ studentProgress }}%</el-tag>
          </div>
        </div>
        <div v-else class="hero-content">
          <div>
            <h3>🎯 教师任务总览</h3>
            <p>快速查看布置效率、提交率与批改进度，形成教学闭环。</p>
          </div>
          <div class="hero-metrics">
            <div class="metric-item">
              <div class="metric-value">{{ stats.total }}</div>
              <div class="metric-label">任务总数</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ stats.submitted }}</div>
              <div class="metric-label">已提交</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ stats.graded }}</div>
              <div class="metric-label">已批改</div>
            </div>
          </div>
        </div>
      </el-card>
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
        <div class="assignment-list" :class="{ 'student-list': !isTeacher }" v-loading="loading">
          <StatusPanel
            v-if="pageErrorDetail"
            :description="pageErrorDetail"
            :actionText="pageErrorActionText"
            :actionRoute="pageErrorActionRoute"
          />

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
              <span class="submission-count">
                {{ isTeacher ? `📝 ${assignment.submission_count} 人已提交` : '🏅 完成后可获得 10 积分' }}
              </span>
              <span class="created-at">{{ formatDate(assignment.created_at) }}</span>
            </div>
          </el-card>

          <!-- 空状态 -->
          <StatusPanel
            v-if="!pageErrorDetail && !loading && assignments.length === 0"
            :description="isTeacher ? '暂无待发布/待批改任务' : '暂无可提交的实验任务'"
            :actionText="isTeacher ? '去布置任务' : '查看个人中心'"
            :actionRoute="isTeacher ? undefined : '/profile'"
            :actionCallback="isTeacher ? () => (showAssignmentDialog = true) : undefined"
          />
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
                value-format="YYYY-MM-DD HH:mm:ss"
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
                value-format="YYYY-MM-DD HH:mm:ss"
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
          <p><strong>发布状态：</strong>{{ currentAssignment.is_published ? '已发布' : '未发布' }}</p>
          <div v-if="isTeacher" style="margin: 10px 0;">
            <el-button
              size="small"
              :type="currentAssignment.is_published ? 'warning' : 'success'"
              @click="toggleAssignmentPublish(currentAssignment)"
              :loading="submitting"
            >
              {{ currentAssignment.is_published ? '取消发布' : '重新发布' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="deleteAssignmentPermanently(currentAssignment)"
              :loading="submitting"
            >
              彻底删除任务
            </el-button>
          </div>
          <div v-if="currentAssignment.requirement" class="requirement">
            <strong>实验要求：</strong>
            <p>{{ currentAssignment.requirement }}</p>
          </div>
        </div>

        <!-- 学生：提交报告 -->
        <div v-if="!isTeacher" class="detail-section">
          <h4>📝 我的实验报告</h4>
          <div class="submission-wizard">
            <el-steps :active="submissionStep" finish-status="success" simple class="wizard-steps">
              <el-step title="实验信息" />
              <el-step title="观察记录" />
              <el-step title="总结与提交" />
            </el-steps>

            <div v-show="submissionStep === 0" class="wizard-panel">
              <el-form :model="submissionForm" label-width="100px">
                <el-form-item label="实验日期" required>
                  <el-date-picker
                    v-model="submissionForm.experiment_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-form>

              <div class="sensor-preview-card">
                <div class="sensor-preview-header">
                  <h5>📡 关联传感器数据（自动拉取）</h5>
                  <el-tag size="small" type="info">{{ currentAssignment.device_name || '未关联设备' }}</el-tag>
                </div>

                <el-skeleton v-if="sensorLoading" animated :rows="2" />

                <div v-else-if="sensorSnapshot" class="sensor-preview-grid">
                  <div class="sensor-item">
                    <span>温度</span>
                    <strong>{{ sensorSnapshot.temp.toFixed(1) }}°C</strong>
                  </div>
                  <div class="sensor-item">
                    <span>湿度</span>
                    <strong>{{ sensorSnapshot.humidity.toFixed(1) }}%</strong>
                  </div>
                  <div class="sensor-item">
                    <span>土壤湿度</span>
                    <strong>{{ sensorSnapshot.soil_moisture.toFixed(1) }}%</strong>
                  </div>
                  <div class="sensor-item">
                    <span>光照</span>
                    <strong>{{ sensorSnapshot.light.toFixed(0) }}Lx</strong>
                  </div>
                  <div class="sensor-time">数据时间：{{ formatDate(sensorSnapshot.timestamp) }}</div>
                </div>

                <el-empty v-else description="当前任务未关联设备或暂无实时数据" :image-size="60" />
              </div>
            </div>

            <div v-show="submissionStep === 1" class="wizard-panel">
              <el-form :model="submissionForm" label-width="100px">
                <el-form-item label="观察记录" required>
                  <el-input
                    v-model="submissionForm.observations"
                    type="textarea"
                    :rows="5"
                    placeholder="记录你的观察发现（例如：叶片颜色变化、土壤变化、环境变化）..."
                  />
                </el-form-item>
                <el-form-item label="观察照片">
                  <el-upload
                    v-model:file-list="submissionPhotoList"
                    :auto-upload="false"
                    :limit="6"
                    list-type="picture-card"
                    accept="image/*"
                    :on-change="onObservationPhotoChange"
                    :on-remove="onObservationPhotoRemove"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-upload>
                  <div class="el-upload__tip">可上传最多 6 张照片，帮助老师理解你的观察过程</div>
                </el-form-item>
              </el-form>
            </div>

            <div v-show="submissionStep === 2" class="wizard-panel">
              <el-form :model="submissionForm" label-width="100px">
                <el-form-item label="实验结论" required>
                  <el-input
                    v-model="submissionForm.conclusion"
                    type="textarea"
                    :rows="4"
                    placeholder="请总结本次实验的结论与原因分析..."
                  />
                </el-form-item>
                <el-form-item label="报告附件">
                  <el-upload
                    :auto-upload="false"
                    :limit="1"
                    :on-change="onReportFileChange"
                    :on-remove="onReportFileRemove"
                    :file-list="reportFileList"
                    accept=".pdf,.doc,.docx,.txt,.md"
                  >
                    <el-button type="primary" plain>选择文档</el-button>
                    <template #tip>
                      <div class="el-upload__tip">支持 pdf/doc/docx/txt/md，最大 20MB</div>
                    </template>
                  </el-upload>
                  <div v-if="mySubmission?.report_file_name" class="report-file-row">
                    <span>已上传：{{ mySubmission.report_file_name }}</span>
                    <el-button text type="primary" @click="downloadReport(mySubmission)">下载</el-button>
                  </div>
                </el-form-item>
                <el-alert
                  title="确认提交后老师将可以看到你的实验记录，请检查内容完整性。"
                  type="success"
                  :closable="false"
                />
              </el-form>
            </div>

            <div class="wizard-actions">
              <el-button @click="prevSubmissionStep" :disabled="submissionStep === 0">上一步</el-button>
              <el-button v-if="submissionStep < 2" type="primary" @click="nextSubmissionStep">下一步</el-button>
              <el-button
                v-else
                type="primary"
                class="submit-rocket-btn"
                @click="submitReport"
                :loading="submitting"
              >
                🚀 提交报告
              </el-button>
            </div>
          </div>
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
                <el-button size="small" type="success" plain @click="downloadReport(row)" v-if="row.report_file_name">
                  附件
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
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, Filter, Search, DataLine } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance } from 'element-plus';
import type { UploadFile, UploadFiles, UploadUserFile } from 'element-plus';
import StatusPanel from '../components/StatusPanel.vue';
import AppTopBar from '../components/AppTopBar.vue';
import { useCurrentUser } from '../composables/useCurrentUser';
import {
  getAssignments,
  createAssignment,
  setAssignmentPublishStatus,
  deleteAssignment,
  getSubmissions,
  submitAssignment as submitAssignmentReport,
  submitAssignmentWithFile,
  gradeAssignment,
  getMySubmission,
  downloadSubmissionReport,
  type Assignment,
  type AssignmentSubmission,
} from '../api/assignments';
import { getHistory, type Telemetry } from '../api';
import { getClasses } from '../api/classes';
import { getDevices } from '../api/devices';

const router = useRouter();

const { role: userRole, isTeacher, ensureLoaded } = useCurrentUser();

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
const studentProgress = computed(() => {
  if (stats.value.total === 0) return 0;
  return Math.round((stats.value.submitted / stats.value.total) * 100);
});

const toLocalDateString = (input: Date = new Date()) => {
  const y = input.getFullYear();
  const m = `${input.getMonth() + 1}`.padStart(2, '0');
  const d = `${input.getDate()}`.padStart(2, '0');
  return `${y}-${m}-${d}`;
};

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
const mySubmission = ref<AssignmentSubmission | null>(null);
const reportFile = ref<File | null>(null);
const reportFileList = ref<UploadFile[]>([]);
const submissionStep = ref(0);
const sensorLoading = ref(false);
const sensorSnapshot = ref<Telemetry | null>(null);
const submissionPhotoList = ref<UploadUserFile[]>([]);
const createdPhotoBlobUrls = new Set<string>();

// 页面级错误/空状态引导（403/401）
const pageErrorDetail = ref<string>('');
const pageErrorActionText = ref<string>('');
const pageErrorActionRoute = ref<string>('');

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
  experiment_date: toLocalDateString(),
  observations: '',
  conclusion: ''
});

const resolvePhotoUrl = (url: string) => {
  if (/^(https?:|blob:|data:)/i.test(url)) return url;
  const normalized = url.startsWith('/') ? url : `/${url}`;
  return `${window.location.protocol}//${window.location.hostname}:8000${normalized}`;
};

const clearPhotoBlobUrls = () => {
  createdPhotoBlobUrls.forEach((url) => URL.revokeObjectURL(url));
  createdPhotoBlobUrls.clear();
};

const resetSubmissionWizard = () => {
  submissionStep.value = 0;
  submissionForm.value = {
    experiment_date: toLocalDateString(),
    observations: '',
    conclusion: ''
  };
  reportFile.value = null;
  reportFileList.value = [];
  sensorSnapshot.value = null;
  sensorLoading.value = false;
  clearPhotoBlobUrls();
  submissionPhotoList.value = [];
};

const loadSensorSnapshot = async (assignment: Assignment) => {
  if (!assignment.device_id) {
    sensorSnapshot.value = null;
    return;
  }

  sensorLoading.value = true;
  try {
    const history = await getHistory(assignment.device_id);
    sensorSnapshot.value = history.length > 0 ? history[0] : null;
  } catch {
    sensorSnapshot.value = null;
  } finally {
    sensorLoading.value = false;
  }
};

const hydrateSubmissionPhotos = (photosRaw?: string | null) => {
  clearPhotoBlobUrls();
  if (!photosRaw) {
    submissionPhotoList.value = [];
    return;
  }

  try {
    const parsed = JSON.parse(photosRaw);
    const list = Array.isArray(parsed) ? parsed : [photosRaw];
    submissionPhotoList.value = list
      .filter((item) => typeof item === 'string' && item.trim().length > 0)
      .map((item, idx) => ({
        name: `photo-${idx + 1}`,
        url: resolvePhotoUrl(item),
        status: 'success'
      }));
  } catch {
    submissionPhotoList.value = [
      {
        name: 'photo-1',
        url: resolvePhotoUrl(photosRaw),
        status: 'success'
      }
    ];
  }
};

const fileToDataUrl = (file: File) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('图片读取失败'));
    reader.readAsDataURL(file);
  });

const buildPhotosPayload = async () => {
  const values: string[] = [];

  for (const file of submissionPhotoList.value) {
    if (file.raw instanceof File) {
      try {
        const dataUrl = await fileToDataUrl(file.raw);
        if (dataUrl) values.push(dataUrl);
      } catch {
        // ignore single photo read failure and continue
      }
      continue;
    }

    if (file.url && !file.url.startsWith('blob:')) {
      values.push(file.url);
      continue;
    }

    if (file.name) {
      values.push(file.name);
    }
  }

  return values.length > 0 ? JSON.stringify(values) : undefined;
};

const nextSubmissionStep = () => {
  if (submissionStep.value === 0) {
    if (!submissionForm.value.experiment_date) {
      ElMessage.warning('请先选择实验日期，再进入下一步');
      return;
    }
  }

  if (submissionStep.value === 1) {
    if (!submissionForm.value.observations.trim()) {
      ElMessage.warning('请先填写观察记录，再进入下一步');
      return;
    }
  }

  submissionStep.value = Math.min(2, submissionStep.value + 1);
};

const prevSubmissionStep = () => {
  submissionStep.value = Math.max(0, submissionStep.value - 1);
};

const buildStudentBaseParams = () => {
  const base: any = { is_published: true };
  if (filterForm.value.class_id) {
    base.class_id = filterForm.value.class_id;
  }
  return base;
};

const loadStudentStats = async () => {
  const base = buildStudentBaseParams();
  const [allAssignments, pendingAssignments, gradedAssignments] = await Promise.all([
    getAssignments({ ...base, status: 'all' }),
    getAssignments({ ...base, status: 'pending' }),
    getAssignments({ ...base, status: 'graded' })
  ]);

  stats.value.total = allAssignments.length;
  stats.value.graded = gradedAssignments.length;
  stats.value.submitted = Math.max(0, allAssignments.length - pendingAssignments.length);
};

const gradeForm = ref({
  score: 80,
  teacher_comment: ''
});

// 加载数据
const loadClasses = async () => {
  try {
    classes.value = await getClasses({ is_active: true });
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载班级失败');
  }
};

const loadDevices = async () => {
  try {
    devices.value = await getDevices();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载设备失败');
  }
};

const loadAssignments = async (showError = true): Promise<boolean> => {
  loading.value = true;
  pageErrorDetail.value = '';
  pageErrorActionText.value = '';
  pageErrorActionRoute.value = '';
  try {
    const params: any = {};
    if (!isTeacher.value) {
      params.is_published = true;
    }
    if (filterForm.value.class_id) params.class_id = filterForm.value.class_id;
    if (!isTeacher.value && filterForm.value.status) {
      params.status = filterForm.value.status;
    }
    assignments.value = await getAssignments(params);
    if (!isTeacher.value) {
      await loadStudentStats();
    } else {
      stats.value.total = assignments.value.length;
      stats.value.submitted = assignments.value.reduce((sum, item: any) => sum + (item.submission_count || 0), 0);
      stats.value.graded = assignments.value.filter((item: any) => (item.submission_count || 0) > 0).length;
    }
    return true;
  } catch (error: any) {
    if (showError) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail || '加载任务失败';
      if (status === 401) {
        pageErrorDetail.value = '未登录或登录已过期，请重新登录。';
        pageErrorActionText.value = '去登录';
        pageErrorActionRoute.value = '/login';
      } else if (status === 403) {
        pageErrorDetail.value = '你无权访问该班级的任务，请检查账号/班级分配后重试。';
        pageErrorActionText.value = '查看个人中心';
        pageErrorActionRoute.value = '/profile';
      } else {
        pageErrorDetail.value = detail;
      }
      ElMessage.error(detail);
    }
    return false;
  } finally {
    loading.value = false;
  }
};

const toggleAssignmentPublish = async (assignment: Assignment) => {
  try {
    const targetStatus = !assignment.is_published;
    const actionText = targetStatus ? '重新发布' : '取消发布';
    await ElMessageBox.confirm(`确认${actionText}该任务吗？`, '提示', { type: 'warning' });
    submitting.value = true;
    await setAssignmentPublishStatus(assignment.id, targetStatus);
    assignment.is_published = targetStatus;
    ElMessage.success(`${actionText}成功`);
    await loadAssignments(false);
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '操作失败');
    }
  } finally {
    submitting.value = false;
  }
};

const deleteAssignmentPermanently = async (assignment: Assignment) => {
  try {
    const submissionHint = assignment.submission_count
      ? `该任务下已有 ${assignment.submission_count} 份提交记录，将一并删除。`
      : '该任务下暂无提交记录。';
    await ElMessageBox.confirm(
      `确认彻底删除任务「${assignment.title}」吗？${submissionHint}此操作不可恢复。`,
      '危险操作确认',
      { type: 'warning' }
    );

    submitting.value = true;
    await deleteAssignment(assignment.id);
    showDetailDialog.value = false;
    currentAssignment.value = null;
    await loadAssignments(false);
    ElMessage.success('任务已彻底删除');
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 查看任务详情
const viewAssignment = async (assignment: Assignment) => {
  currentAssignment.value = assignment;
  showDetailDialog.value = true;
  mySubmission.value = null;
  resetSubmissionWizard();

  if (isTeacher.value) {
    // 教师查看提交情况
    try {
      submissions.value = await getSubmissions(assignment.id);
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '加载提交记录失败');
    }
  } else {
    await loadSensorSnapshot(assignment);
    // 学生查看自己的提交
    try {
      const submission = await getMySubmission(assignment.id);
      if (submission) {
        mySubmission.value = submission;
        submissionForm.value.observations = submission.observations || '';
        submissionForm.value.conclusion = submission.conclusion || '';
        submissionForm.value.experiment_date = submission.experiment_date
          ? submission.experiment_date.split('T')[0]
          : toLocalDateString();
        hydrateSubmissionPhotos((submission as any).photos || null);
      }
    } catch (error) {
      // 未找到提交记录，正常
    }
  }
};

// 提交任务
const submitAssignment = async () => {
  if (!assignmentFormRef.value) return;
  if (!assignmentForm.value.title.trim()) {
    ElMessage.warning('请输入任务标题');
    return;
  }
  if (!assignmentForm.value.class_id) {
    ElMessage.warning('请选择布置班级');
    return;
  }
  if (assignmentForm.value.start_date && assignmentForm.value.due_date) {
    const start = new Date(assignmentForm.value.start_date).getTime();
    const due = new Date(assignmentForm.value.due_date).getTime();
    if (due < start) {
      ElMessage.warning('截止时间不能早于开始时间');
      return;
    }
  }

  submitting.value = true;
  try {
    await createAssignment(assignmentForm.value);
    const loaded = await loadAssignments(false);
    if (loaded) {
      ElMessage.success('任务发布成功');
    } else {
      ElMessage.warning('任务发布成功，但任务列表刷新失败，请稍后手动刷新');
    }
    showAssignmentDialog.value = false;
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

  if (!submissionForm.value.experiment_date) {
    ElMessage.warning('请填写实验日期');
    submissionStep.value = 0;
    return;
  }
  if (!submissionForm.value.observations.trim()) {
    ElMessage.warning('请填写观察记录');
    submissionStep.value = 1;
    return;
  }
  if (!submissionForm.value.conclusion.trim()) {
    ElMessage.warning('请填写实验结论');
    submissionStep.value = 2;
    return;
  }

  const payload = {
    ...submissionForm.value,
    photos: await buildPhotosPayload()
  };

  submitting.value = true;
  try {
    if (reportFile.value) {
      await submitAssignmentWithFile(currentAssignment.value.id, payload, reportFile.value);
    } else {
      await submitAssignmentReport(currentAssignment.value.id, payload);
    }
    const loaded = await loadAssignments(false);
    if (loaded) {
      ElMessage.success('报告提交成功');
    } else {
      ElMessage.warning('报告提交成功，但任务列表刷新失败，请稍后手动刷新');
    }
    showDetailDialog.value = false;
    stats.value.submitted = Math.min(stats.value.submitted + 1, stats.value.total);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败');
  } finally {
    submitting.value = false;
  }
};

const onReportFileChange = (file: UploadFile, files: UploadFiles) => {
  reportFile.value = (file.raw as File) || null;
  reportFileList.value = files.slice(-1) as UploadFile[];
};

const onReportFileRemove = () => {
  reportFile.value = null;
  reportFileList.value = [];
};

const onObservationPhotoChange = (file: UploadFile, files: UploadFiles) => {
  submissionPhotoList.value = files.slice(0, 6).map((item, index) => {
    let url = item.url;
    if (!url && item.raw) {
      url = URL.createObjectURL(item.raw);
      createdPhotoBlobUrls.add(url);
    }
    return {
      ...item,
      name: item.name || `photo-${index + 1}`,
      url
    };
  }) as UploadUserFile[];
};

const onObservationPhotoRemove = (file: UploadFile) => {
  if (file.url && createdPhotoBlobUrls.has(file.url)) {
    URL.revokeObjectURL(file.url);
    createdPhotoBlobUrls.delete(file.url);
  }
};

const downloadReport = async (submission: AssignmentSubmission) => {
  try {
    const blob = await downloadSubmissionReport(submission.id);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = submission.report_file_name || `submission_${submission.id}.dat`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '下载失败');
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
  const lines = [
    `观察记录：${submission.observations || '无'}`,
    `实验结论：${submission.conclusion || '无'}`,
    submission.temp_records ? `温度记录：${submission.temp_records}` : '',
    submission.humidity_records ? `湿度记录：${submission.humidity_records}` : ''
  ].filter(Boolean);

  ElMessageBox.alert(
    lines.join('\n\n'),
    `${submission.student_name} 的实验报告`,
    {
      confirmButtonText: '我知道了'
    }
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
  if (isTeacher.value) {
    if (!assignment.is_published) return '未发布';
    const now = new Date();
    const due = assignment.due_date ? new Date(assignment.due_date) : null;
    if (due && due < now) return '已截止';
    return '进行中';
  }

  const due = assignment.due_date ? new Date(assignment.due_date) : null;
  if (due && due < new Date()) return '已截止';
  return '待完成';
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

onMounted(async () => {
  try {
    await ensureLoaded();
  } catch {
    // 401/403 会由全局拦截器/页面状态面板处理
  }
  await loadClasses();
  await loadDevices();
  await loadAssignments();
});

watch(showDetailDialog, (visible) => {
  if (!visible) {
    clearPhotoBlobUrls();
  }
});
</script>

<style scoped>
.assignments-page {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.role-hero {
  max-width: 1400px;
  margin: 16px auto 0;
  padding: 0 20px;
}

.hero-card {
  border-radius: 12px;
  border: 1px solid #d9ecff;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.hero-content h3 {
  margin: 0;
  color: #303133;
}

.hero-content p {
  margin: 6px 0 0;
  color: #606266;
}

.hero-right {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-metrics {
  display: flex;
  gap: 12px;
}

.metric-item {
  min-width: 90px;
  text-align: center;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f5f7fa;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #409eff;
}

.metric-label {
  font-size: 12px;
  color: #909399;
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

.student-list .assignment-card {
  border: 1px solid #e1f3d8;
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

.submission-wizard {
  border: 1px solid #e7f0ea;
  border-radius: 12px;
  padding: 14px;
  background: #fbfefc;
}

.wizard-steps {
  margin-bottom: 16px;
}

.wizard-panel {
  border: 1px dashed #d6e7dd;
  border-radius: 10px;
  padding: 12px;
  background: #ffffff;
}

.sensor-preview-card {
  margin-top: 6px;
  padding: 10px;
  border-radius: 8px;
  background: #f4faf6;
  border: 1px solid #e1f0e6;
}

.sensor-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.sensor-preview-header h5 {
  margin: 0;
  font-size: 14px;
  color: #365746;
}

.sensor-preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.sensor-item {
  border-radius: 8px;
  padding: 8px;
  background: #ffffff;
  border: 1px solid #e5efe8;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-item span {
  font-size: 12px;
  color: #668575;
}

.sensor-item strong {
  font-size: 18px;
  color: #1f5f3f;
}

.sensor-time {
  grid-column: 1 / -1;
  font-size: 12px;
  color: #6b8a7b;
  margin-top: 2px;
}

.wizard-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.submit-rocket-btn {
  background: linear-gradient(120deg, #2f8a57, #55a870);
  border-color: #2f8a57;
}

.submit-rocket-btn:hover {
  background: linear-gradient(120deg, #28764b, #4c9c66);
  border-color: #28764b;
}

.requirement {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}

.report-file-row {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}

@media (max-width: 768px) {
  .role-hero {
    padding: 0 12px;
  }

  .hero-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-right {
    width: 100%;
  }

  .hero-metrics {
    width: 100%;
  }

  .main-container {
    flex-direction: column;
    padding: 12px;
  }

  .sensor-preview-grid {
    grid-template-columns: 1fr;
  }

  .wizard-actions {
    justify-content: space-between;
  }

  .sidebar {
    width: 100%;
  }
}
</style>
