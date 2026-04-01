<template>
  <div class="plants-page">
    <!-- 顶部导航 -->
    <AppTopBar title="🌱 植物档案" :roleTagType="roleTagType" :roleText="userRoleText">
      <template #extra-actions>
        <el-button type="primary" @click="showPlantDialog = true" v-if="isTeacher">
          <el-icon><Plus /></el-icon> 创建档案
        </el-button>
      </template>
    </AppTopBar>

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
            <el-form-item label="状态">
              <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 100%">
                <el-option label="生长中" value="growing" />
                <el-option label="已收获" value="harvested" />
                <el-option label="已枯萎" value="withered" />
              </el-select>
            </el-form-item>
            <el-button type="primary" style="width: 100%" @click="loadPlants">查询</el-button>
          </el-form>
        </el-card>
      </div>

      <!-- 右侧植物列表 -->
      <div class="content-area">
        <div class="plant-grid" v-loading="loading">
          <StatusPanel
            v-if="pageErrorDetail"
            :description="pageErrorDetail"
            :actionText="pageErrorActionText"
            :actionRoute="pageErrorActionRoute"
          />

          <el-card
            v-for="plant in plants"
            :key="plant.id"
            class="plant-card"
            shadow="hover"
            @click="viewPlant(plant)"
          >
            <div class="plant-image">
              <img v-if="plant.cover_image" :src="resolveImageUrl(plant.cover_image)" class="cover-img" alt="植物封面" />
              <div v-else class="image-placeholder">
                <el-icon :size="60"><Picture /></el-icon>
              </div>
            </div>
            <h3 class="plant-name">{{ plant.plant_name }}</h3>
            <p class="plant-species">{{ plant.species || '未指定品种' }}</p>
            <div class="plant-meta">
              <span>📊 {{ plant.growth_record_count }} 条记录</span>
              <span :class="['status-tag', plant.status]">
                {{ getStatusText(plant.status) }}
              </span>
            </div>
          </el-card>

          <StatusPanel
            v-if="!pageErrorDetail && !loading && plants.length === 0"
            :description="isTeacher ? '暂无班级植物档案' : '暂无可查看的植物档案'"
            :actionText="isTeacher ? '创建档案' : '去个人中心'"
            :actionRoute="isTeacher ? undefined : '/profile'"
            :actionCallback="isTeacher ? () => (showPlantDialog = true) : undefined"
          />
        </div>
      </div>
    </div>

    <!-- 创建档案对话框 -->
    <el-dialog v-model="showPlantDialog" title="创建植物档案" width="550px" :close-on-click-modal="false">
      <el-form :model="plantForm" label-width="100px" ref="plantFormRef">
        <el-form-item label="植物名称" required>
          <el-input v-model="plantForm.plant_name" placeholder="如：番茄 01 号" />
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="plantForm.species" placeholder="如：樱桃番茄" />
        </el-form-item>
        <el-form-item label="所属班级">
          <el-select v-model="plantForm.class_id" placeholder="选择班级" style="width: 100%">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.class_name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联设备">
          <el-select v-model="plantForm.device_id" placeholder="选择设备" clearable style="width: 100%">
            <el-option
              v-for="device in devices"
              :key="device.id"
              :label="device.device_name"
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="种植日期">
          <el-date-picker
            v-model="plantForm.plant_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="预期收获">
          <el-date-picker
            v-model="plantForm.expected_harvest_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="plantForm.status" style="width: 100%">
            <el-option label="生长中" value="growing" />
            <el-option label="已收获" value="harvested" />
            <el-option label="已枯萎" value="withered" />
          </el-select>
        </el-form-item>
        <el-form-item label="封面图片">
          <el-upload
            :show-file-list="false"
            :http-request="handleCoverUpload"
            accept="image/*"
          >
            <el-button :loading="uploadingCover" type="primary" plain>上传图片</el-button>
          </el-upload>
          <div v-if="plantForm.cover_image" class="cover-preview-wrap">
            <img :src="resolveImageUrl(plantForm.cover_image)" class="cover-preview" alt="封面预览" />
          </div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="plantForm.description"
            type="textarea"
            :rows="3"
            placeholder="植物描述..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPlantDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPlant" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 植物详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="植物详情" width="900px" :close-on-click-modal="false">
      <div v-if="currentPlant" class="plant-detail">
        <el-row :gutter="20">
          <!-- 左侧：植物信息 -->
          <el-col :span="10">
            <div class="plant-info">
              <div class="info-avatar">
                <img v-if="currentPlant.cover_image" :src="resolveImageUrl(currentPlant.cover_image)" class="detail-cover-img" alt="植物封面" />
                <el-icon v-else :size="80"><Picture /></el-icon>
              </div>
              <h3>{{ currentPlant.plant_name }}</h3>
              <p class="species">{{ currentPlant.species }}</p>
              <div class="info-list">
                <p><strong>班级：</strong>{{ currentPlant.class_name || '-' }}</p>
                <p><strong>设备：</strong>{{ currentPlant.device_name || '-' }}</p>
                <p><strong>种植日期：</strong>{{ currentPlant.plant_date || '-' }}</p>
                <p><strong>状态：</strong>{{ getStatusText(currentPlant.status) }}</p>
                <p v-if="currentPlant.description"><strong>描述：</strong>{{ currentPlant.description }}</p>
              </div>
            </div>
          </el-col>

          <!-- 右侧：生长记录 -->
          <el-col :span="14">
            <div class="growth-records">
              <div class="records-header">
                <h4>📈 生长记录</h4>
                <el-button type="primary" size="small" @click="showRecordDialog = true" v-if="!isTeacher">
                  <el-icon><Plus /></el-icon> 添加记录
                </el-button>
              </div>
              <el-timeline>
                <el-timeline-item
                  v-for="record in records"
                  :key="record.id"
                  :timestamp="record.record_date"
                  placement="top"
                >
                  <el-card>
                    <div class="record-content">
                      <div class="record-stage">
                        <el-tag :type="getStageType(record.stage)" size="small">
                          {{ getStageText(record.stage) }}
                        </el-tag>
                      </div>
                      <div class="record-data" v-if="record.height_cm || record.leaf_count">
                        <span v-if="record.height_cm">📏 {{ record.height_cm }} cm</span>
                        <span v-if="record.leaf_count">🍃 {{ record.leaf_count }} 叶</span>
                        <span v-if="record.flower_count">🌸 {{ record.flower_count }} 花</span>
                        <span v-if="record.fruit_count">🍎 {{ record.fruit_count }} 果</span>
                      </div>
                      <p class="record-desc">{{ record.description || '无描述' }}</p>
                      <p class="record-author">记录人：{{ record.recorder_name }}</p>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
              <StatusPanel
                v-if="recordErrorDetail"
                :description="recordErrorDetail"
                :actionText="recordErrorActionText"
                :actionRoute="recordErrorActionRoute"
              />

              <StatusPanel
                v-else-if="records.length === 0"
                description="暂无生长记录"
                :actionText="!isTeacher ? '添加记录' : undefined"
                :actionCallback="!isTeacher ? () => (showRecordDialog = true) : undefined"
              />
            </div>
          </el-col>
        </el-row>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加记录对话框 -->
    <el-dialog v-model="showRecordDialog" title="添加生长记录" width="500px" :close-on-click-modal="false">
      <el-form :model="recordForm" label-width="100px">
        <el-form-item label="记录日期">
          <el-date-picker
            v-model="recordForm.record_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="生长阶段">
          <el-select v-model="recordForm.stage" placeholder="选择阶段" style="width: 100%">
            <el-option label="种子" value="seed" />
            <el-option label="发芽" value="sprout" />
            <el-option label="幼苗" value="seedling" />
            <el-option label="开花" value="flowering" />
            <el-option label="结果" value="fruiting" />
            <el-option label="收获" value="harvested" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="高度 (cm)">
              <el-input-number v-model="recordForm.height_cm" :min="0" :max="500" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="叶片数">
              <el-input-number v-model="recordForm.leaf_count" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="花朵数">
              <el-input-number v-model="recordForm.flower_count" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="果实数">
              <el-input-number v-model="recordForm.fruit_count" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述">
          <el-input
            v-model="recordForm.description"
            type="textarea"
            :rows="3"
            placeholder="观察描述..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRecordDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRecord" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Plus, Filter, Picture } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { FormInstance, UploadRequestOptions } from 'element-plus';
