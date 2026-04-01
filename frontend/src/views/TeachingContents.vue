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
        <NotificationBell />
        <el-button @click="$router.push('/')">返回工作台</el-button>
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
              <el-progress type="dashboard" :percentage="progressDistribution.completed" status="success" :format="() => `已完成 ${stats.completed_count}`" />
            </el-col>
            <el-col :span="8">
              <el-progress type="dashboard" :percentage="progressDistribution.inProgress" status="warning" :format="() => `进行中 ${stats.in_progress_count}`" />
            </el-col>
            <el-col :span="8">
              <el-progress type="dashboard" :percentage="progressDistribution.notStarted" status="exception" :format="() => `未开始 ${stats.not_started_count}`" />
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
        <!-- 顶部筛选 -->
        <div class="search-bar app-glass-card">
          <el-input
            v-model="searchQuery"
            placeholder="搜索教学内容..."
            clearable
            @keyup.enter="handleSearch"
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select v-model="activeCategoryId" placeholder="全部分类" class="search-select" @change="loadContents">
            <el-option label="全部分类" :value="0" />
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>

          <el-select v-model="searchType" placeholder="全部类型" clearable class="search-select">
            <el-option label="文章" value="article" />
            <el-option label="视频" value="video" />
            <el-option label="图片" value="image" />
            <el-option label="PDF" value="pdf" />
          </el-select>

          <el-button type="primary" round @click="handleSearch">搜索</el-button>
          <el-button round @click="clearSearch" v-if="searchQuery || searchType || activeCategoryId">重置</el-button>
        </div>

        <!-- 教师管理员操作栏 -->
        <div v-if="canManage" class="action-bar">
          <el-button type="primary" @click="showContentEditor = true; editingContent = null">
            + 新建内容
          </el-button>
        </div>

        <!-- 内容卡片流 -->
        <div v-if="contents.length > 0" class="content-waterfall">
          <article
            v-for="content in contents"
            :key="content.id"
            class="content-card app-glass-card"
            @click="viewContent(content.id)"
          >
            <div class="card-cover" :class="`type-${content.content_type}`">
              <template v-if="content.content_type === 'video' && content.cover_image">
                <img :src="resolveAssetUrl(content.cover_image)" :alt="content.title" />
              </template>
              <template v-if="content.content_type === 'video'">
                <div class="play-overlay">
                  <el-icon :size="26"><VideoPlay /></el-icon>
                </div>
              </template>
              <template v-else-if="content.content_type === 'article'">
                <div class="article-cover-default">
                  <span class="leaf-icon">🌿</span>
                  <span>自然科学小课堂</span>
                </div>
              </template>
              <template v-else-if="content.cover_image">
                <img :src="resolveAssetUrl(content.cover_image)" :alt="content.title" />
              </template>
              <template v-else>
                <div class="generic-cover">📘 教学资源</div>
              </template>

              <div v-if="canManage" class="manager-overlay" @click.stop>
                <el-button circle size="small" @click="editContent(content)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button circle size="small" type="danger" plain @click="deleteContentItem(content.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <div class="card-body">
              <h3 class="content-title">{{ content.title }}</h3>
              <p class="content-summary">{{ getContentSummary(content) }}</p>
            </div>

            <div class="card-footer">
              <div class="footer-left">
                <el-tag size="small" :type="getTypeTag(content.content_type)">{{ getTypeText(content.content_type) }}</el-tag>
                <span class="duration">{{ estimateDurationText(content) }}</span>
              </div>
              <div v-if="userRole === 'student'" class="footer-right progress-inline">
                <span class="progress-blocks">{{ getProgressBlocks(getContentProgress(content.id)) }}</span>
                <span class="progress-text">{{ getContentProgress(content.id) }}%</span>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="empty-content-state app-glass-card">
          <div class="empty-plant">🌱</div>
          <h3>这里还没有找到教学内容</h3>
          <p>{{ searchQuery || searchType || activeCategoryId ? '换个关键词或分类试试吧。' : '老师正在准备有趣的科学内容，稍后回来看看。' }}</p>
          <el-button type="primary" round @click="handleEmptyAction">去学习</el-button>
        </div>
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
                <div class="comment-author">
                  <el-avatar :size="28" :src="resolveAssetUrl(comment.student_avatar_url)">{{ (comment.student_name || '?').slice(0, 1) }}</el-avatar>
                  <strong>{{ comment.student_name }}</strong>
                </div>
                <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
              </div>
              <div class="comment-body">{{ comment.comment }}</div>
              <div class="comment-actions">
                <el-button text size="small" @click="startReply(comment.id)">回复</el-button>
                <el-button text size="small" @click="toggleLike(comment)">
                  {{ comment.liked ? '取消点赞' : '点赞' }} ({{ comment.like_count || 0 }})
                </el-button>
              </div>

              <div v-if="replyingCommentId === comment.id" class="reply-input">
                <el-input
                  v-model="replyText"
                  type="textarea"
                  :rows="2"
                  placeholder="写下你的回复..."
                />
                <div class="reply-actions">
                  <el-button size="small" @click="cancelReply">取消</el-button>
                  <el-button type="primary" size="small" @click="submitReply(comment.id)">发送回复</el-button>
                </div>
              </div>

              <div v-if="comment.replies && comment.replies.length > 0" class="reply-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <div class="comment-header">
                    <div class="comment-author">
                      <el-avatar :size="24" :src="resolveAssetUrl(reply.student_avatar_url)">{{ (reply.student_name || '?').slice(0, 1) }}</el-avatar>
                      <strong>{{ reply.student_name }}</strong>
                    </div>
                    <span class="comment-time">{{ formatDate(reply.created_at) }}</span>
                  </div>
                  <div class="comment-body">{{ reply.comment }}</div>
                  <div class="comment-actions">
                    <el-button text size="small" @click="toggleLike(reply)">
                      {{ reply.liked ? '取消点赞' : '点赞' }} ({{ reply.like_count || 0 }})
                    </el-button>
                  </div>
                </div>
              </div>

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
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Folder, Search, VideoPlay, Edit, Delete } from '@element-plus/icons-vue';
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
  replyComment,
  toggleCommentLike,
  getLearningStats,
  getStudentsProgress
} from '../api/teaching';
import NotificationBell from '../components/NotificationBell.vue';

