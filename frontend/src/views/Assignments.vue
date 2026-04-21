<template>
  <div class="assignments-page" :class="{ 'student-view': !isTeacher, 'teacher-view': isTeacher }">
    <div class="assignments-shell app-page-shell app-page-shell--wide app-fade-up">
      <!-- 顶部导航 -->
      <AppTopBar title="📝 实验报告" :roleTagType="roleTagType" :roleText="userRoleText">
        <template #extra-actions>
          <el-button @click="router.push('/teaching')">教学资源</el-button>
          <el-button type="primary" @click="showAssignmentDialog = true" v-if="isTeacher">
            <el-icon><Plus /></el-icon> 布置任务
          </el-button>
        </template>
      </AppTopBar>

      <div class="role-hero">
        <el-card shadow="never" class="hero-card app-glass-card">
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

      <div class="filter-toolbar app-glass-card">
        <div class="filter-toolbar__left">
          <h4>任务视图</h4>
          <p>按班级与状态快速定位任务，列表与统计会实时同步。</p>
        </div>
        <div class="filter-toolbar__right">
          <el-tag effect="plain" type="info">总任务 {{ stats.total }}</el-tag>
          <el-tag effect="plain" type="warning">已提交 {{ stats.submitted }}</el-tag>
          <el-tag effect="plain" type="success">已批改 {{ stats.graded }}</el-tag>
          <el-button text @click="filtersCollapsed = !filtersCollapsed">
            {{ filtersCollapsed ? '展开筛选面板' : '收起筛选面板' }}
          </el-button>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="main-container" :class="{ 'filters-collapsed': filtersCollapsed }">
        <!-- 左侧筛选 -->
        <transition name="filter-collapse">
          <div v-show="!filtersCollapsed" class="sidebar">
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
                <el-button type="primary" style="width: 100%" @click="applyFilters">
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
        </transition>

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
              <el-tag
                v-if="isTeacher && !assignment.can_manage"
                size="small"
                type="info"
                effect="plain"
              >
                只读
              </el-tag>
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

        <div v-if="!pageErrorDetail && pagination.total > 0" class="assignment-pagination">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[12, 24, 36]"
            layout="total, sizes, prev, pager, next"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
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
          <div v-if="isTeacher && canManageCurrentAssignment" style="margin: 10px 0;">
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
          <el-alert
            v-else-if="isTeacher && !canManageCurrentAssignment"
            title="当前任务为只读模式：你可以查看提交与下载附件，但不能发布、删除或批改。"
            type="info"
            :closable="false"
            style="margin: 10px 0"
          />
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
                <el-button
                  size="small"
                  type="primary"
                  @click="showGradeDialog(row)"
                  v-if="row.status === 'submitted' && canGradeCurrentAssignment"
                >
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
        <el-form-item label="AI 建议">
          <div class="ai-feedback-row">
            <el-button
              type="primary"
              plain
              :loading="aiFeedbackLoading"
              :disabled="!currentSubmission || !currentAssignment"
              @click="generateAIFeedback"
            >
              生成点评建议
            </el-button>
            <el-tag v-if="aiFeedbackSource" size="small" type="info" effect="plain">来源：{{ aiFeedbackSource }}</el-tag>
          </div>
          <div v-if="aiFeedbackDraft" class="ai-feedback-draft">
            <div class="draft-score-row">
              <span>建议分数区间：{{ aiFeedbackDraft.score_band }}</span>
              <el-button size="small" @click="applyFeedbackPart('score')">采纳分数</el-button>
            </div>
            <div class="draft-block">
              <strong>优点</strong>
              <div class="draft-lines">{{ aiFeedbackDraft.strengths.join('；') || '暂无' }}</div>
            </div>
            <div class="draft-block">
              <strong>改进建议</strong>
              <div class="draft-lines">{{ aiFeedbackDraft.improvements.join('；') || '暂无' }}</div>
            </div>
            <div class="draft-block">
              <strong>评语草稿</strong>
              <div class="draft-lines">{{ aiFeedbackDraft.teacher_comment_draft || '暂无' }}</div>
            </div>
            <div class="draft-actions">
              <el-button size="small" @click="applyFeedbackPart('strengths')">采纳优点</el-button>
              <el-button size="small" @click="applyFeedbackPart('improvements')">采纳改进</el-button>
              <el-button size="small" @click="applyFeedbackPart('comment')">采纳评语</el-button>
              <el-button size="small" type="primary" @click="applyFeedbackPart('all')">一键全部采纳</el-button>
            </div>
          </div>
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
import { usePagination } from '../composables/usePagination';
import { getActionErrorMessage, getHttpStatus, getErrorMessage } from '../utils/error';
import {
  getAssignments,
  createAssignment,
  setAssignmentPublishStatus,
  deleteAssignment,
  getSubmissions,
  submitAssignment as submitAssignmentReport,
  submitAssignmentWithFile,
  gradeAssignment,
  getAssignmentAIFeedback,
  getMySubmission,
  downloadSubmissionReport,
  type Assignment,
  type AssignmentListResponse,
  type AssignmentAIFeedback,
  type AssignmentSubmission,
} from '../api/assignments';
import { getHistory, resolveBackendAssetUrl, type Telemetry } from '../api';
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
const { pagination, setTotal, changePageSize, resetPage } = usePagination(1, 12);

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
const filtersCollapsed = ref(false);