import StatusPanel from '../components/StatusPanel.vue';
import apiClient from '../api';
import {
  uploadPlantImage,
  getPlants,
  createPlant,
  getPlantRecords,
  createPlantRecord,
} from '../api/plants';
import { getClasses } from '../api/classes';
import { getDevices } from '../api/devices';
import { useCurrentUser } from '../composables/useCurrentUser';
import AppTopBar from '../components/AppTopBar.vue';

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

// 数据
const plants = ref<any[]>([]);
const classes = ref<any[]>([]);
const devices = ref<any[]>([]);
const records = ref<any[]>([]);
const loading = ref(false);
const submitting = ref(false);
const uploadingCover = ref(false);

const toLocalDateString = (input: Date = new Date()) => {
  const y = input.getFullYear();
  const m = `${input.getMonth() + 1}`.padStart(2, '0');
  const d = `${input.getDate()}`.padStart(2, '0');
  return `${y}-${m}-${d}`;
};

// 页面级错误/空状态引导（403/401）
const pageErrorDetail = ref<string>('');
const pageErrorActionText = ref<string>('');
const pageErrorActionRoute = ref<string>('');

const recordErrorDetail = ref<string>('');
const recordErrorActionText = ref<string>('');
const recordErrorActionRoute = ref<string>('');