const router = useRouter();
const route = useRoute();
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
const replyingCommentId = ref<number | null>(null);
const replyText = ref('');
const learningRecord = ref<any>(null);

// 学习记录
const learningRecords = ref<any[]>([]);
const learningProgressMap = computed(() => {
  const map = new Map<number, number>();
  for (const record of learningRecords.value) {
    map.set(record.content_id, Number(record.progress_percent || 0));
  }
  return map;
});

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

const progressDistribution = computed(() => {
  const total = stats.value.total_learning_records || (
    (stats.value.completed_count || 0) +
    (stats.value.in_progress_count || 0) +
    (stats.value.not_started_count || 0)
  );
  if (!total) {
    return { completed: 0, inProgress: 0, notStarted: 0 };
  }
  const completed = Math.round((stats.value.completed_count / total) * 100);
  const inProgress = Math.round((stats.value.in_progress_count / total) * 100);
  const notStarted = Math.max(0, 100 - completed - inProgress);
  return { completed, inProgress, notStarted };
});

// 加载统计
const loadStats = async () => {
  if (!canManage.value) return;
  try {
    stats.value = await getLearningStats();
    studentsProgress.value = await getStudentsProgress();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '学习统计加载失败');
  }
};

// 加载数据
const loadCategories = async () => {
  try {
    categories.value = await getCategories();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载分类失败');
  }
};

const loadContents = async () => {
  try {
    const params: any = {};
    if (activeCategoryId.value) params.category_id = activeCategoryId.value;
    if (searchType.value) params.content_type = searchType.value;
    if (searchQuery.value) params.search = searchQuery.value;
    const response = await getContents(params);
    contents.value = Array.isArray(response) ? response : (response?.items || []);
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载内容失败');
  }
};

const loadLearningRecords = async () => {
  if (userRole.value === 'student') {
    try {
      learningRecords.value = await getMyLearning();
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '加载学习记录失败');
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
    await loadComments();
    
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
    ElMessage.error(error.response?.data?.detail || '操作失败');
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
    await loadComments();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '评论失败');
  }
};

const loadComments = async () => {
  if (!currentContentId.value) return;
  comments.value = await getComments(currentContentId.value);
};

const startReply = (commentId: number) => {
  replyingCommentId.value = commentId;
  replyText.value = '';
};

const cancelReply = () => {
  replyingCommentId.value = null;
  replyText.value = '';
};

const submitReply = async (commentId: number) => {
  if (!replyText.value.trim()) {
    ElMessage.warning('请输入回复内容');
    return;
  }
  try {
    await replyComment(commentId, replyText.value);
    ElMessage.success('回复成功');
    cancelReply();
    await loadComments();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '回复失败');
  }
};

