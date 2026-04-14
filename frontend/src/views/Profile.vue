<template>
  <div class="profile-page">
    <div class="header">
      <div class="header-left">
        <h2>👤 个人中心</h2>
      </div>
      <div class="header-right">
        <NotificationBell />
        <el-button @click="$router.push('/')">🏠 返回工作台</el-button>
      </div>
    </div>

    <div class="content" v-loading="loading">
      <StatusPanel
        v-if="pageErrorDetail"
        :description="pageErrorDetail"
        :actionText="pageErrorActionText"
        :actionRoute="pageErrorActionRoute"
      />

      <el-row v-else :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover" class="profile-card">
            <div class="avatar-row">
              <el-avatar :size="80" :src="resolvedAvatarUrl">{{ (profile?.real_name || profile?.username || '?').slice(0, 1) }}</el-avatar>
              <el-upload
                :show-file-list="false"
                accept="image/jpeg,image/png,image/webp"
                :http-request="handleAvatarUpload"
              >
                <el-button size="small">上传头像</el-button>
              </el-upload>
            </div>
            <h3>{{ profile?.real_name || profile?.username || '-' }}</h3>
            <el-form label-width="70px" class="profile-edit-form">
              <el-form-item label="名称">
                <el-input v-model="profileForm.real_name" maxlength="20" show-word-limit placeholder="请输入 2-20 字名称" />
              </el-form-item>
            </el-form>
            <el-button type="primary" size="small" :loading="savingProfile" @click="saveProfile">保存资料</el-button>
            <p><strong>用户名：</strong>{{ profile?.username || '-' }}</p>
            <p><strong>角色：</strong>{{ roleText(profile?.role) }}</p>
            <p><strong>邮箱：</strong>{{ profile?.email || '-' }}</p>
            <p><strong>{{ isTeacherRole ? '任教班级：' : '所属班级：' }}</strong>{{ profile?.class_name || '-' }}</p>
          </el-card>
        </el-col>

        <el-col :span="16">
          <el-card shadow="hover" class="todo-card">
            <template #header>
              <div class="card-header">📌 我的待办</div>
            </template>
            <div class="todo-grid">
              <!-- Teacher dashboard -->
              <div v-if="isTeacherRole" class="todo-item">
                <div class="todo-num">{{ profile?.todos?.pending_assignments ?? 0 }}</div>
                <div class="todo-label">待发布任务</div>
              </div>
              <div v-if="isTeacherRole" class="todo-item">
                <div class="todo-num warning">{{ profile?.todos?.assignments_to_grade ?? 0 }}</div>
                <div class="todo-label">待批改报告</div>
              </div>
              <div v-if="isTeacherRole" class="todo-item">
                <div class="todo-num success">{{ profile?.todos?.plants_in_class ?? 0 }}</div>
                <div class="todo-label">班级植物档案数</div>
              </div>

              <!-- Admin dashboard -->
              <div v-if="isAdminRole" class="todo-item">
                <div class="todo-num">{{ profile?.todos?.pending_assignments ?? 0 }}</div>
                <div class="todo-label">未发布任务</div>
              </div>
              <div v-if="isAdminRole" class="todo-item">
                <div class="todo-num warning">{{ profile?.todos?.assignments_to_grade ?? 0 }}</div>
                <div class="todo-label">待批改报告</div>
              </div>
              <div v-if="isAdminRole" class="todo-item">
                <div class="todo-num success">{{ profile?.todos?.plants_in_class ?? 0 }}</div>
                <div class="todo-label">植物档案总数</div>
              </div>

              <!-- Student dashboard -->
              <div v-if="isStudentRole" class="todo-item">
                <div class="todo-num">{{ profile?.todos?.pending_assignments ?? 0 }}</div>
                <div class="todo-label">待提交任务</div>
              </div>
              <div v-if="isStudentRole" class="todo-item">
                <div class="todo-num danger">{{ profile?.todos?.overdue_assignments ?? 0 }}</div>
                <div class="todo-label">已逾期任务</div>
              </div>
              <div v-if="isStudentRole" class="todo-item">
                <div class="todo-num warning">{{ profile?.todos?.assignments_to_grade ?? 0 }}</div>
                <div class="todo-label">已批改报告</div>
              </div>
              <div v-if="isStudentRole" class="todo-item">
                <div class="todo-num success">{{ profile?.todos?.plants_in_class ?? 0 }}</div>
                <div class="todo-label">我的植物档案数</div>
              </div>
            </div>

            <div class="profile-actions">
              <el-button type="primary" size="small" @click="router.push('/assignments')">
                {{ isTeacherRole || isAdminRole ? '去任务中心' : '去提交任务' }}
              </el-button>
              <el-button size="small" @click="router.push('/plants')">
                {{ isTeacherRole || isAdminRole ? '去植物档案' : '我的植物入口' }}
              </el-button>
              <el-button v-if="isTeacherRole || isAdminRole" size="small" @click="router.push('/groups')">小组协作</el-button>
            </div>
          </el-card>

          <el-card shadow="hover" class="upcoming-card">
            <template #header>
              <div class="card-header">⏰ {{ isTeacherRole || isAdminRole ? '待截止任务' : '即将到期任务' }}</div>
            </template>
            <el-table
              v-if="(profile?.upcoming_assignments || []).length > 0"
              :data="profile?.upcoming_assignments || []"
              size="small"
              style="width: 100%"
            >
              <el-table-column prop="title" label="任务" min-width="160" />
              <el-table-column prop="class_name" label="班级" width="120" />
              <el-table-column label="截止时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.due_date) }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_published ? 'success' : 'info'">{{ row.is_published ? '已发布' : '未发布' }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
            <StatusPanel
              v-else
              :description="isTeacherRole || isAdminRole ? '暂无待截止任务' : '暂无待办任务'"
              :actionText="isTeacherRole || isAdminRole ? '去任务列表' : '去提交任务'"
              actionRoute="/assignments"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import type { UploadRequestOptions } from 'element-plus';
import { resolveBackendAssetUrl } from '../api';
import { getErrorMessage } from '../utils/error';
import { getMyProfile, updateMyProfile, uploadProfileAvatar, type UserProfile } from '../api/profile';
import StatusPanel from '../components/StatusPanel.vue';
import NotificationBell from '../components/NotificationBell.vue';

const profile = ref<UserProfile | null>(null);
const loading = ref(false);
const savingProfile = ref(false);
const router = useRouter();
const profileForm = ref({ real_name: '' });

const isTeacherRole = computed(() => profile.value?.role === 'teacher');
const isAdminRole = computed(() => profile.value?.role === 'admin');
const isStudentRole = computed(() => profile.value?.role === 'student');
const pageErrorDetail = ref<string>('');
const pageErrorActionText = ref<string>('');
const pageErrorActionRoute = ref<string>('');

const roleText = (role?: string) => {
  if (role === 'admin') return '管理员';
  if (role === 'teacher') return '教师';
  if (role === 'student') return '学生';
  return '-';
};

const resolvedAvatarUrl = computed(() => {
  return resolveBackendAssetUrl(profile.value?.avatar_url);
});

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
};

