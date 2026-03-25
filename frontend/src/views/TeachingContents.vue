<template>
  <div class="teaching-container">
    <!-- 顶部导航 -->
    <div class="header">
      <div class="header-left">
        <h2>📚 教学资源</h2>
        <el-tag :type="roleTagType">{{ userRoleText }}</el-tag>
      </div>
      <div class="header-right">
        <el-button v-if="canManage" @click="showStatsDialog = true">📊 学习统计</el-button>
        <el-button @click="$router.push('/')">返回大棚监控</el-button>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 学习统计对话框 -->
    <el-dialog v-model="showStatsDialog" title="📊 学习统计" width="900px" v-if="canManage">
      <el-tabs>
        <el-tab-pane label="概览统计">
          <el-row :gutter="20" class="stats-grid">
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-item">
                  <div class="stat-label">学生总数</div>
                  <div class="stat-value">{{ stats.total_students }}</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-item">
                  <div class="stat-label">教学内容</div>
                  <div class="stat-value">{{ stats.total_contents }}</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-item">
                  <div class="stat-label">平均完成率</div>
                  <div class="stat-value">{{ stats.completion_rate }}%</div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="6">
              <el-card shadow="hover">
                <div class="stat-item">
                  <div class="stat-label">平均进度</div>
                  <div class="stat-value">{{ stats.average_progress }}%</div>
                </div>
              </el-card>
            </el-col>
          </el-row>
          
          <h4 style="margin-top: 30px;">学习进度分布</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-progress type="dashboard" :percentage="stats.completed_count" status="success" :format="() => `已完成 ${stats.completed_count}`" />
            </el-col>
            <el-col :span="8">
              <el-progress type="dashboard" :percentage="stats.in_progress_count" status="warning" :format="() => `进行中 ${stats.in_progress_count}`" />
            </el-col>
            <el-col :span="8">
              <el-progress type="dashboard" :percentage="stats.not_started_count" status="exception" :format="() => `未开始 ${stats.not_started_count}`" />
            </el-col>
          </el-row>
        </el-tab-pane>
        
        <el-tab-pane label="学生进度">
          <el-table :data="studentsProgress" style="width: 100%">
            <el-table-column prop="student_name" label="学生" width="120" />
            <el-table-column prop="completed_count" label="已完成" width="100" />
            <el-table-column prop="in_progress_count" label="进行中" width="100" />
            <el-table-column label="完成率" width="150">
              <template #default="{ row }">
                <el-progress :percentage="row.completion_rate" :status="row.completion_rate >= 80 ? 'success' : undefined" />
              </template>
            </el-table-column>
            <el-table-column label="学习时长">
              <template #default="{ row }">
                {{ formatDuration(row.total_time_spent) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <div class="main-content">
      <!-- 左侧分类导航 -->
      <div class="sidebar">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>分类导航</span>
              <el-button v-if="canManage" type="primary" size="small" @click="showCategoryDialog = true">
                + 新建分类
              </el-button>
            </div>
          </template>
          <el-menu :default-active="activeCategoryId.toString()" @select="handleCategorySelect">
            <el-menu-item index="0">
              <el-icon><Folder /></el-icon>
              <span>全部分类</span>
            </el-menu-item>
            <el-menu-item
              v-for="category in categories"
              :key="category.id"
              :index="category.id.toString()"
            >
              <el-icon><Folder /></el-icon>
              <span>{{ category.name }}</span>
            </el-menu-item>
          </el-menu>
        </el-card>

        <!-- 我的学习进度 -->
        <el-card class="mt-4">
          <template #header>
            <span>我的学习</span>
          </template>
          <div v-if="learningRecords.length > 0" class="learning-list">
            <div
              v-for="record in learningRecords.slice(0, 5)"
              :key="record.id"
              class="learning-item"
              @click="viewContent(record.content_id)"
            >
              <div class="learning-title">{{ getContentTitle(record.content_id) }}</div>
              <el-progress :percentage="record.progress_percent" :status="record.status === 'completed' ? 'success' : undefined" />
            </div>
          </div>
          <el-empty v-else description="暂无学习记录" :image-size="60" />
        </el-card>
      </div>

      <!-- 右侧内容列表 -->
      <div class="content-area">
        <!-- 搜索栏 -->
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索教学内容..."
            clearable
            @keyup.enter="handleSearch"
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="searchType" placeholder="全部类型" clearable style="width: 120px; margin-left: 10px;">
            <el-option label="文章" value="article" />
            <el-option label="视频" value="video" />
            <el-option label="图片" value="image" />
            <el-option label="PDF" value="pdf" />
          </el-select>
          <el-button type="primary" @click="handleSearch" style="margin-left: 10px;">搜索</el-button>
          <el-button @click="clearSearch" v-if="searchQuery || searchType">重置</el-button>
        </div>

        <!-- 教师管理员操作栏 -->
        <div v-if="canManage" class="action-bar">
          <el-button type="primary" @click="showContentEditor = true; editingContent = null">
            + 新建内容
          </el-button>
        </div>

        <!-- 内容列表 -->
        <el-row :gutter="20" class="content-grid">
          <el-col
            v-for="content in contents"
            :key="content.id"
            :xs="24"
            :sm="12"
            :md="8"
          >
            <el-card
              shadow="hover"
              class="content-card"
              @click="viewContent(content.id)"
            >
              <div class="content-cover" v-if="content.cover_image">
                <img :src="content.cover_image" :alt="content.title" />
              </div>
              <div class="content-type-tag">
                <el-tag size="small" :type="getTypeTag(content.content_type)">
                  {{ getTypeText(content.content_type) }}
                </el-tag>
              </div>
              <h3 class="content-title">{{ content.title }}</h3>
              <div class="content-meta">
                <span class="meta-item">
                  <el-icon><View /></el-icon>
                  {{ content.view_count }}
                </span>
                <span class="meta-item" v-if="content.is_published">
                  <el-icon><CircleCheck /></el-icon>
                  已发布
                </span>
                <span class="meta-item" v-else>
                  <el-icon><Clock /></el-icon>
                  未发布
                </span>
              </div>
              <!-- 管理操作 -->
              <div v-if="canManage" class="content-actions" @click.stop>
                <el-button size="small" @click="editContent(content)">编辑</el-button>
                <el-button size="small" type="primary" @click="togglePublish(content)">
                  {{ content.is_published ? '取消发布' : '发布' }}
                </el-button>
                <el-button size="small" type="danger" @click="deleteContentItem(content.id)">删除</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="contents.length === 0" description="暂无教学内容" />
      </div>
    </div>

    <!-- 分类编辑对话框 -->
    <el-dialog v-model="showCategoryDialog" title="新建分类" width="400px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" placeholder="如：农作物习性" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input v-model="categoryForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="categoryForm.parent_id" placeholder="选择父分类（可选）" clearable>
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCategoryDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCategory">创建</el-button>
      </template>
    </el-dialog>

    <!-- 内容编辑对话框 -->
    <el-dialog
      v-model="showContentEditor"
      :title="editingContent ? '编辑内容' : '新建内容'"
      width="800px"
    >
      <el-form :model="contentForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="contentForm.title" placeholder="输入标题" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="contentForm.category_id" placeholder="选择分类">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="contentForm.content_type">
            <el-radio label="article">文章</el-radio>
            <el-radio label="video">视频</el-radio>
            <el-radio label="image">图片</el-radio>
            <el-radio label="pdf">PDF</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="封面图">
          <el-input v-model="contentForm.cover_image" placeholder="封面图 URL" />
        </el-form-item>
        <el-form-item label="视频链接" v-if="contentForm.content_type === 'video'">
          <el-input v-model="contentForm.video_url" placeholder="视频 URL" />
        </el-form-item>
        <el-form-item label="内容" v-if="contentForm.content_type === 'article'">
          <el-input
            v-model="contentForm.content"
            type="textarea"
            :rows="10"
            placeholder="输入文章内容（支持 Markdown）"
          />
        </el-form-item>
        <el-form-item label="发布状态">
          <el-switch v-model="contentForm.is_published" active-text="发布" inactive-text="草稿" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showContentEditor = false">取消</el-button>
        <el-button type="primary" @click="submitContent">保存</el-button>
      </template>
    </el-dialog>

    <!-- 内容详情对话框 -->
    <el-dialog
      v-model="showContentDetail"
      :title="currentContent?.title || '内容详情'"
      width="900px"
      @opened="loadContentDetail"
    >
      <div v-if="currentContent" class="content-detail">
        <div class="detail-meta">
          <el-tag :type="getTypeTag(currentContent.content_type)">
            {{ getTypeText(currentContent.content_type) }}
          </el-tag>
          <span class="meta-text">分类：{{ currentContent.category?.name }}</span>
          <span class="meta-text">阅读：{{ currentContent.view_count }}</span>
        </div>
        
        <!-- 视频内容 -->
        <div v-if="currentContent.content_type === 'video' && currentContent.video_url" class="video-container">
          <video :src="currentContent.video_url" controls style="width: 100%; max-height: 500px;"></video>
        </div>
        
        <!-- 文章内容 -->
        <div v-if="currentContent.content_type === 'article'" class="article-content" v-html="formatContent(currentContent.content)">
        </div>

        <!-- 学习进度 -->
        <div class="learning-progress">
          <el-button
            type="primary"
            :disabled="learningRecord?.status === 'completed'"
            @click="markAsComplete"
          >
            {{ learningRecord?.status === 'completed' ? '已完成' : '标记为完成' }}
          </el-button>
          <el-progress
            v-if="learningRecord"
            :percentage="learningRecord.progress_percent"
            :status="learningRecord.status === 'completed' ? 'success' : undefined"
          />
        </div>

        <!-- 评论区 -->
        <div class="comments-section">
          <h4>评论与问答</h4>
          <div class="comment-input">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="3"
              placeholder="写下你的问题或感想..."
            />
            <el-button type="primary" @click="submitComment" style="margin-top: 10px;">发表评论</el-button>
          </div>
          <div class="comment-list">
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <strong>{{ comment.student_name }}</strong>
                <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
              </div>
              <div class="comment-body">{{ comment.comment }}</div>
              <div v-if="comment.teacher_reply" class="teacher-reply">
                <el-tag size="small" type="success">教师回复</el-tag>
                <p>{{ comment.teacher_reply }}</p>
              </div>
            </div>
            <el-empty v-if="comments.length === 0" description="暂无评论" :image-size="50" />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Folder, View, CircleCheck, Clock, Search } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import MarkdownIt from 'markdown-it';
import {
  getCategories,
  getCategoriesTree,
  createCategory,
  updateCategory,
  deleteCategory,
  getContents,
  getContent,
  createContent,
  updateContent,
  deleteContent,
  publishContent,
  getMyLearning,
  startLearning,
  completeLearning,
  getComments,
  addComment,
  getLearningStats,
  getStudentsProgress
} from '../api/teaching';

const router = useRouter();
const userRole = ref(localStorage.getItem('role') || 'student');

// Markdown 渲染
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true
});

