import { createRouter, createWebHistory } from 'vue-router';
import { ElMessage } from 'element-plus';
import { getAuthToken, getUserRole } from '../utils/authSession';

const CHUNK_RELOAD_GUARD_KEY = 'router:chunk-reload-once';

const isChunkLoadError = (error: unknown): boolean => {
  const message = String((error as any)?.message || error || '').toLowerCase();
  return (
    message.includes('failed to fetch dynamically imported module')
    || message.includes('importing a module script failed')
    || message.includes('loading chunk')
    || message.includes('dynamic import')
  );
};

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue')
  },
  {
    path: '/',
    name: 'HomeRedirect',
    redirect: () => {
      const role = getUserRole();
      if (role === 'admin') return '/home/admin';
      if (role === 'teacher') return '/home/teacher';
      return '/home/student';
    },
    meta: { requiresAuth: true }
  },
  {
    path: '/home/student',
    name: 'StudentHome',
    component: () => import('../views/StudentHome.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/home/teacher',
    name: 'TeacherHome',
    component: () => import('../views/TeacherHome.vue'),
    meta: { requiresAuth: true, requiresTeacher: true }
  },
  {
    path: '/home/admin',
    name: 'AdminHome',
    component: () => import('../views/AdminHome.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/monitor',
    name: 'Dashboard',
    component: () => import('../components/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/teaching',
    name: 'TeachingContents',
    component: () => import('../views/TeachingContents.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/market',
    name: 'Market',
    component: () => import('../views/Market.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: () => import('../views/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: () => import('../views/Assignments/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/plants',
    name: 'Plants',
    component: () => import('../views/Plants/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: () => import('../views/Groups/index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'OperationLogs',
    component: () => import('../views/OperationLogs.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/analytics',
    name: 'TeachingAnalytics',
    component: () => import('../views/TeachingAnalytics.vue'),
    meta: { requiresAuth: true, requiresTeacher: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/display',
    name: 'DashboardDisplay',
    component: () => import('../views/DashboardDisplay.vue'),
    meta: { requiresAuth: false }  // 大屏展示不需要认证
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const token = getAuthToken();
  const role = getUserRole();

  // 大屏展示页面不需要认证
  if (to.path === '/display') {
    next();
    return;
  }

  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } });
  } else if (to.meta.requiresAdmin && role !== 'admin') {
    ElMessage.error('当前账号无管理员权限，已为你跳转到个人中心');
    next({ path: '/profile', query: { from: to.fullPath } });
  } else if (to.meta.requiresTeacher && !['teacher', 'admin'].includes(role || '')) {
    ElMessage.error('当前账号无教师权限，已为你跳转到个人中心');
    next({ path: '/profile', query: { from: to.fullPath } });
  } else {
    next();
  }
});

router.afterEach(() => {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem(CHUNK_RELOAD_GUARD_KEY);
  }
});

router.onError((error) => {
  console.error('[router:error]', error);

  if (typeof window !== 'undefined' && isChunkLoadError(error)) {
    const hasRetried = sessionStorage.getItem(CHUNK_RELOAD_GUARD_KEY) === '1';
    if (!hasRetried) {
      sessionStorage.setItem(CHUNK_RELOAD_GUARD_KEY, '1');
      ElMessage.warning('页面资源已更新，正在自动刷新...');
      window.location.reload();
      return;
    }

    sessionStorage.removeItem(CHUNK_RELOAD_GUARD_KEY);
    ElMessage.error('页面资源加载失败，请手动刷新后重试');
    return;
  }

  ElMessage.error('页面跳转失败，请稍后重试');
});

export default router;
