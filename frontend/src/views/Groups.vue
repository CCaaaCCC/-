<template>
  <div class="groups-page">
    <!-- 顶部导航 -->
    <AppTopBar title="👥 小组合作学习" :roleTagType="roleTagType" :roleText="userRoleText">
      <template #extra-actions>
        <el-button type="primary" @click="showGroupDialog = true" v-if="isTeacherOrAdmin">
          <el-icon><Plus /></el-icon> 创建小组
        </el-button>
      </template>
    </AppTopBar>

    <!-- 主内容区 -->
    <div class="main-container" v-loading="loading">
      <!-- 左侧筛选 -->
      <div class="sidebar">
        <el-card class="filter-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Filter /></el-icon>
              <span>筛选</span>
            </div>
          </template>
          <el-form :model="filterForm" label-position="top">
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
            <el-button type="primary" style="width: 100%" @click="loadGroups">查询</el-button>
          </el-form>
        </el-card>

        <!-- 统计卡片 -->
        <el-card class="stats-card" shadow="hover" style="margin-top: 16px">
          <div class="stat-item">
            <div class="stat-value">{{ groups.length }}</div>
            <div class="stat-label">小组总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalMembers }}</div>
            <div class="stat-label">成员总数</div>
          </div>
        </el-card>
      </div>

      <!-- 右侧小组列表 -->
      <div class="content-area">
        <div class="groups-grid">
          <StatusPanel
            v-if="pageErrorDetail"
            :description="pageErrorDetail"
            :actionText="pageErrorActionText"
            :actionRoute="pageErrorActionRoute"
          />

          <el-card
            v-for="group in groups"
            :key="group.id"
            class="group-card"
            shadow="hover"
            @click="viewGroup(group)"
          >
            <div class="group-header">
              <h3 class="group-name">{{ group.group_name }}</h3>
              <el-tag size="small" type="info">{{ getClassName(group.class_id) }}</el-tag>
            </div>
            <p class="group-description">{{ group.description || '暂无描述' }}</p>
            <div class="group-meta">
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ group.member_count || 0 }} 名成员
              </span>
              <span class="meta-item" v-if="group.device_name">
                <el-icon><Monitor /></el-icon>
                {{ group.device_name }}
              </span>
            </div>
            <div class="group-members-preview" v-if="group.members && group.members.length > 0">
              <el-tag
                v-for="member in group.members.slice(0, 4)"
                :key="member.id"
                size="small"
                :type="getRoleTagType(member.role)"
                style="margin-right: 4px; margin-bottom: 4px"
              >
                {{ getRoleName(member.role) }}: {{ member.student_name }}
              </el-tag>
              <el-tag v-if="group.members.length > 4" size="small">+{{ group.members.length - 4 }}</el-tag>
            </div>
          </el-card>

          <StatusPanel
            v-if="!pageErrorDetail && !loading && groups.length === 0"
            :description="'暂无学习小组'"
            :actionText="isTeacherOrAdmin ? '创建小组' : '查看个人中心'"
            :actionRoute="isTeacherOrAdmin ? undefined : '/profile'"
            :actionCallback="isTeacherOrAdmin ? () => (showGroupDialog = true) : undefined"
          />
        </div>
      </div>
    </div>

    <!-- 创建/编辑小组对话框 -->
    <el-dialog
      v-model="showGroupDialog"
      :title="editingGroup ? '编辑小组' : '创建小组'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="groupForm" label-width="100px" ref="groupFormRef" :rules="groupRules">
        <el-form-item label="小组名称" prop="group_name">
          <el-input v-model="groupForm.group_name" placeholder="如：探索者小组" />
        </el-form-item>
        <el-form-item label="所属班级" prop="class_id">
          <el-select v-model="groupForm.class_id" placeholder="选择班级" style="width: 100%">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.class_name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责设备">
          <el-select v-model="groupForm.device_id" placeholder="选择设备（可选）" clearable style="width: 100%">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.device_name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="小组描述">
          <el-input
            v-model="groupForm.description"
            type="textarea"
            :rows="3"
            placeholder="小组简介或口号"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupDialog = false">取消</el-button>
        <el-button type="primary" @click="saveGroup" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 小组详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedGroup?.group_name || '小组详情'"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedGroup" class="group-detail">
        <div class="detail-header">
          <div class="detail-info">
            <h3>{{ selectedGroup.group_name }}</h3>
            <p>{{ selectedGroup.description || '暂无描述' }}</p>
            <div class="detail-meta">
              <el-tag>{{ getClassName(selectedGroup.class_id) }}</el-tag>
              <el-tag type="success" v-if="selectedGroup.device_name">
                <el-icon><Monitor /></el-icon> {{ selectedGroup.device_name }}
              </el-tag>
            </div>
          </div>
          <div class="detail-actions" v-if="isTeacherOrAdmin">
            <el-button type="primary" @click="editGroup(selectedGroup)">编辑小组</el-button>
            <el-button type="danger" @click="confirmDeleteGroup(selectedGroup.id)">删除小组</el-button>
          </div>
        </div>

        <!-- 成员管理 -->
        <div class="members-section">
          <div class="section-header">
            <h4>👥 小组成员 ({{ selectedGroup.members?.length || 0 }}人)</h4>
            <el-button type="primary" size="small" @click="showAddMember = true" v-if="isTeacherOrAdmin">
              <el-icon><Plus /></el-icon> 添加成员
            </el-button>
          </div>
          <el-table :data="selectedGroup.members || []" style="width: 100%">
            <el-table-column prop="student_name" label="姓名" width="120" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column label="角色" width="150">
              <template #default="{ row }">
                <el-select
                  v-model="row.role"
                  size="small"
                  @change="updateMemberRole(row)"
                  v-if="isTeacherOrAdmin"
                >
                  <el-option label="组长" value="leader" />
                  <el-option label="记录员" value="recorder" />
                  <el-option label="操作员" value="operator" />
                  <el-option label="汇报员" value="reporter" />
                </el-select>
                <el-tag v-else :type="getRoleTagType(row.role)">
                  {{ getRoleName(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="加入时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.joined_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" v-if="isTeacherOrAdmin">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  @click="removeMember(row.id)"
                >
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="showAddMember"
      title="添加小组成员"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="memberForm" label-width="80px">
        <el-form-item label="选择学生">
          <el-select v-model="memberForm.student_id" placeholder="选择学生" style="width: 100%">
            <el-option
              v-for="student in availableStudents"
              :key="student.id"
              :label="`${student.real_name} (${student.username})`"
              :value="student.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="memberForm.role" placeholder="选择角色" style="width: 100%">
            <el-option label="组长" value="leader" />
            <el-option label="记录员" value="recorder" />
            <el-option label="操作员" value="operator" />
            <el-option label="汇报员" value="reporter" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMember = false">取消</el-button>
        <el-button type="primary" @click="saveMember" :loading="saving">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Filter, User, Monitor, Picture } from 'lucide-vue-next';
import StatusPanel from '../components/StatusPanel.vue';
import { useCurrentUser } from '../composables/useCurrentUser';
import AppTopBar from '../components/AppTopBar.vue';
import {
  getGroups,
  getGroupDetail,
  createGroup,
  updateGroup,
  deleteGroup,
  addGroupMember,
  updateGroupMemberRole,
  removeGroupMember,
} from '../api/groups';
import { getClasses } from '../api/classes';
import { getDevices } from '../api/devices';
import { getUsers } from '../api/users';

const router = useRouter();

// 用户信息
const { role: userRole, ensureLoaded } = useCurrentUser();
const userRoleText = computed(() => {
  const map: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' };
  return map[userRole] || '未知';
});
const roleTagType = computed(() => {
  const map: Record<string, string> = { student: '', teacher: 'warning', admin: 'danger' };
  return map[userRole.value] || '';
});
const isTeacherOrAdmin = computed(() => ['teacher', 'admin'].includes(userRole.value));
const isTeacher = computed(() => userRole.value === 'teacher');

// 状态
const loading = ref(false);
const saving = ref(false);
const groups = ref<any[]>([]);
const classes = ref<any[]>([]);
const devices = ref<any[]>([]);
const availableStudents = ref<any[]>([]);

// 页面级错误/空状态引导（403/401）
const pageErrorDetail = ref<string>('');
const pageErrorActionText = ref<string>('');
const pageErrorActionRoute = ref<string>('');

// 筛选
const filterForm = ref({ class_id: null });

// 对话框
const showGroupDialog = ref(false);
const showDetailDialog = ref(false);
const showAddMember = ref(false);
const editingGroup = ref<any>(null);
const selectedGroup = ref<any>(null);

// 表单
const groupForm = ref({
  group_name: '',
  class_id: null as number | null,
  device_id: null as number | null,
  description: ''
});

const memberForm = ref({
  student_id: null as number | null,
  role: 'recorder'
});

const groupRules = {
  group_name: [{ required: true, message: '请输入小组名称', trigger: 'blur' }],
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }]
};