const loadProfile = async () => {
  loading.value = true;
  try {
    profile.value = await getMyProfile();
    profileForm.value.real_name = profile.value.real_name || '';
    pageErrorDetail.value = '';
  } catch (error: any) {
    const status = error.response?.status;
    const detail = getErrorMessage(error, '加载个人信息失败');
    if (status === 401) {
      pageErrorDetail.value = '未登录或登录已过期，请重新登录。';
      pageErrorActionText.value = '去登录';
      pageErrorActionRoute.value = '/login';
    } else if (status === 403) {
      pageErrorDetail.value = '你无权访问该班级数据，请检查账号/班级分配后重试。';
      pageErrorActionText.value = '返回工作台';
      pageErrorActionRoute.value = '/';
    } else {
      pageErrorDetail.value = detail;
      pageErrorActionText.value = '';
      pageErrorActionRoute.value = '';
    }
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
};

const saveProfile = async () => {
  const realName = profileForm.value.real_name.trim();
  if (realName.length < 2 || realName.length > 20) {
    ElMessage.warning('名称长度需在 2-20 字之间');
    return;
  }

  savingProfile.value = true;
  try {
    profile.value = await updateMyProfile({ real_name: realName });
    ElMessage.success('资料已更新');
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '保存失败'));
  } finally {
    savingProfile.value = false;
  }
};

const handleAvatarUpload = async (options: UploadRequestOptions) => {
  try {
    const file = options.file as File;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      ElMessage.warning('仅支持 jpg/png/webp 图片');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      ElMessage.warning('头像大小不能超过 2MB');
      return;
    }

    const result = await uploadProfileAvatar(file);
    if (profile.value) {
      profile.value.avatar_url = result.avatar_url;
    }
    ElMessage.success('头像上传成功');
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '头像上传失败'));
  }
};

onMounted(loadProfile);
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 8% 0, var(--layout-glow-left), transparent 28%),
    linear-gradient(180deg, var(--bg-surface) 0%, var(--bg-page) 100%);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 24px;
  background: var(--glass-bg-strong);
  border-bottom: 1px solid var(--el-border-color-light);
  box-shadow: var(--shadow-soft);
}

.content {
  max-width: var(--layout-max-width);
  margin: 0 auto;
  padding: 20px;
}

.profile-card h3 {
  margin-top: 0;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.profile-edit-form {
  margin-bottom: 8px;
}

.todo-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 10px;
}

.todo-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px 10px;
  text-align: center;
}

.todo-num {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.todo-num.danger {
  color: var(--el-color-danger);
}

.todo-num.warning {
  color: var(--el-color-warning);
}

.todo-num.success {
  color: var(--el-color-success);
}

.todo-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.upcoming-card {
  margin-top: 20px;
}

.profile-actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .todo-grid {
    grid-template-columns: repeat(2, minmax(120px, 1fr));
  }
}
</style>
