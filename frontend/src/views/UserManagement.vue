<template>
  <div class="user-management">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="header-left">
        <h2 class="page-title">👤 用户管理</h2>
        <el-tag :type="roleTagType" size="large">{{ userRoleText }}</el-tag>
      </div>
      <div class="header-right">
        <el-button @click="$router.push('/')">🏠 返回大棚监控</el-button>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 左侧边栏 -->
      <div class="sidebar">
        <!-- 用户统计卡片 -->
        <el-card class="sidebar-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>用户统计</span>
            </div>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value primary">{{ stats.total_users }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value danger">{{ stats.admin_count }}</div>
              <div class="stat-label">管理员</div>
            </div>
            <div class="stat-item">
              <div class="stat-value warning">{{ stats.teacher_count }}</div>
              <div class="stat-label">教师</div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">{{ stats.student_count }}</div>
              <div class="stat-label">学生</div>
            </div>
          </div>
        </el-card>

        <!-- 筛选卡片 -->
        <el-card class="sidebar-card mt-4" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Filter /></el-icon>
              <span>筛选条件</span>
            </div>
          </template>
          <el-form :model="filterForm" label-position="top" size="default">
            <el-form-item label="角色">
              <el-select v-model="filterForm.role" placeholder="全部角色" clearable style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="教师" value="teacher" />
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
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
            <el-form-item label="状态">
              <el-select v-model="filterForm.is_active" placeholder="全部状态" clearable style="width: 100%">
                <el-option label="启用" :value="true" />
                <el-option label="禁用" :value="false" />
              </el-select>
            </el-form-item>
            <el-button type="primary" style="width: 100%" @click="loadUsers">
              <el-icon><Search /></el-icon> 查询
            </el-button>
            <el-button style="width: 100%; margin-top: 8px" @click="resetFilter">重置</el-button>
          </el-form>
        </el-card>

        <!-- 班级快速导航 -->
        <el-card class="sidebar-card mt-4" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><School /></el-icon>
              <span>班级导航</span>
              <el-button type="primary" size="small" circle @click="showClassDialog = true">
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
          </template>
          <el-menu :default-active="activeClassId.toString()" @select="handleClassSelect" style="border: none">
            <el-menu-item index="0">
              <el-icon><Grid /></el-icon>
              <span>全部班级</span>
            </el-menu-item>
            <el-menu-item
              v-for="cls in classes"
              :key="cls.id"
              :index="cls.id.toString()"
            >
              <el-icon><UserIcon /></el-icon>
              <span>{{ cls.class_name }}</span>
              <el-tag size="small" style="margin-left: auto">{{ cls.student_count }}</el-tag>
            </el-menu-item>
          </el-menu>
        </el-card>
      </div>

      <!-- 右侧内容区 -->
      <div class="content-area">
        <!-- 顶部操作栏 -->
        <div class="action-bar">
          <div class="search-box">
            <el-input
              v-model="searchQuery"
              placeholder="搜索用户名、姓名、学号/工号..."
              clearable
              @keyup.enter="loadUsers"
              style="width: 320px"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="loadUsers">搜索</el-button>
          </div>
          
          <div class="toolbar-actions">
            <el-button @click="exportUsers">
              <el-icon><Download /></el-icon> 导出
            </el-button>
            <el-button @click="showImportDialog = true">
              <el-icon><Upload /></el-icon> 批量导入
            </el-button>
            <el-button type="primary" @click="showUserDialog = true; editingUser = null">
              <el-icon><Plus /></el-icon> 添加用户
            </el-button>
          </div>
        </div>

        <!-- 批量操作提示栏 -->
        <el-alert
          v-if="selectedUserIds.length > 0"
          :title="`已选择 ${selectedUserIds.length} 个用户`"
          type="info"
          :closable="false"
          show-icon
          class="batch-alert"
        >
          <template #default>
            <div class="batch-actions">
              <el-button size="small" type="danger" @click="batchDelete">
                <el-icon><Delete /></el-icon> 批量删除
              </el-button>
              <el-button size="small" type="warning" @click="showBatchResetPwd = true">
                <el-icon><Key /></el-icon> 批量重置密码
              </el-button>
              <el-button size="small" type="success" @click="showBatchClass = true">
                <el-icon><School /></el-icon> 批量改班级
              </el-button>
              <el-button size="small" @click="clearSelection">取消选择</el-button>
            </div>
          </template>
        </el-alert>

        <!-- 用户表格 -->
        <el-card shadow="never" class="table-card">
          <el-table 
            :data="users" 
            style="width: 100%" 
            v-loading="loading"
            @selection-change="handleSelectionChange"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
          >
            <el-table-column type="selection" width="50" align="center" />
            <el-table-column prop="username" label="用户名" width="130" />
            <el-table-column prop="real_name" label="姓名" width="100" align="center" />
            <el-table-column label="角色" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getRoleTag(row.role)" size="small">
                  {{ getRoleText(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="student_id" label="学号" width="120" align="center" />
            <el-table-column prop="teacher_id" label="工号" width="120" align="center" />
            <el-table-column prop="class_name" label="班级" width="130" align="center" />
            <el-table-column label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" width="320" fixed="right" align="center">
              <template #default="{ row }">
                <el-button size="small" @click="editUser(row)">编辑</el-button>
                <el-button size="small" type="warning" @click="showResetPassword(row)">重置密码</el-button>
                <el-button size="small" :type="row.is_active ? 'warning' : 'success'" @click="toggleActive(row)">
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="danger" @click="confirmDelete(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="showUserDialog"
      :title="editingUser ? '编辑用户' : '添加用户'"
      width="550px"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" label-width="90px" ref="userFormRef" :rules="userFormRules">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" required prop="username">
              <el-input v-model="userForm.username" :disabled="!!editingUser" placeholder="3-20 位字母数字下划线" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" required prop="password" v-if="!editingUser">
              <el-input v-model="userForm.password" type="password" placeholder="至少 6 位" show-password />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色" required prop="role">
              <el-select v-model="userForm.role" :disabled="!!editingUser" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="教师" value="teacher" />
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="userForm.real_name" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="example@email.com" />
        </el-form-item>

        <el-row :gutter="20" v-if="userForm.role === 'student'">
          <el-col :span="12">
            <el-form-item label="学号">
              <el-input v-model="userForm.student_id" placeholder="学号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级">
              <el-select v-model="userForm.class_id" placeholder="选择班级" style="width: 100%">
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.class_name"
                  :value="cls.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="userForm.role === 'teacher'">
          <el-col :span="12">
            <el-form-item label="工号">
              <el-input v-model="userForm.teacher_id" placeholder="工号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="账号状态">
          <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUserDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUser" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建班级对话框 -->
    <el-dialog v-model="showClassDialog" title="新建班级" width="450px" :close-on-click-modal="false">
      <el-form :model="classForm" label-width="90px">
        <el-form-item label="班级名称" required>
          <el-input v-model="classForm.class_name" placeholder="如：三年级 1 班" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="classForm.grade" placeholder="如：三年级" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="classForm.description" type="textarea" :rows="3" placeholder="班级描述..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showClassDialog = false">取消</el-button>
        <el-button type="primary" @click="submitClass" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showImportDialog" title="批量导入用户" width="550px" :close-on-click-modal="false">
      <el-alert
        title="导入说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          <div>
            <el-icon><InfoFilled /></el-icon>
            <span style="margin-left: 8px">导入说明</span>
          </div>
        </template>
        <ul style="margin: 10px 0; padding-left: 20px">
          <li>请上传 Excel 文件（.xlsx 或 .xls）</li>
          <li>Excel 第一行应为表头：用户名 | 密码 | 角色 | 姓名 | 学号/工号 | 邮箱 | 班级</li>
          <li>角色必须是：student、teacher 或 admin</li>
          <li>学生密码至少 6 位，管理员/教师密码需 8 位且包含大小写字母和数字</li>
        </ul>
      </el-alert>
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".xlsx,.xls"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importing">导入</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showResetDialog" title="重置密码" width="400px" :close-on-click-modal="false">
      <el-form :model="resetForm" label-width="80px">
        <el-form-item label="新密码" required>
          <el-input v-model="resetForm.newPassword" type="password" placeholder="至少 6 位" show-password />
          <div class="form-tip">
            <el-tag size="small" type="info">至少 6 位字符</el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showResetDialog = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>

    <!-- 批量修改班级对话框 -->
    <el-dialog v-model="showBatchClass" title="批量修改班级" width="400px" :close-on-click-modal="false">
      <el-form :model="batchClassForm" label-width="80px">
        <el-form-item label="选择班级">
          <el-select v-model="batchClassForm.class_id" placeholder="选择班级" style="width: 100%" clearable>
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.class_name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-alert
          title="提示"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        >
          <ul style="margin: 5px 0; padding-left: 20px">
            <li>留空表示清除班级分配</li>
            <li>只有学生账号可以分配班级</li>
          </ul>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showBatchClass = false">取消</el-button>
        <el-button type="primary" @click="submitBatchClass" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>

    <!-- 批量重置密码对话框 -->
    <el-dialog v-model="showBatchResetPwd" title="批量重置密码" width="400px" :close-on-click-modal="false">
      <el-form :model="batchResetForm" label-width="80px">
        <el-form-item label="新密码" required>
          <el-input v-model="batchResetForm.newPassword" type="password" placeholder="至少 6 位" show-password />
          <div class="form-tip">
            <el-tag size="small" type="info">至少 6 位字符</el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchResetPwd = false">取消</el-button>
        <el-button type="primary" @click="submitBatchResetPassword" :loading="submitting">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRouter } from 'vue-router';
import {
  Search, UploadFilled, Download, Upload, Plus, Delete, Key,
  DataLine, Filter, School, Grid, User as UserIcon, InfoFilled
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  resetPassword,
  toggleUserActive,
  getUserStats,
  importUsers,
  exportUsers,
  getClasses,
  createClass,
  batchDeleteUsers,
  batchUpdateClass,
  batchResetPassword,
  type User,
  type UserCreate
} from '../api/users';

const router = useRouter();
const userRole = ref(localStorage.getItem('role') || 'admin');

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

// 统计数据
const stats = ref({
  total_users: 0,
  admin_count: 0,
  teacher_count: 0,
  student_count: 0,
  active_count: 0,
  inactive_count: 0
});

// 筛选
const filterForm = ref({
  role: '',
  class_id: undefined as number | undefined,
  is_active: undefined as boolean | undefined
});
const searchQuery = ref('');
const activeClassId = ref(0);

// 用户列表
const users = ref<User[]>([]);
const loading = ref(false);

// 批量选择
const selectedUserIds = ref<number[]>([]);

// 班级列表
const classes = ref<any[]>([]);
const showClassDialog = ref(false);
const classForm = ref({
  class_name: '',
  grade: '',
  description: ''
});

// 用户对话框
const showUserDialog = ref(false);
const editingUser = ref<User | null>(null);
const submitting = ref(false);
const userFormRef = ref<FormInstance>();
const userForm = ref<UserCreate>({
  username: '',
  password: '',
  role: 'student',
  real_name: '',
  email: '',
  student_id: undefined,
  teacher_id: undefined,
  class_id: undefined,
  is_active: true
});

// 表单验证规则
const userFormRules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '3-20 位字母、数字、下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
});