// 权限判断
const canManage = computed(() => ['teacher', 'admin'].includes(userRole.value));
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

// 分类相关
const categories = ref<any[]>([]);
const activeCategoryId = ref(0);
const showCategoryDialog = ref(false);
const categoryForm = ref({
  name: '',
  description: '',
  parent_id: undefined as number | undefined
});

// 内容相关
const contents = ref<any[]>([]);
const showContentEditor = ref(false);
const editingContent = ref<any>(null);
const contentForm = ref({
  title: '',
  category_id: 0,
  content_type: 'article',
  content: '',
  video_url: '',
  cover_image: '',
  is_published: false
});

// 内容详情
const showContentDetail = ref(false);
const currentContent = ref<any>(null);
const currentContentId = ref<number | null>(null);
const comments = ref<any[]>([]);
const newComment = ref('');
const learningRecord = ref<any>(null);

// 学习记录
const learningRecords = ref<any[]>([]);

// 搜索相关
const searchQuery = ref('');
const searchType = ref('');

// 统计相关（教师端）
const showStatsDialog = ref(false);
const stats = ref<any>({
  total_students: 0,
  total_contents: 0,
  total_learning_records: 0,
  completed_count: 0,
  in_progress_count: 0,
  not_started_count: 0,
  completion_rate: 0,
  average_progress: 0
});
const studentsProgress = ref<any[]>([]);