// 对话框
const showAssignmentDialog = ref(false);
const showDetailDialog = ref(false);
const showGradeDialogVisible = ref(false);
const aiFeedbackLoading = ref(false);
const aiFeedbackSource = ref('');
const aiFeedbackDraft = ref<AssignmentAIFeedback | null>(null);
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
const canManageCurrentAssignment = computed(() => Boolean(currentAssignment.value?.can_manage));
const canGradeCurrentAssignment = computed(() => Boolean(currentAssignment.value?.can_grade));

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
  return resolveBackendAssetUrl(url);
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

const normalizeAssignmentListResponse = (
  payload: Assignment[] | AssignmentListResponse,
): AssignmentListResponse => {
  if (Array.isArray(payload)) {
    return {
      items: payload,
      total: payload.length,
      page: 1,
      page_size: payload.length || pagination.page_size,
    };
  }
  return payload;
};

const getAssignmentTotalByQuery = async (params: Record<string, any>) => {
  const response = await getAssignments({
    ...params,
    with_pagination: true,
    page: 1,
    page_size: 1,
  });
  return normalizeAssignmentListResponse(response).total;
};

const loadStudentStats = async () => {
  const base = buildStudentBaseParams();
  const [total, pending, graded] = await Promise.all([
    getAssignmentTotalByQuery({ ...base, status: 'all' }),
    getAssignmentTotalByQuery({ ...base, status: 'pending' }),
    getAssignmentTotalByQuery({ ...base, status: 'graded' }),
  ]);

  stats.value.total = total;
  stats.value.graded = graded;
  stats.value.submitted = Math.max(0, total - pending);
};

const loadTeacherStats = async () => {
  const params: any = {};
  if (filterForm.value.class_id) params.class_id = filterForm.value.class_id;
  const response = await getAssignments(params);
  const allAssignments = Array.isArray(response) ? response : response.items;
  stats.value.total = allAssignments.length;
  stats.value.submitted = allAssignments.reduce((sum, item: any) => sum + (item.submission_count || 0), 0);
  stats.value.graded = allAssignments.filter((item: any) => (item.submission_count || 0) > 0).length;
};

const gradeForm = ref({
  score: 80,
  teacher_comment: ''
});

const parseScoreBand = (band: string): number | null => {
  const match = band.match(/(\d+)(?:\s*[-~至]\s*(\d+))?/);
  if (!match) return null;

  const low = Number(match[1]);
  const high = Number(match[2] || match[1]);
  if (Number.isNaN(low) || Number.isNaN(high)) return null;

  return Math.max(0, Math.min(100, Math.round((low + high) / 2)));
};

const generateAIFeedback = async () => {
  if (!currentAssignment.value || !currentSubmission.value) {
    ElMessage.warning('请先选择待批改的提交记录');
    return;
  }

  aiFeedbackLoading.value = true;
  try {
    const feedback = await getAssignmentAIFeedback(currentAssignment.value.id, currentSubmission.value.id);
    aiFeedbackDraft.value = feedback;
    aiFeedbackSource.value = feedback.source;
    ElMessage.success(`AI 建议生成成功（${feedback.source}）`);
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, 'AI 建议生成失败'));
  } finally {
    aiFeedbackLoading.value = false;
  }
};

const appendTeacherComment = (text: string) => {
  const cleaned = text.trim();
  if (!cleaned) return;
  gradeForm.value.teacher_comment = gradeForm.value.teacher_comment
    ? `${gradeForm.value.teacher_comment}\n${cleaned}`
    : cleaned;
};