// 导入对话框
const showImportDialog = ref(false);
const importFile = ref<File | null>(null);
const importing = ref(false);

// 重置密码对话框
const showResetDialog = ref(false);
const resetUser = ref<User | null>(null);
const resetForm = ref({
  newPassword: ''
});

// 批量修改班级对话框
const showBatchClass = ref(false);
const batchClassForm = ref({
  class_id: undefined as number | undefined
});

// 批量重置密码对话框
const showBatchResetPwd = ref(false);
const batchResetForm = ref({
  newPassword: ''
});

// 加载数据
const loadStats = async () => {
  try {
    stats.value = await getUserStats();
  } catch (error) {
    console.error('加载统计失败:', error);
  }
};

const loadClasses = async () => {
  try {
    classes.value = await getClasses({ is_active: true });
  } catch (error) {
    console.error('加载班级失败:', error);
  }
};

const loadUsers = async () => {
  loading.value = true;
  try {
    const params: any = { ...filterForm.value };
    if (searchQuery.value) params.search = searchQuery.value;
    users.value = await getUsers(params);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户失败');
  } finally {
    loading.value = false;
  }
};

const resetFilter = () => {
  filterForm.value = {
    role: '',
    class_id: undefined,
    is_active: undefined
  };
  searchQuery.value = '';
  loadUsers();
};