// 计算属性
const totalMembers = computed(() => {
  return groups.value.reduce((sum, g) => sum + (g.member_count || 0), 0);
});

// 加载数据
const loadGroups = async () => {
  loading.value = true;
  pageErrorDetail.value = '';
  pageErrorActionText.value = '';
  pageErrorActionRoute.value = '';
  try {
    const params: any = {};
    if (filterForm.value.class_id) {
      params.class_id = filterForm.value.class_id;
    }
    const data = await getGroups(params);
    groups.value = data;
  } catch (error: any) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.message;
    if (status === 401) {
      pageErrorDetail.value = '未登录或登录已过期，请重新登录。';
      pageErrorActionText.value = '去登录';
      pageErrorActionRoute.value = '/login';
    } else if (status === 403) {
      pageErrorDetail.value = '你无权访问该班级的小组数据，请检查账号/班级分配后重试。';
      pageErrorActionText.value = '查看个人中心';
      pageErrorActionRoute.value = '/profile';
    } else {
      pageErrorDetail.value = detail;
    }
    ElMessage.error('加载小组列表失败：' + detail);
  } finally {
    loading.value = false;
  }
};

const loadClasses = async () => {
  try {
    classes.value = await getClasses();
  } catch (error: any) {
    ElMessage.error('加载班级列表失败：' + (error.response?.data?.detail || error.message));
  }
};

