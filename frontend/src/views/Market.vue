<template>
  <div class="market-page app-page-shell app-fade-up">
    <AppTopBar
      title="🛒 校园线下商城"
      :roleTagType="roleTagType"
      :roleText="userRoleText"
      subtitle="学生可发布农作物、花卉等线下售卖信息，仅展示信息，不提供在线支付"
    >
      <template #extra-actions>
        <el-button type="primary" round @click="openCreateDialog">发布商品</el-button>
      </template>
    </AppTopBar>

    <div class="toolbar app-glass-card">
      <el-input
        v-model="filters.search"
        placeholder="搜索商品标题、描述、地点"
        clearable
        class="toolbar-input"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select v-model="filters.status" placeholder="在售状态" clearable class="toolbar-select" @change="loadProducts">
        <el-option label="在售" value="on_sale" />
        <el-option label="已售出" value="sold" />
        <el-option label="已下架" value="off_shelf" />
      </el-select>

      <el-switch v-model="filters.mine" active-text="只看我发布" @change="handleMineToggle" />

      <el-button type="primary" round @click="handleSearch">查询</el-button>
      <el-button round @click="resetFilters">重置</el-button>
    </div>

    <div class="market-grid">
      <template v-if="loading">
        <div
          v-for="idx in Math.max(6, Math.floor(pagination.page_size / 2))"
          :key="`market-skeleton-${idx}`"
          class="market-skeleton app-glass-card"
        >
          <el-skeleton animated>
            <template #template>
              <el-skeleton-item variant="image" class="skeleton-image" />
              <div class="skeleton-body">
                <el-skeleton-item variant="h3" style="width: 72%" />
                <el-skeleton-item variant="text" />
                <el-skeleton-item variant="text" style="width: 84%" />
                <el-skeleton-item variant="text" style="width: 58%" />
              </div>
            </template>
          </el-skeleton>
        </div>
      </template>

      <template v-else-if="products.length > 0">
        <MarketProductCard
          v-for="item in visibleProducts"
          :key="item.id"
          :item="item"
          :resolveAssetUrl="resolveAssetUrl"
          :statusText="statusText"
          :statusTagType="statusTagType"
          :formatPrice="formatPrice"
          :formatDate="formatDate"
          @edit="openEditDialog"
          @remove="removeProduct"
        />
      </template>

      <div v-else class="empty-state app-glass-card">
        <div class="empty-icon">🧺</div>
        <h3>暂无商品信息</h3>
        <p>试试切换筛选条件，或发布第一条线下售卖信息。</p>
        <el-button type="primary" round @click="openCreateDialog">立即发布</el-button>
      </div>
    </div>

    <p v-if="!loading && visibleProducts.length < products.length" class="rendering-hint">
      正在平滑渲染更多卡片...
    </p>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[12, 24, 36]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadProducts"
        @size-change="handlePageSizeChange"
      />
    </div>

    <el-dialog
      v-model="showEditor"
      :title="editingProduct ? '编辑商品信息' : '发布商品信息'"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="productForm" label-width="92px">
        <el-form-item label="商品标题" required>
          <el-input v-model="productForm.title" placeholder="例如：自种番茄（新鲜采摘）" />
        </el-form-item>
        <el-form-item label="商品描述">
          <el-input v-model="productForm.description" type="textarea" :rows="4" placeholder="写明品种、品质、售卖时间等信息" />
        </el-form-item>
        <el-form-item label="价格(元)">
          <el-input-number v-model="productForm.price" :min="0" :precision="2" :step="0.5" :controls="true" style="width: 220px" />
        </el-form-item>
        <el-form-item label="售卖地点" required>
          <el-input v-model="productForm.location" placeholder="例如：教学楼东侧温室门口" />
        </el-form-item>
        <el-form-item label="联系方式" required>
          <el-input v-model="productForm.contact_info" placeholder="例如：班级群私信 / 电话" />
        </el-form-item>
        <el-form-item label="商品状态" required>
          <el-select v-model="productForm.status" style="width: 220px">
            <el-option label="在售" value="on_sale" />
            <el-option label="已售出" value="sold" />
            <el-option label="已下架" value="off_shelf" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品图片">
          <div class="upload-row">
            <el-upload
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              :http-request="handleImageUploadRequest"
            >
              <el-button>上传图片</el-button>
            </el-upload>
            <span class="upload-tip">支持 jpg/png/webp/gif，最大 10MB</span>
          </div>
          <img v-if="productForm.image_url" :src="resolveAssetUrl(productForm.image_url)" class="preview-image" alt="商品图片" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditor = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitProduct">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import type { UploadRequestOptions } from 'element-plus';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import AppTopBar from '../components/AppTopBar.vue';