// 加载统计
const loadStats = async () => {
  if (!canManage.value) return;
  try {
    stats.value = await getLearningStats();
    studentsProgress.value = await getStudentsProgress();
  } catch (error) {
    console.error('加载统计失败:', error);
  }
};

// 加载数据
const loadCategories = async () => {
  try {
    categories.value = await getCategories();
  } catch (error) {
    console.error('加载分类失败:', error);
  }
};

const loadContents = async () => {
  try {
    const params: any = {};
    if (activeCategoryId.value) params.category_id = activeCategoryId.value;
    if (searchType.value) params.content_type = searchType.value;
    if (searchQuery.value) params.search = searchQuery.value;
    contents.value = await getContents(params);
  } catch (error) {
    console.error('加载内容失败:', error);
  }
};

const loadLearningRecords = async () => {
  if (userRole.value === 'student') {
    try {
      learningRecords.value = await getMyLearning();
    } catch (error) {
      console.error('加载学习记录失败:', error);
    }
  }
};

// 分类选择
const handleCategorySelect = (index: string) => {
  activeCategoryId.value = parseInt(index);
  loadContents();
};

// 类型标签
const getTypeTag = (type: string) => {
  const map: Record<string, any> = {
    article: '',
    video: 'warning',
    image: 'success',
    pdf: 'danger'
  };
  return map[type] || '';
};

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    article: '文章',
    video: '视频',
    image: '图片',
    pdf: 'PDF'
  };
  return map[type] || type;
};