const applyFeedbackPart = (part: 'score' | 'strengths' | 'improvements' | 'comment' | 'all') => {
  if (!aiFeedbackDraft.value) {
    ElMessage.warning('请先生成 AI 建议');
    return;
  }

  const feedback = aiFeedbackDraft.value;

  if (part === 'score' || part === 'all') {
    const suggestedScore = parseScoreBand(feedback.score_band);
    if (suggestedScore !== null) {
      gradeForm.value.score = suggestedScore;
    }
  }

  if (part === 'strengths' || part === 'all') {
    appendTeacherComment(feedback.strengths?.length ? `优点：${feedback.strengths.join('；')}` : '');
  }

  if (part === 'improvements' || part === 'all') {
    appendTeacherComment(feedback.improvements?.length ? `改进建议：${feedback.improvements.join('；')}` : '');
  }

  if (part === 'comment' || part === 'all') {
    appendTeacherComment(feedback.teacher_comment_draft || '');
  }

  ElMessage.success('已采纳 AI 建议');
};

// 加载数据
const loadClasses = async () => {
  try {
    classes.value = await getClasses({ is_active: true });
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载班级失败'));
  }
};

const loadDevices = async () => {
  try {
    devices.value = await getDevices();
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载设备失败'));
  }
};

const sanitizeAssignment = (item: Assignment): Assignment => {
  const normalizedTitle = String(item.title || '').trim() || `未命名任务 #${item.id}`;
  return {
    ...item,
    title: normalizedTitle,
    description: item.description || '',
  };
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

    const requestedPage = pagination.page;
    let normalized = normalizeAssignmentListResponse(
      await getAssignments({
        ...params,
        with_pagination: true,
        page: requestedPage,
        page_size: pagination.page_size,
      }),
    );
    setTotal(normalized.total);

    if (pagination.page !== requestedPage) {
      normalized = normalizeAssignmentListResponse(
        await getAssignments({
          ...params,
          with_pagination: true,
          page: pagination.page,
          page_size: pagination.page_size,
        }),
      );
      setTotal(normalized.total);
    }

    assignments.value = normalized.items
      .filter((item: Assignment | null | undefined): item is Assignment => Boolean(item && item.id))
      .map((item) => sanitizeAssignment(item));

    if (!isTeacher.value) {
      await loadStudentStats();
    } else {
      await loadTeacherStats();
    }
    return true;
  } catch (error: any) {
    if (showError) {
      const status = error.response?.status;
      const detail = getErrorMessage(error, '加载任务失败');
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

const applyFilters = () => {
  resetPage();
  loadAssignments();
};

const handlePageSizeChange = (size: number) => {
  changePageSize(size);
  loadAssignments();
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadAssignments();
};

const toggleAssignmentPublish = async (assignment: Assignment) => {
  if (!assignment.can_manage) {
    ElMessage.warning('该任务为只读模式，无法变更发布状态');
    return;
  }
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
      ElMessage.error(getActionErrorMessage(error, {
        action: '切换任务发布状态',
        fallback: '切换发布状态失败，请稍后重试',
      }));
    }
  } finally {
    submitting.value = false;
  }
};

const deleteAssignmentPermanently = async (assignment: Assignment) => {
  if (!assignment.can_manage) {
    ElMessage.warning('该任务为只读模式，无法删除');
    return;
  }
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
      ElMessage.error(getErrorMessage(error, '删除失败'));
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
      ElMessage.error(getErrorMessage(error, '加载提交记录失败'));
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
    } catch (error: unknown) {
      const status = getHttpStatus(error);
      if (status !== 404) {
        ElMessage.error(getActionErrorMessage(error, {
          action: '加载我的提交记录',
          fallback: '加载提交记录失败，请稍后重试',
        }));
      }
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
    ElMessage.error(getErrorMessage(error, '发布失败'));
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
    ElMessage.error(getErrorMessage(error, '提交失败'));
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
    ElMessage.error(getErrorMessage(error, '下载失败'));
  }
};

// 显示批改对话框
const showGradeDialog = (submission: AssignmentSubmission) => {
  if (!canGradeCurrentAssignment.value) {
    ElMessage.warning('该任务为只读模式，无法批改');
    return;
  }
  currentSubmission.value = submission;
  gradeForm.value.score = 80;
  gradeForm.value.teacher_comment = '';
  aiFeedbackSource.value = '';
  aiFeedbackDraft.value = null;
  showGradeDialogVisible.value = true;
};