import MarketProductCard from '../components/market/MarketProductCard.vue';
import {
  createMarketProduct,
  deleteMarketProduct,
  getMarketProducts,
  updateMarketProduct,
  uploadMarketImage,
  type MarketProduct,
  type MarketProductCreatePayload,
  type MarketProductStatus,
} from '../api/market';
import { resolveBackendAssetUrl } from '../api';
import { getUserRole } from '../utils/authSession';
import { getErrorMessage } from '../utils/error';
import { usePagination } from '../composables/usePagination';
import { createFileValidator } from '../composables/useFileValidation';

const userRole = ref(getUserRole() || 'student');
const loading = ref(false);
const submitting = ref(false);
const showEditor = ref(false);
const editingProduct = ref<MarketProduct | null>(null);

const products = ref<MarketProduct[]>([]);
const { pagination, resetPage, setTotal, changePageSize } = usePagination(1, 12);
const renderCount = ref(0);
let revealTimer: ReturnType<typeof setTimeout> | null = null;

const filters = ref({
  search: '',
  status: '' as '' | MarketProductStatus,
  mine: false,
});

const visibleProducts = computed(() => {
  if (renderCount.value <= 0) {
    return products.value;
  }
  return products.value.slice(0, renderCount.value);
});

const defaultProductForm = (): MarketProductCreatePayload => ({
  title: '',
  description: '',
  price: undefined,
  location: '',
  contact_info: '',
  image_url: '',
  status: 'on_sale',
});

const productForm = ref<MarketProductCreatePayload>(defaultProductForm());

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

const resolveAssetUrl = (url?: string | null) => resolveBackendAssetUrl(url || undefined);

const clearRevealTimer = () => {
  if (revealTimer) {
    window.clearTimeout(revealTimer);
    revealTimer = null;
  }
};

const startProgressiveReveal = () => {
  clearRevealTimer();
  const total = products.value.length;
  if (total === 0) {
    renderCount.value = 0;
    return;
  }

  renderCount.value = Math.min(12, total);

  const revealNext = () => {
    renderCount.value = Math.min(total, renderCount.value + 12);
    if (renderCount.value < total) {
      revealTimer = window.setTimeout(revealNext, 16);
    } else {
      clearRevealTimer();
    }
  };

  if (renderCount.value < total) {
    revealTimer = window.setTimeout(revealNext, 16);
  }
};

const statusText = (status: string) => {
  if (status === 'sold') return '已售出';
  if (status === 'off_shelf') return '已下架';
  return '在售';
};

const statusTagType = (status: string) => {
  if (status === 'sold') return 'success';
  if (status === 'off_shelf') return 'info';
  return 'warning';
};

const formatDate = (value?: string) => {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('zh-CN');
};

const formatPrice = (price?: number | null) => {
  if (price === null || price === undefined) return '面议';
  return `¥${Number(price).toFixed(2)}`;
};

