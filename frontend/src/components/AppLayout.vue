<template>
  <div class="app-layout">
    <div v-if="!isDesktop && sidebarOpen" class="mobile-backdrop" @click="closeSidebar"></div>
    <!-- 侧边栏玻璃面板 -->
    <aside class="app-sidebar app-glass-card" :class="{ 'is-open': isDesktop || sidebarOpen }">
      <div class="sidebar-header">
        <h1 class="logo-text">EcoSTEM 4C</h1>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="nav-item--active"
          @click="handleNavClick"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      
      <!-- 底部退出等 -->
      <div class="sidebar-footer">
        <router-link to="/profile" class="nav-item" active-class="nav-item--active" @click="handleNavClick">
          <el-icon><User /></el-icon>
          <span>个人中心</span>
        </router-link>
        <button class="nav-item nav-item--danger" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 右侧容器 -->
    <div class="app-main-container">
      <header class="app-top-header app-glass-header">
        <div class="header-left">
          <button class="mobile-menu-btn" type="button" @click="toggleSidebar" aria-label="打开导航菜单">
            ☰
          </button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>工作台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleThemeCommand">
            <el-button class="theme-switcher-btn" plain>
              <span
                class="theme-dot"
                :class="[
                  `theme-dot--${theme}`,
                  theme === 'system' ? `theme-dot--resolved-${effectiveTheme}` : ''
                ]"
              ></span>
              <span>{{ currentThemeLabel }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu class="theme-dropdown-menu">
                <el-dropdown-item
                  v-for="item in themeOptions"
                  :key="item.value"
                  :command="item.value"
                  :class="{ 'is-active': theme === item.value }"
                >
                  <span class="theme-menu-item">
                    <span class="theme-option-dot" :class="`theme-option-dot--${item.value}`"></span>
                    <span>{{ item.label }}</span>
                  </span>
                  <el-icon v-if="theme === item.value"><Check /></el-icon>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <NotificationBell />
        </div>
      </header>
      
      <!-- 页面内容 -->
      <main class="app-main-content">
        <slot></slot>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { House, Monitor, Document, UserFilled, Connection, TrendCharts, SwitchButton, User, ArrowDown, Check, ShoppingCart } from '@element-plus/icons-vue';
import { logoutUser } from '../api';
import { ElMessage } from 'element-plus';
import NotificationBell from './NotificationBell.vue';
import { isThemeMode, type ThemeMode, useTheme } from '../composables/useTheme';
import { clearAuthSession, getUserRole } from '../utils/authSession';

const route = useRoute();
const router = useRouter();
const role = getUserRole() || 'student';
const { theme, effectiveTheme, setTheme } = useTheme();
const sidebarOpen = ref(false);
const isDesktop = ref(typeof window === 'undefined' ? true : window.innerWidth > 1024);

const themeOptions = [
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
  { value: 'modern', label: '现代' },
  { value: 'system', label: '跟随系统' },
] as const;

const currentThemeLabel = computed(() => {
  if (theme.value === 'system') {
    return `跟随系统 (${effectiveTheme.value === 'dark' ? '深色' : '浅色'})`;
  }

  return themeOptions.find((item) => item.value === theme.value)?.label || '浅色';
});

const allNavItems = [
  { path: `/home/${role}`, label: '首页概览', icon: House, roles: ['admin', 'teacher', 'student'] },
  { path: '/monitor', label: '大棚监控', icon: Monitor, roles: ['admin', 'teacher', 'student'] },
  { path: '/teaching', label: '教学资源', icon: Document, roles: ['admin', 'teacher', 'student'] },
  { path: '/market', label: '线下商城', icon: ShoppingCart, roles: ['admin', 'teacher', 'student'] },
  { path: '/assignments', label: '实验报告', icon: Document, roles: ['admin', 'teacher', 'student'] },
  { path: '/plants', label: '植物生长', icon: TrendCharts, roles: ['admin', 'teacher', 'student'] },
  { path: '/groups', label: '学习小组', icon: UserFilled, roles: ['admin', 'teacher', 'student'] },
  { path: '/users', label: '账号管理', icon: UserFilled, roles: ['admin'] },
  { path: '/logs', label: '操作日志', icon: Connection, roles: ['admin'] },
  { path: '/analytics', label: '教学分析', icon: TrendCharts, roles: ['teacher', 'admin'] }
];

const navItems = computed(() => {
  return allNavItems.filter(item => item.roles.includes(role));
});

const currentRouteName = computed(() => {
  return route.name?.toString() || '页面';
});

const updateViewportState = () => {
  if (typeof window === 'undefined') {
    return;
  }

  isDesktop.value = window.innerWidth > 1024;
  if (isDesktop.value) {
    sidebarOpen.value = false;
  }
};

const toggleSidebar = () => {
  if (isDesktop.value) {
    return;
  }
  sidebarOpen.value = !sidebarOpen.value;
};

const closeSidebar = () => {
  if (!isDesktop.value) {
    sidebarOpen.value = false;
  }
};

const handleNavClick = () => {
  closeSidebar();
};

const handleThemeCommand = (command: string | number | object) => {
  if (typeof command !== 'string' || !isThemeMode(command)) {
    return;
  }

  const nextTheme = command as ThemeMode;
  setTheme(nextTheme);

  if (nextTheme === 'system') {
    ElMessage.success(`已切换为跟随系统 (${effectiveTheme.value === 'dark' ? '深色' : '浅色'})`);
    return;
  }

  ElMessage.success(`已切换为${themeOptions.find((item) => item.value === nextTheme)?.label || '新'}主题`);
};

const handleLogout = async () => {
  try {
    await logoutUser();
    clearAuthSession();
    ElMessage.success('已退出登录');
    router.push('/login');
  } catch (e) {
    ElMessage.error('退出异常，仅清除本地凭证');
    clearAuthSession();
    router.push('/login');
  }
};

watch(
  () => route.fullPath,
  () => {
    closeSidebar();
  }
);

onMounted(() => {
  updateViewportState();
  window.addEventListener('resize', updateViewportState);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateViewportState);
});
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: radial-gradient(circle at 0 0, var(--layout-glow-left), transparent 24%),
    radial-gradient(circle at 100% 0, var(--layout-glow-right), transparent 20%),
    linear-gradient(170deg, var(--bg-page) 0%, var(--bg-surface) 100%);
}