// 提交批改
const submitGrade = async () => {
  if (!currentAssignment.value || !currentSubmission.value) return;
  if (!canGradeCurrentAssignment.value) {
    ElMessage.warning('该任务为只读模式，无法批改');
    return;
  }

  submitting.value = true;
  try {
    await gradeAssignment(currentAssignment.value.id, currentSubmission.value.id, gradeForm.value);
    ElMessage.success('批改完成');
    showGradeDialogVisible.value = false;
    viewAssignment(currentAssignment.value);
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '批改失败'));
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
  padding-bottom: var(--space-6);
  background:
    radial-gradient(circle at 6% 0, var(--layout-glow-left), transparent 28%),
    linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-page) 100%);
}

.assignments-shell {
  padding-top: var(--space-5);
}

.role-hero {
  margin: 0 0 var(--space-4);
}

.hero-card {
  border-radius: 16px;
  border: 1px solid var(--el-border-color-light);
  background: var(--glass-bg-strong);
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-5);
}

.hero-content h3 {
  margin: 0;
  color: var(--text-main);
}

.hero-content p {
  margin: 6px 0 0;
  color: var(--text-secondary);
}

.hero-right {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.hero-metrics {
  display: flex;
  gap: var(--space-3);
}

.metric-item {
  min-width: 90px;
  text-align: center;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.metric-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: 14px;
  margin-bottom: var(--space-4);
}

.filter-toolbar__left {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.filter-toolbar__left h4 {
  margin: 0;
  font-size: 16px;
  color: var(--text-main);
}

.filter-toolbar__left p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.filter-toolbar__right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.filter-collapse-enter-active,
.filter-collapse-leave-active {
  transition: all var(--motion-base) var(--ease-standard);
}

.filter-collapse-enter-from,
.filter-collapse-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

.main-container {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: var(--space-5);
}

.main-container.filters-collapsed {
  grid-template-columns: minmax(0, 1fr);
}

.sidebar {
  width: 100%;
  position: sticky;
  top: var(--space-4);
  align-self: start;
}

.filter-card,
.stats-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-light);
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-weight: 600;
  color: var(--text-main);
}

.mt-4 {
  margin-top: var(--space-4);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

.stat-item {
  text-align: center;
  padding: 12px 10px;
  background: var(--el-fill-color-light);
  border-radius: 10px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
}

.stat-value.primary { color: var(--el-color-primary); }
.stat-value.warning { color: var(--el-color-warning); }
.stat-value.success { color: var(--el-color-success); }

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.content-area {
  width: 100%;
  min-width: 0;
}

.assignment-pagination {
  margin-top: var(--space-4);
  display: flex;
  justify-content: flex-end;
}

.assignment-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}

.assignment-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.student-list .assignment-card {
  border: 1px solid var(--el-border-color-light);
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
  color: var(--text-main);
}

.assignment-description {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 12px 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.assignment-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.assignment-footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-tertiary);
}

.submission-count {
  color: var(--el-color-primary);
}

.assignment-detail {
  max-height: 500px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: var(--text-main);
}

.submission-wizard {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 14px;
  background: var(--glass-bg);
}

.wizard-steps {
  margin-bottom: 16px;
}

.wizard-panel {
  border: 1px dashed var(--el-border-color);
  border-radius: 10px;
  padding: 12px;
  background: var(--bg-card);
}

.sensor-preview-card {
  margin-top: 6px;
  padding: 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-light);
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
  color: var(--text-main);
}

.sensor-preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.sensor-item {
  border-radius: 8px;
  padding: 8px;
  background: var(--bg-card);
  border: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-item span {
  font-size: 12px;
  color: var(--text-tertiary);
}

.sensor-item strong {
  font-size: 18px;
  color: var(--text-main);
}

.sensor-time {
  grid-column: 1 / -1;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.wizard-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.submit-rocket-btn {
  background: linear-gradient(120deg, var(--color-plant-600), var(--color-plant-500));
  border-color: var(--color-plant-600);
}

.submit-rocket-btn:hover {
  background: linear-gradient(120deg, var(--color-plant-700), var(--color-plant-600));
  border-color: var(--color-plant-700);
}

.requirement {
  background: var(--el-fill-color-light);
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
  color: var(--text-secondary);
}

.ai-feedback-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-feedback-draft {
  margin-top: 10px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 10px;
  background: color-mix(in srgb, var(--el-fill-color-light) 56%, transparent);
}

.draft-score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.draft-block {
  margin-top: 8px;
}

.draft-lines {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.draft-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

@media (max-width: 1100px) {
  .main-container {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }

  .sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .assignments-shell {
    padding-top: var(--space-3);
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

  .filter-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-toolbar__right {
    justify-content: flex-start;
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