// 分类管理
const submitCategory = async () => {
  if (!categoryForm.value.name) {
    ElMessage.warning('请输入分类名称');
    return;
  }
  try {
    await createCategory(categoryForm.value);
    ElMessage.success('分类创建成功');
    showCategoryDialog.value = false;
    loadCategories();
    categoryForm.value = { name: '', description: '', parent_id: undefined };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败');
  }
};

// 内容管理
const editContent = (content: any) => {
  editingContent.value = content;
  contentForm.value = {
    title: content.title,
    category_id: content.category_id,
    content_type: content.content_type,
    content: content.content || '',
    video_url: content.video_url || '',
    cover_image: content.cover_image || '',
    is_published: content.is_published
  };
  showContentEditor.value = true;
};

const submitContent = async () => {
  if (!contentForm.value.title || !contentForm.value.category_id) {
    ElMessage.warning('请填写必填项');
    return;
  }
  try {
    if (editingContent.value) {
      await updateContent(editingContent.value.id, contentForm.value);
      ElMessage.success('更新成功');
    } else {
      await createContent(contentForm.value);
      ElMessage.success('创建成功');
    }
    showContentEditor.value = false;
    loadContents();
    editingContent.value = null;
    contentForm.value = {
      title: '',
      category_id: 0,
      content_type: 'article',
      content: '',
      video_url: '',
      cover_image: '',
      is_published: false
    };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  }
};

const togglePublish = async (content: any) => {
  try {
    await publishContent(content.id);
    ElMessage.success('操作成功');
    loadContents();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败');
  }
};

const deleteContentItem = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此内容吗？', '确认删除', {
      type: 'warning'
    });
    await deleteContent(id);
    ElMessage.success('删除成功');
    loadContents();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败');
    }
  }
};

// 内容详情
const viewContent = async (id: number) => {
  currentContentId.value = id;
  showContentDetail.value = true;
};

const loadContentDetail = async () => {
  if (!currentContentId.value) return;
  try {
    currentContent.value = await getContent(currentContentId.value);
    comments.value = await getComments(currentContentId.value);
    
    // 开始学习
    await startLearning(currentContentId.value);
    
    // 加载学习记录
    const records = await getMyLearning();
    learningRecord.value = records.find(r => r.content_id === currentContentId.value);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载失败');
  }
};

const markAsComplete = async () => {
  if (!currentContentId.value) return;
  try {
    await completeLearning(currentContentId.value);
    learningRecord.value = { ...learningRecord.value, status: 'completed', progress_percent: 100 };
    ElMessage.success('已标记为完成');
    loadLearningRecords();
  } catch (error: any) {
    ElMessage.error('操作失败');
  }
};

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容');
    return;
  }
  if (!currentContentId.value) return;
  try {
    await addComment(currentContentId.value, newComment.value);
    ElMessage.success('评论成功');
    newComment.value = '';
    comments.value = await getComments(currentContentId.value);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '评论失败');
  }
};