const loadDevices = async () => {
  try {
    devices.value = await getDevices();
  } catch (error: any) {
    ElMessage.error('加载设备列表失败：' + (error.response?.data?.detail || error.message));
  }
};

const loadAvailableStudents = async () => {
  try {
    const response = await getUsers({ role: 'student', page: 1, page_size: 500 });
    const users = response.items || [];
    availableStudents.value = users.filter((u: any) => u.is_active);
  } catch (error: any) {
    ElMessage.error('加载学生列表失败：' + (error.response?.data?.detail || error.message));
  }
};

// 获取小组详情
const viewGroup = async (group: any) => {
  showDetailDialog.value = true;
  selectedGroup.value = { ...group };

  // 直接按小组 ID 拉取详情，避免同班全量查询
  try {
    selectedGroup.value = await getGroupDetail(group.id);
  } catch (error: any) {
    ElMessage.error('加载小组详情失败：' + (error.response?.data?.detail || error.message));
  }
};

// 保存小组
const saveGroup = async () => {
  if (!groupForm.value.group_name || !groupForm.value.class_id) {
    ElMessage.warning('请填写必填项');
    return;
  }

  saving.value = true;
  try {
    if (editingGroup.value) {
      await updateGroup(editingGroup.value.id, groupForm.value);
      ElMessage.success('小组更新成功');
    } else {
      await createGroup(groupForm.value);
      ElMessage.success('小组创建成功');
    }
    showGroupDialog.value = false;
    groupForm.value = { group_name: '', class_id: null, device_id: null, description: '' };
    editingGroup.value = null;
    loadGroups();
  } catch (error: any) {
    ElMessage.error('保存失败：' + (error.response?.data?.detail || error.message));
  } finally {
    saving.value = false;
  }
};

