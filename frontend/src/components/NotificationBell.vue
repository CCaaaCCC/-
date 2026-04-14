<template>
  <el-popover
    placement="bottom"
    :width="360"
    trigger="click"
    v-model:visible="popoverVisible"
    @show="loadNotifications"
  >
    <template #reference>
      <el-badge :value="unreadCount" :hidden="unreadCount <= 0" :max="99">
        <el-button class="notice-btn" circle>
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <div class="notice-panel">
      <div class="notice-header">
        <strong>消息提醒</strong>
        <el-button link type="primary" @click="readAll" :disabled="unreadCount <= 0">全部已读</el-button>
      </div>

      <el-scrollbar max-height="320px">
        <div v-if="notifications.length > 0" class="notice-list">
          <div
            v-for="item in notifications"
            :key="item.id"
            class="notice-item"
            :class="{ unread: !item.is_read }"
            @click="openNotification(item)"
          >
            <div class="notice-title-row">
              <span class="notice-title">{{ item.title }}</span>
              <el-tag size="small" v-if="!item.is_read" type="danger">未读</el-tag>
            </div>
            <div class="notice-content">{{ item.content || '你有一条新动态' }}</div>
            <div class="notice-time">{{ formatDate(item.created_at) }}</div>
          </div>
        </div>
        <el-empty v-else description="暂无通知" :image-size="60" />
      </el-scrollbar>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Bell } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import {
  getNotifications,
  getNotificationUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from '../api';
import { getErrorMessage } from '../utils/error';

const router = useRouter();
const unreadCount = ref(0);
const notifications = ref<NotificationItem[]>([]);
const popoverVisible = ref(false);
let timer: number | null = null;

const loadUnreadCount = async () => {
  try {
    const data = await getNotificationUnreadCount();
    unreadCount.value = data.unread_count || 0;
  } catch {
    // Keep silent to avoid noisy UX when page is idle.
  }
};

const loadNotifications = async () => {
  try {
    const data = await getNotifications({ page: 1, page_size: 20 });
    notifications.value = data.items || [];
    await loadUnreadCount();
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '加载通知失败'));
  }
};

const readAll = async () => {
  try {
    await markAllNotificationsRead();
    notifications.value = notifications.value.map((item) => ({ ...item, is_read: true }));
    unreadCount.value = 0;
    ElMessage.success('已全部标记为已读');
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '操作失败'));
  }
};

const openNotification = async (item: NotificationItem) => {
  try {
    if (!item.is_read) {
      await markNotificationRead(item.id);
      item.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    }

    popoverVisible.value = false;
    if (item.content_id) {
      router.push({ path: '/teaching', query: { content_id: String(item.content_id) } });
    } else {
      router.push('/teaching');
    }
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '打开通知失败'));
  }
};

const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString('zh-CN');

onMounted(() => {
  loadUnreadCount();
  timer = window.setInterval(loadUnreadCount, 20000);
});

onUnmounted(() => {
  if (timer) {
    window.clearInterval(timer);
    timer = null;
  }
});
</script>

<style scoped>
.notice-btn {
  border-radius: 50%;
}

.notice-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notice-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 10px;
  cursor: pointer;
  background: var(--bg-card);
  transition: background-color 0.2s, border-color 0.2s;
}

.notice-item:hover {
  background-color: var(--el-fill-color-light);
}

.notice-item.unread {
  border-color: var(--color-danger);
  background: rgba(226, 100, 95, 0.08);
}

.notice-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.notice-title {
  font-size: 14px;
  color: var(--text-main);
  font-weight: 600;
}

.notice-content {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 4px;
}

.notice-time {
  color: var(--text-tertiary);
  font-size: 12px;
}
</style>