// 筛选
const filterForm = ref({
  class_id: undefined as number | undefined,
  status: undefined as string | undefined
});

// 对话框
const showPlantDialog = ref(false);
const showDetailDialog = ref(false);
const showRecordDialog = ref(false);
const currentPlant = ref<any>(null);
const plantFormRef = ref<FormInstance>();

// 表单
const plantForm = ref({
  plant_name: '',
  species: '',
  class_id: undefined as number | undefined,
  device_id: undefined as number | undefined,
  plant_date: undefined as string | undefined,
  expected_harvest_date: undefined as string | undefined,
  status: 'growing',
  cover_image: '',
  description: ''
});

const recordForm = ref({
  record_date: toLocalDateString(),
  stage: 'seedling',
  height_cm: undefined as number | undefined,
  leaf_count: undefined as number | undefined,
  flower_count: undefined as number | undefined,
  fruit_count: undefined as number | undefined,
  description: ''
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

const loadPlants = async (showError = true): Promise<boolean> => {
  loading.value = true;
  pageErrorDetail.value = '';
  pageErrorActionText.value = '';
  pageErrorActionRoute.value = '';
  try {
    const params: any = {};
    if (filterForm.value.class_id) params.class_id = filterForm.value.class_id;
    if (filterForm.value.status) params.status = filterForm.value.status;
    plants.value = await getPlants(params);
    return true;
  } catch (error: any) {
    if (showError) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail || '加载失败';
      if (status === 401) {
        pageErrorDetail.value = '未登录或登录已过期，请重新登录。';
        pageErrorActionText.value = '去登录';
        pageErrorActionRoute.value = '/login';
      } else if (status === 403) {
        pageErrorDetail.value = '你无权访问该班级的植物档案，请检查账号/班级分配后重试。';
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

// 查看植物详情
const viewPlant = async (plant: any) => {
  currentPlant.value = plant;
  showDetailDialog.value = true;
  recordErrorDetail.value = '';
  recordErrorActionText.value = '';
  recordErrorActionRoute.value = '';
  try {
    records.value = await getPlantRecords(plant.id);
  } catch (error) {
    const status = (error as any)?.response?.status;
    const detail = (error as any)?.response?.data?.detail || '加载记录失败';
    if (status === 401) {
      recordErrorDetail.value = '未登录或登录已过期，请重新登录。';
      recordErrorActionText.value = '去登录';
      recordErrorActionRoute.value = '/login';
    } else if (status === 403) {
      recordErrorDetail.value = '你无权访问该植物的生长记录，请检查账号/班级分配后重试。';
      recordErrorActionText.value = '查看个人中心';
      recordErrorActionRoute.value = '/profile';
    } else {
      recordErrorDetail.value = detail;
    }
  }
};

// 创建植物档案
const submitPlant = async () => {
  if (!plantForm.value.plant_name) {
    ElMessage.warning('请输入植物名称');
    return;
  }

  submitting.value = true;
  try {
    await createPlant(plantForm.value);
    const loaded = await loadPlants(false);
    if (loaded) {
      ElMessage.success('档案创建成功');
    } else {
      ElMessage.warning('档案创建成功，但列表刷新失败，请稍后手动刷新');
    }
    showPlantDialog.value = false;
    plantForm.value = {
      plant_name: '',
      species: '',
      class_id: undefined,
      device_id: undefined,
      plant_date: undefined,
      expected_harvest_date: undefined,
      status: 'growing',
      cover_image: '',
      description: ''
    };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败');
  } finally {
    submitting.value = false;
  }
};

const handleCoverUpload = async (options: UploadRequestOptions) => {
  uploadingCover.value = true;
  try {
    const file = options.file as File;
    const res = await uploadPlantImage(file);
    plantForm.value.cover_image = res.url;
    options.onSuccess?.(res as any);
    ElMessage.success('封面上传成功');
  } catch (error: any) {
    options.onError?.(error);
    ElMessage.error(error.response?.data?.detail || '封面上传失败');
  } finally {
    uploadingCover.value = false;
  }
};

const resolveImageUrl = (url?: string) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const base = (apiClient.defaults.baseURL || '').replace(/\/api\/?$/, '');
  return `${base}${url}`;
};

// 添加生长记录
const submitRecord = async () => {
  if (!currentPlant.value) return;

  submitting.value = true;
  try {
    await createPlantRecord(currentPlant.value.id, recordForm.value);
    ElMessage.success('记录添加成功');
    showRecordDialog.value = false;
    viewPlant(currentPlant.value);
    recordForm.value = {
      record_date: toLocalDateString(),
      stage: 'seedling',
      height_cm: undefined,
      leaf_count: undefined,
      flower_count: undefined,
      fruit_count: undefined,
      description: ''
    };
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败');
  } finally {
    submitting.value = false;
  }
};

// 辅助函数
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    growing: '生长中',
    harvested: '已收获',
    withered: '已枯萎'
  };
  return map[status] || status;
};

const getStageText = (stage?: string) => {
  const map: Record<string, string> = {
    seed: '种子',
    sprout: '发芽',
    seedling: '幼苗',
    flowering: '开花',
    fruiting: '结果',
    harvested: '收获'
  };
  return map[stage || ''] || stage || '';
};

const getStageType = (stage?: string) => {
  const map: Record<string, any> = {
    seed: 'info',
    sprout: 'success',
    seedling: 'success',
    flowering: 'warning',
    fruiting: 'danger',
    harvested: 'success'
  };
  return map[stage || ''] || '';
};

onMounted(async () => {
  try {
    await ensureLoaded();
  } catch {
    // 401/403 会由全局拦截器/页面状态面板处理
  }
  await loadClasses();
  await loadDevices();
  await loadPlants();
});
</script>

<style scoped>
.plants-page {
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

.filter-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.content-area {
  flex: 1;
  min-width: 0;
}

.plant-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.plant-card {
  cursor: pointer;
  transition: transform 0.2s;
  text-align: center;
}

.plant-card:hover {
  transform: translateY(-4px);
}

.plant-image {
  height: 150px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px 8px 0 0;
  margin: -16px -16px 0 -16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-placeholder {
  color: white;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px 8px 0 0;
}

.cover-preview-wrap {
  margin-top: 8px;
}

.cover-preview {
  width: 120px;
  height: 90px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid #dcdfe6;
}

.plant-name {
  margin: 12px 0 4px;
  font-size: 16px;
  color: #303133;
}

.plant-species {
  margin: 0 0 12px;
  font-size: 13px;
  color: #909399;
}

.plant-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #909399;
}

.status-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.growing {
  background: #f0f9ff;
  color: #409EFF;
}

.status-tag.harvested {
  background: #f0fff9;
  color: #67C23A;
}

.status-tag.withered {
  background: #fef0f0;
  color: #F56C6C;
}

.plant-detail {
  padding: 20px;
}

.plant-info {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.info-avatar {
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.info-avatar .el-icon {
  font-size: 60px;
}

.detail-cover-img {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 50%;
}

.plant-info h3 {
  margin: 0 0 8px;
  font-size: 20px;
  color: #303133;
}

.species {
  color: #909399;
  margin: 0 0 16px;
}

.info-list {
  text-align: left;
  padding: 0 20px;
}

.info-list p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}

.growth-records {
  padding: 20px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.records-header h4 {
  margin: 0;
  font-size: 16px;
}

.record-content {
  padding: 8px 0;
}

.record-stage {
  margin-bottom: 8px;
}

.record-data {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.record-desc {
  margin: 8px 0;
  color: #303133;
}

.record-author {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}
</style>
