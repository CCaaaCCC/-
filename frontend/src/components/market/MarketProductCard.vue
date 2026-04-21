<template>
  <article class="market-card app-glass-card">
    <div class="card-image-wrap">
      <img
        v-if="item.image_url"
        v-lazy="resolveAssetUrl(item.image_url)"
        :alt="item.title"
        class="card-image"
      />
      <div v-else class="card-image-empty">🌿 暂无图片</div>
      <el-tag class="status-tag" :type="statusTagType(item.status)">{{ statusText(item.status) }}</el-tag>
    </div>

    <div class="card-content">
      <h3 class="title">{{ item.title }}</h3>
      <p class="desc">{{ item.description || '暂无描述' }}</p>

      <div class="meta-row">
        <span class="meta-label">价格</span>
        <span class="price">{{ formatPrice(item.price) }}</span>
      </div>
      <div class="meta-row">
        <span class="meta-label">地点</span>
        <span>{{ item.location }}</span>
      </div>
      <div class="meta-row">
        <span class="meta-label">联系方式</span>
        <span>{{ item.contact_info }}</span>
      </div>
      <div class="meta-row muted">
        <span>发布者：{{ item.seller_name || '未知' }}</span>
        <span>{{ formatDate(item.created_at) }}</span>
      </div>
    </div>

    <div v-if="item.can_edit || item.can_delete" class="card-actions">
      <el-button v-if="item.can_edit" size="small" @click="$emit('edit', item)">编辑</el-button>
      <el-button
        v-if="item.can_delete"
        size="small"
        type="danger"
        plain
        @click="$emit('remove', item)"
      >
        删除
      </el-button>
    </div>

    <div v-else class="card-actions card-actions--readonly">
      <el-tag size="small" type="info" effect="plain">只读（仅发布者或管理员可编辑）</el-tag>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { MarketProduct } from '../../api/market';

defineProps<{
  item: MarketProduct;
  resolveAssetUrl: (url?: string | null) => string;
  statusText: (status: string) => string;
  statusTagType: (status: string) => string;
  formatPrice: (price?: number | null) => string;
  formatDate: (value?: string) => string;
}>();

defineEmits<{
  edit: [item: MarketProduct];
  remove: [item: MarketProduct];
}>();
</script>

<style scoped>
.market-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  content-visibility: auto;
  contain-intrinsic-size: 340px;
}

.card-image-wrap {
  position: relative;
  height: 180px;
  background: color-mix(in srgb, var(--el-fill-color-light) 72%, transparent);
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-image-empty {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--text-tertiary);
  font-size: 18px;
}

.status-tag {
  position: absolute;
  top: 10px;
  right: 10px;
}

.card-content {
  padding: 12px 14px;
  display: grid;
  gap: 8px;
}

.title {
  margin: 0;
  font-size: 17px;
  color: var(--text-main);
}

.desc {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  min-height: 42px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--text-secondary);
  font-size: 13px;
}

.meta-label {
  color: var(--text-tertiary);
}

.price {
  color: var(--el-color-danger);
  font-weight: 700;
}

.meta-row.muted {
  color: var(--text-tertiary);
  font-size: 12px;
}

.card-actions {
  padding: 0 14px 14px;
  display: flex;
  gap: 8px;
}

.card-actions--readonly {
  padding-top: 6px;
}
</style>