const handleClassSelect = (index: string) => {
  activeClassId.value = parseInt(index);
  filterForm.value.class_id = index === '0' ? undefined : parseInt(index);
  loadUsers();
};

// 角色标签
const getRoleTag = (role: string) => {
  const map: Record<string, any> = {
    admin: 'danger',
    teacher: 'warning',
    student: 'success'
  };
  return map[role] || '';
};

const getRoleText = (role: string) => {
  const map: Record<string, string> = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  };
  return map[role] || role;
};

// 批量选择处理
const handleSelectionChange = (selection: any[]) => {
  selectedUserIds.value = selection.map(item => item.id);
};

const clearSelection = () => {
  selectedUserIds.value = [];
};

// 用户操作
const editUser = (user: User) => {
  editingUser.value = user;
  userForm.value = {
    username: user.username,
    password: '',
    role: user.role,
    real_name: user.real_name || '',
    email: user.email || '',
    student_id: user.student_id || undefined,
    teacher_id: user.teacher_id || undefined,
    class_id: user.class_id || undefined,
    is_active: user.is_active
  };
  showUserDialog.value = true;
};

const submitUser = async () => {
  if (!userFormRef.value) return;
  
  await userFormRef.value.validate(async (valid) => {
    if (!valid) return;

    try {
      if (editingUser.value) {
        await updateUser(editingUser.value.id, userForm.value);
        ElMessage.success('更新成功');
      } else {
        await createUser(userForm.value);
        ElMessage.success('创建成功');
      }
      showUserDialog.value = false;
      loadUsers();
      loadStats();
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '操作失败');
    }
  });
};

const confirmDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此用户吗？', '确认删除', { type: 'warning' });
    await deleteUser(id);
    ElMessage.success('删除成功');
    loadUsers();
    loadStats();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败');
    }
  }
};

// 批量删除
const batchDelete = async () => {
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请选择要删除的用户');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUserIds.value.length} 个用户吗？删除后无法恢复！`,
      '确认批量删除',
      { type: 'warning' }
    );
    
    const result = await batchDeleteUsers(selectedUserIds.value);
    ElMessage.success(result.message);
    if (result.failed_users && result.failed_users.length > 0) {
      ElMessage.warning(`以下用户删除失败：${result.failed_users.map((u: any) => u.username).join(', ')}`);
    }
    clearSelection();
    loadUsers();
    loadStats();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '批量删除失败');
    }
  }
};

const toggleActive = async (user: User) => {
  try {
    await toggleUserActive(user.id);
    ElMessage.success('操作成功');
    loadUsers();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  }
};

const showResetPassword = (user: User) => {
  resetUser.value = user;
  resetForm.value.newPassword = '';
  showResetDialog.value = true;
};

const submitResetPassword = async () => {
  if (!resetForm.value.newPassword || resetForm.value.newPassword.length < 6) {
    ElMessage.warning('密码至少 6 位');
    return;
  }
  if (!resetUser.value) return;

  try {
    await resetPassword(resetUser.value.id, resetForm.value.newPassword);
    ElMessage.success('密码已重置');
    showResetDialog.value = false;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  }
};