// 工具函数
const formatDuration = (seconds: number): string => {
  if (!seconds) return '0 分钟';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  }
  return `${minutes}分钟`;
};

const getContentTitle = (contentId: number) => {
  const content = contents.value.find(c => c.id === contentId);
  return content?.title || `内容 #${contentId}`;
};

const formatContent = (content?: string) => {
  if (!content) return '<p>暂无内容</p>';
  // 使用 Markdown 渲染
  return md.render(content);
};

const handleSearch = () => {
  loadContents();
};

const clearSearch = () => {
  searchQuery.value = '';
  searchType.value = '';
  loadContents();
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN');
};

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  router.push('/login');
};

onMounted(() => {
  loadCategories();
  loadContents();
  loadLearningRecords();
  loadStats();
});
</script>

<style scoped>
.teaching-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  display: flex;
  padding: 20px;
  gap: 20px;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.mt-4 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.learning-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.learning-item {
  cursor: pointer;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.learning-item:hover {
  background-color: #f5f5f5;
}

.learning-title {
  font-size: 14px;
  margin-bottom: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.action-bar {
  margin-bottom: 20px;
}

.content-grid {
  margin-top: 20px;
}

.content-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.2s;
}

.content-card:hover {
  transform: translateY(-4px);
}

.content-cover {
  height: 140px;
  overflow: hidden;
  border-radius: 4px;
  margin: -16px -16px 0;
  background: #f0f0f0;
}

.content-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.content-type-tag {
  margin-top: 10px;
}

.content-title {
  font-size: 16px;
  margin: 10px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.content-meta {
  display: flex;
  gap: 15px;
  color: #999;
  font-size: 13px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stats-grid {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px 0;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.content-actions {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.content-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-meta {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.meta-text {
  color: #666;
  font-size: 14px;
}

.video-container {
  margin: 20px 0;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.article-content {
  line-height: 1.8;
  font-size: 16px;
  padding: 20px 0;
}

/* Markdown 样式 */
.article-content :deep(h1),
.article-content :deep(h2),
.article-content :deep(h3),
.article-content :deep(h4) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: #333;
}

.article-content :deep(h1) {
  font-size: 24px;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eee;
}

.article-content :deep(h2) {
  font-size: 20px;
  padding-bottom: 0.25em;
  border-bottom: 1px solid #eee;
}

.article-content :deep(h3) {
  font-size: 16px;
}

.article-content :deep(p) {
  margin-top: 0;
  margin-bottom: 16px;
}

.article-content :deep(ul),
.article-content :deep(ol) {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

.article-content :deep(li) {
  margin-top: 4px;
}

.article-content :deep(li + li) {
  margin-top: 0.25em;
}

.article-content :deep(table) {
  border-collapse: collapse;
  margin: 16px 0;
  width: 100%;
  overflow: auto;
}

.article-content :deep(th),
.article-content :deep(td) {
  padding: 8px 12px;
  border: 1px solid #ddd;
  text-align: left;
}

.article-content :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.article-content :deep(tr:nth-child(2n)) {
  background-color: #f8f9fa;
}

.article-content :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

.article-content :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
}

.article-content :deep(pre code) {
  display: inline;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.article-content :deep(blockquote) {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 16px 0;
}

.article-content :deep(blockquote > :first-child) {
  margin-top: 0;
}

.article-content :deep(blockquote > :last-child) {
  margin-bottom: 0;
}

.article-content :deep(hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}

.article-content :deep(strong) {
  font-weight: 600;
}

.learning-progress {
  margin: 20px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.comments-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #eee;
}

.comments-section h4 {
  margin-bottom: 15px;
}

.comment-input {
  margin-bottom: 20px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.comment-item {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.comment-time {
  color: #999;
  font-size: 13px;
}

.comment-body {
  line-height: 1.6;
  margin-bottom: 10px;
}

.teacher-reply {
  margin-top: 10px;
  padding: 10px;
  background: #e8f5e9;
  border-radius: 4px;
}

.teacher-reply p {
  margin: 8px 0 0;
}
</style>