const toggleLike = async (comment: any) => {
  try {
    const result = await toggleCommentLike(comment.id);
    comment.liked = result.liked;
    comment.like_count = result.like_count;
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '点赞操作失败');
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

const stripText = (value?: string) => {
  if (!value) return '';
  return value
    .replace(/<[^>]*>/g, ' ')
    .replace(/[\r\n]+/g, ' ')
    .replace(/[#>*`_\-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

const getContentSummary = (content: any) => {
  if (content.content_type === 'video') {
    return stripText(content.content) || '点击进入视频学习，边看边思考科学问题。';
  }
  if (content.content_type === 'article') {
    return stripText(content.content) || '一篇图文内容，适合课后自主阅读。';
  }
  if (content.content_type === 'pdf') {
    return '文档资料，适合下载后结合课堂讲解学习。';
  }
  if (content.content_type === 'image') {
    return '图片资料，适合观察现象与记录细节。';
  }
  return '点击查看完整教学内容。';
};

const estimateDurationText = (content: any) => {
  if (content.content_type === 'video') return '约 8 分钟';
  const plain = stripText(content.content);
  const minutes = Math.max(1, Math.ceil(plain.length / 220));
  return `约 ${minutes} 分钟`;
};

const getContentProgress = (contentId: number) => {
  return learningProgressMap.value.get(contentId) || 0;
};

const getProgressBlocks = (percent: number) => {
  const filled = Math.max(0, Math.min(5, Math.round(percent / 20)));
  return `${'▓'.repeat(filled)}${'░'.repeat(5 - filled)}`;
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
  activeCategoryId.value = 0;
  loadContents();
};

const handleEmptyAction = () => {
  clearSearch();
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN');
};

const resolveAssetUrl = (url?: string) => {
  if (!url) return '';
  if (/^https?:\/\//i.test(url)) return url;
  return `http://localhost:8000${url}`;
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

watch(
  () => route.query.content_id,
  (value) => {
    const queryContentId = Number(value);
    if (!Number.isNaN(queryContentId) && queryContentId > 0) {
      viewContent(queryContentId);
    }
  },
  { immediate: true }
);
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


.content-waterfall {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
  align-items: start;
}

.content-card {
  position: relative;
  cursor: pointer;
  border-radius: 16px;
  border: 1px solid rgba(58, 137, 91, 0.16);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.content-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 30px rgba(21, 65, 42, 0.16);
}

.card-cover {
  position: relative;
  height: 160px;
  background: #eef5f0;
  overflow: hidden;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-cover.type-video {
  background: linear-gradient(145deg, #0d2f44 0%, #1e6b8d 100%);
}

.card-cover.type-article {
  background: linear-gradient(140deg, #d9f3e2 0%, #bbdfca 100%);
}

.article-cover-default,
.generic-cover {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #214f35;
  font-weight: 700;
}

.leaf-icon {
  font-size: 34px;
}

.generic-cover {
  color: #4d6659;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #ffffff;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.12), rgba(0, 0, 0, 0.28));
}

.manager-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.content-card:hover .manager-overlay {
  opacity: 1;
  transform: translateY(0);
}

.card-body {
  padding: 12px 14px 4px;
}

.content-title {
  font-size: 16px;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 44px;
}

.content-summary {
  margin: 8px 0 0;
  color: #60776b;
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 14px 14px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration {
  font-size: 12px;
  color: #6f8578;
}

.progress-inline {
  display: flex;
  align-items: center;
  gap: 6px;
}

.progress-blocks {
  font-size: 11px;
  letter-spacing: 1px;
  color: #2d7a4d;
}

.progress-text {
  font-size: 12px;
  color: #4f6b5c;
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

.search-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(58, 137, 91, 0.14);
}

.search-input {
  width: 320px;
  max-width: 100%;
}

.search-select {
  width: 150px;
}

.search-bar :deep(.el-input__wrapper),
.search-bar :deep(.el-select__wrapper) {
  border-radius: 999px;
}

.empty-content-state {
  margin-top: 18px;
  border-radius: 18px;
  border: 1px dashed rgba(45, 122, 77, 0.35);
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 10px;
  padding: 24px;
}

.empty-plant {
  font-size: 48px;
}

.empty-content-state h3 {
  margin: 0;
  color: #2b5840;
}

.empty-content-state p {
  margin: 0;
  color: #638073;
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
  align-items: center;
  margin-bottom: 10px;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-time {
  color: #999;
  font-size: 13px;
}

.comment-body {
  line-height: 1.6;
  margin-bottom: 10px;
}

.comment-actions {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.reply-input {
  margin-top: 8px;
  margin-bottom: 8px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.reply-list {
  margin-top: 10px;
  padding-left: 12px;
  border-left: 2px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply-item {
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 10px;
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

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
    padding: 12px;
  }

  .sidebar {
    width: 100%;
  }

  .search-input,
  .search-select {
    width: 100%;
  }

  .search-bar :deep(.el-button) {
    width: 100%;
  }

  .content-waterfall {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }
}

@media (max-width: 520px) {
  .content-waterfall {
    grid-template-columns: 1fr;
  }
}
</style>