// 批量修改班级
const submitBatchClass = async () => {
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请选择要修改的用户');
    return;
  }

  try {
    const classId = batchClassForm.value.class_id || null;
    const result = await batchUpdateClass(selectedUserIds.value, classId);
    ElMessage.success(result.message);
    showBatchClass.value = false;
    clearSelection();
    loadUsers();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '批量修改失败');
  }
};

// 批量重置密码
const submitBatchResetPassword = async () => {
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请选择要重置密码的用户');
    return;
  }

  if (!batchResetForm.value.newPassword || batchResetForm.value.newPassword.length < 6) {
    ElMessage.warning('密码至少 6 位');
    return;
  }

  try {
    const result = await batchResetPassword(selectedUserIds.value, batchResetForm.value.newPassword);
    ElMessage.success(result.message);
    if (result.failed_users && result.failed_users.length > 0) {
      ElMessage.warning(`以下用户重置失败：${result.failed_users.map((u: any) => u.username).join(', ')}`);
    }
    showBatchResetPwd.value = false;
    clearSelection();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '批量重置密码失败');
  }
};

// 班级操作
const submitClass = async () => {
  if (!classForm.value.class_name) {
    ElMessage.warning('请输入班级名称');
    return;
  }
  submitting.value = true;
  try {
    await createClass(classForm.value);
    ElMessage.success('创建成功');
    showClassDialog.value = false;
    loadClasses();
    classForm.value = { class_name: '', grade: '', description: '' };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败');
  } finally {
    submitting.value = false;
  }
};

// 导入导出
const handleFileChange = (file: any) => {
  importFile.value = file.raw;
};

const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件');
    return;
  }
  importing.value = true;
  try {
    const result = await importUsers(importFile.value);
    ElMessage.success(result.message);
    if (result.error_rows && result.error_rows.length > 0) {
      ElMessage.warning(`有 ${result.error_rows.length} 行导入失败，请检查文件格式`);
    }
    showImportDialog.value = false;
    importFile.value = null;
    loadUsers();
    loadStats();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导入失败');
  } finally {
    importing.value = false;
  }
};

const exportUsers = async () => {
  try {
    const blob = await exportUsers();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `用户列表_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    ElMessage.success('导出成功');
  } catch (error: any) {
    ElMessage.error('导出失败');
  }
};

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  router.push('/login');
};

onMounted(() => {
  loadStats();
  loadClasses();
  loadUsers();
});
</script>

<style scoped>
.user-management {
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
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.main-container {
  display: flex;
  padding: 20px;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.sidebar-card {
  border-radius: 8px;
}

.sidebar-card :deep(.el-card__header) {
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
  padding: 14px 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
}

.mt-4 {
  margin-top: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 8px 0;
}

.stat-item {
  text-align: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.stat-item:hover {
  background: #ecf5ff;
  transform: translateY(-2px);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.stat-value.primary { color: #409EFF; }
.stat-value.danger { color: #F56C6C; }
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

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.search-box {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.batch-alert {
  margin-bottom: 16px;
  border-radius: 8px;
}

.batch-alert :deep(.el-alert__content) {
  width: 100%;
}

.batch-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.table-card {
  border-radius: 8px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.form-tip {
  margin-top: 6px;
  display: flex;
  gap: 8px;
}

/* 表格样式优化 */
:deep(.el-table) {
  --el-table-header-bg-color: #fafafa;
  --el-table-header-text-color: #606266;
  --el-table-row-hover-bg-color: #f5f7fa;
}

:deep(.el-table th) {
  font-weight: 600;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>
