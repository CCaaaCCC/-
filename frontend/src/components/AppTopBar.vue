<template>
  <div class="header app-glass-card">
    <div class="header-left">
      <h2 class="app-page-title">{{ title }}</h2>
      <el-tag :type="roleTagType">{{ roleText }}</el-tag>
    </div>
    <div class="header-right">
      <el-button class="topbar-btn" @click="router.push('/')">🏠 返回工作台</el-button>
      <NotificationBell />
      <el-button class="topbar-btn" @click="router.push('/profile')">👤 个人中心</el-button>
      <slot name="extra-actions" />
      <el-button type="danger" plain class="topbar-btn" @click="handleLogout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import NotificationBell from './NotificationBell.vue';

defineProps<{
  title: string;
  roleTagType: string;
  roleText: string;
}>();

const router = useRouter();

const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  router.push('/login');
};
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-radius: 14px;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: var(--text-main);
}

.header-right {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.topbar-btn {
  border-radius: 10px;
}

@media (max-width: 900px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
  }

  .topbar-btn {
    flex: 1 1 160px;
  }
}
</style>