// 编辑小组
const editGroup = (group: any) => {
  editingGroup.value = group;
  groupForm.value = {
    group_name: group.group_name,
    class_id: group.class_id,
    device_id: group.device_id,
    description: group.description
  };
  showDetailDialog.value = false;
  showGroupDialog.value = true;
};

// 删除小组
const confirmDeleteGroup = async (groupId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个小组吗？', '警告', {
      type: 'warning'
    });
    await deleteGroup(groupId);
    ElMessage.success('小组已删除');
    showDetailDialog.value = false;
    await loadGroups();
  } catch (error) {
    // 用户取消
  }
};

// 添加成员
const saveMember = async () => {
  if (!memberForm.value.student_id || !selectedGroup.value) {
    ElMessage.warning('请选择学生和角色');
    return;
  }

  saving.value = true;
  try {
    await addGroupMember(selectedGroup.value.id, memberForm.value);
    ElMessage.success('成员添加成功');
    showAddMember.value = false;
    memberForm.value = { student_id: null, role: 'recorder' };
    viewGroup(selectedGroup.value);
  } catch (error: any) {
    ElMessage.error('添加失败：' + (error.response?.data?.detail || error.message));
  } finally {
    saving.value = false;
  }
};

// 移除成员
const removeMember = async (memberId: number) => {
  try {
    await ElMessageBox.confirm('确定要移除这个成员吗？', '警告', {
      type: 'warning'
    });
    await removeGroupMember(memberId);
    ElMessage.success('成员已移除');
    if (selectedGroup.value) {
      viewGroup(selectedGroup.value);
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败：' + (error.response?.data?.detail || error.message));
    }
  }
};

// 更新成员角色（待实现后端 API）
const updateMemberRole = async (member: any) => {
  try {
    await updateGroupMemberRole(member.id, member.role);
    ElMessage.success('成员角色更新成功');
  } catch (error: any) {
    ElMessage.error('角色更新失败：' + (error.response?.data?.detail || error.message));
  }
};

// 辅助函数
const getClassName = (classId: number) => {
  const cls = classes.value.find((c) => c.id === classId);
  return cls ? cls.class_name : '未知班级';
};

const getRoleName = (role: string) => {
  const map: Record<string, string> = {
    leader: '组长',
    recorder: '记录员',
    operator: '操作员',
    reporter: '汇报员'
  };
  return map[role] || role;
};

const getRoleTagType = (role: string) => {
  const map: Record<string, string> = {
    leader: 'danger',
    recorder: 'primary',
    operator: 'warning',
    reporter: 'success'
  };
  return map[role] || '';
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN');
};

onMounted(async () => {
  try {
    await ensureLoaded();
  } catch {
    // 401/403 会由全局拦截器/页面状态面板处理
  }
  loadGroups();
  loadClasses();
  loadDevices();
  loadAvailableStudents();
});
</script>

<style scoped>
.groups-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  color: #333;
}

.header-right {
  display: flex;
  gap: 12px;
}

.main-container {
  display: flex;
  gap: 20px;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.filter-card,
.stats-card {
  background: rgba(255, 255, 255, 0.95);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #333;
}

.stat-item {
  text-align: center;
  padding: 12px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.group-card {
  background: rgba(255, 255, 255, 0.95);
  cursor: pointer;
  transition: transform 0.2s;
}

.group-card:hover {
  transform: translateY(-4px);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.group-name {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.group-description {
  color: #666;
  font-size: 14px;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.group-meta {
  display: flex;
  gap: 16px;
  color: #666;
  font-size: 13px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.group-members-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.group-detail {
  padding: 10px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.detail-info h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.detail-info p {
  margin: 0 0 12px 0;
  color: #666;
}

.detail-meta {
  display: flex;
  gap: 8px;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.members-section {
  margin-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
  }

  .groups-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

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

  .groups-grid {
    grid-template-columns: 1fr;
  }
}
</style>