const loadProducts = async () => {
  loading.value = true;
  clearRevealTimer();
  try {
    const response = await getMarketProducts({
      search: filters.value.search.trim() || undefined,
      status: filters.value.status || undefined,
      mine: filters.value.mine,
      page: pagination.page,
      page_size: pagination.page_size,
    });
    products.value = response.items || [];
    setTotal(response.total || 0);
    startProgressiveReveal();
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载商品失败'));
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  resetPage();
  loadProducts();
};

const handleMineToggle = () => {
  resetPage();
  loadProducts();
};

const resetFilters = () => {
  filters.value = { search: '', status: '', mine: false };
  resetPage();
  loadProducts();
};

const handlePageSizeChange = (size: number) => {
  changePageSize(size);
  loadProducts();
};

const openCreateDialog = () => {
  editingProduct.value = null;
  productForm.value = defaultProductForm();
  showEditor.value = true;
};

const openEditDialog = (item: MarketProduct) => {
  editingProduct.value = item;
  productForm.value = {
    title: item.title,
    description: item.description || '',
    price: item.price ?? undefined,
    location: item.location,
    contact_info: item.contact_info,
    image_url: item.image_url || '',
    status: (item.status as MarketProductStatus) || 'on_sale',
  };
  showEditor.value = true;
};

const validateProductForm = () => {
  if (!productForm.value.title?.trim()) {
    ElMessage.warning('请填写商品标题');
    return false;
  }
  if (!productForm.value.location?.trim()) {
    ElMessage.warning('请填写售卖地点');
    return false;
  }
  if (!productForm.value.contact_info?.trim()) {
    ElMessage.warning('请填写联系方式');
    return false;
  }
  return true;
};

const submitProduct = async () => {
  if (!validateProductForm()) {
    return;
  }

  submitting.value = true;
  try {
    const payload: MarketProductCreatePayload = {
      title: productForm.value.title.trim(),
      description: productForm.value.description?.trim() || undefined,
      price: productForm.value.price,
      location: productForm.value.location.trim(),
      contact_info: productForm.value.contact_info.trim(),
      image_url: productForm.value.image_url || undefined,
      status: productForm.value.status,
    };

    if (editingProduct.value) {
      await updateMarketProduct(editingProduct.value.id, payload);
      ElMessage.success('商品信息已更新');
    } else {
      await createMarketProduct(payload);
      ElMessage.success('商品发布成功');
    }

    showEditor.value = false;
    await loadProducts();
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '保存失败'));
  } finally {
    submitting.value = false;
  }
};

const removeProduct = async (item: MarketProduct) => {
  try {
    await ElMessageBox.confirm(`确认删除商品“${item.title}”？`, '删除确认', { type: 'warning' });
    await deleteMarketProduct(item.id);
    ElMessage.success('商品已删除');
    await loadProducts();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(getErrorMessage(error, '删除失败'));
    }
  }
};

const validateImageUpload = createFileValidator(
  {
    allowedExtensions: ['jpg', 'jpeg', 'png', 'webp', 'gif'],
    maxSizeMB: 10,
    extensionMessage: '仅支持 jpg/jpeg/png/webp/gif',
    sizeMessage: '图片大小不能超过 10MB',
  },
  (message) => ElMessage.error(message),
);

const beforeImageUpload = (file: File) => validateImageUpload(file);

const handleImageUploadRequest = async (option: UploadRequestOptions) => {
  try {
    const result = await uploadMarketImage(option.file as File);
    productForm.value.image_url = result.url;
    option.onSuccess?.(result as any);
    ElMessage.success('图片上传成功');
  } catch (error: any) {
    option.onError?.(error);
    ElMessage.error(getErrorMessage(error, '图片上传失败'));
  }
};

onMounted(() => {
  loadProducts();
});

onBeforeUnmount(() => {
  clearRevealTimer();
});
</script>

<style scoped>
.market-page {
  min-height: 100vh;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  margin-bottom: 16px;
}

.toolbar-input {
  width: 320px;
  max-width: 100%;
}

.toolbar-select {
  width: 160px;
}

.market-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.market-skeleton {
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  overflow: hidden;
}

.skeleton-image {
  width: 100%;
  height: 180px;
}

.skeleton-body {
  padding: 12px 14px;
  display: grid;
  gap: 10px;
}

.empty-state {
  grid-column: 1 / -1;
  border: 1px dashed var(--el-border-color);
  border-radius: 14px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 10px;
}

.empty-icon {
  font-size: 42px;
}

.rendering-hint {
  margin: 12px 4px 0;
  color: var(--text-tertiary);
  font-size: 12px;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-tip {
  color: var(--text-tertiary);
  font-size: 12px;
}

.preview-image {
  margin-top: 10px;
  width: 180px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

@media (max-width: 920px) {
  .toolbar-input,
  .toolbar-select {
    width: 100%;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>