.mobile-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(8, 17, 13, 0.42);
  z-index: 8;
}

.app-sidebar {
  width: 240px;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 16px;
  border-right: 1px solid var(--el-border-color-light);
  border-radius: 0;
  box-shadow: 4px 0 24px rgba(26, 68, 52, 0.04);
  z-index: 10;
  flex-shrink: 0;
}

.sidebar-header {
  margin-bottom: 32px;
  padding: 0 12px;
}

.logo-text {
  font-size: 1.4rem;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-plant-600), var(--color-sun-600));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-control);
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 600;
  transition: all var(--motion-fast) var(--ease-standard);
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  font-size: 1rem;
}

.nav-item:hover {
  background: rgba(45, 157, 120, 0.04);
  color: var(--color-plant-600);
}

.nav-item--active {
  background: rgba(45, 157, 120, 0.1);
  color: var(--color-plant-600);
  box-shadow: inset 4px 0 0 var(--color-plant-500);
}

.nav-item--danger {
  color: var(--color-danger);
}
.nav-item--danger:hover {
  background: rgba(226, 100, 95, 0.08);
  color: var(--color-danger);
}

.app-main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.app-top-header {
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  border-bottom: 1px solid var(--el-border-color-light);
  background: var(--glass-bg-strong);
  backdrop-filter: blur(12px);
  z-index: 5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mobile-menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  background: var(--glass-bg);
  color: var(--text-main);
  font-size: 18px;
  cursor: pointer;
}

.theme-switcher-btn {
  min-width: 110px;
  font-weight: 600;
}

.theme-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  display: inline-block;
}

.theme-dot--light {
  background: linear-gradient(135deg, #ffffff, #dceee6);
}

.theme-dot--dark {
  background: linear-gradient(135deg, #1f2d28, #31443d);
  border-color: rgba(255, 255, 255, 0.24);
}

.theme-dot--modern {
  background: linear-gradient(135deg, #0fa3a0, #ff8f3f);
}

.theme-dot--system {
  background: conic-gradient(from 180deg, #1f2d28 0 50%, #ffffff 50% 100%);
}

.theme-dot--resolved-dark {
  box-shadow: 0 0 0 2px rgba(54, 90, 73, 0.25);
}

.theme-dot--resolved-light {
  box-shadow: 0 0 0 2px rgba(183, 208, 196, 0.45);
}

.theme-menu-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.theme-option-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.theme-option-dot--light {
  background: linear-gradient(135deg, #ffffff, #dceee6);
}

.theme-option-dot--dark {
  background: linear-gradient(135deg, #1f2d28, #31443d);
  border-color: rgba(255, 255, 255, 0.24);
}

.theme-option-dot--modern {
  background: linear-gradient(135deg, #0fa3a0, #ff8f3f);
}

.theme-option-dot--system {
  background: conic-gradient(from 180deg, #1f2d28 0 50%, #ffffff 50% 100%);
}

:deep(.theme-dropdown-menu .el-dropdown-menu__item) {
  min-width: 150px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.theme-dropdown-menu .el-dropdown-menu__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 700;
}

.app-main-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
  position: relative;
}

@media (max-width: 1024px) {
  .mobile-menu-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .app-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 264px;
    transform: translateX(-110%);
    transition: transform var(--motion-base) var(--ease-standard);
    border-radius: 0 18px 18px 0;
    z-index: 10;
  }

  .app-sidebar.is-open {
    transform: translateX(0);
  }

  .app-top-header {
    padding: 0 16px;
  }

  .app-main-content {
    padding: 20px 16px;
  }
}

@media (max-width: 640px) {
  .app-top-header {
    height: auto;
    min-height: 56px;
    padding: 8px 12px;
  }

  .theme-switcher-btn {
    min-width: 96px;
    padding-inline: 8px;
  }

  .app-main-content {
    padding: 14px 12px;
  }
}
</style>
