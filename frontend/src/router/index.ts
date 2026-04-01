import { createRouter, createWebHistory } from 'vue-router';
import { ElMessage } from 'element-plus';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'HomeRedirect',
    redirect: () => {
      const role = localStorage.getItem('role');
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
    path: '/users',
    name: 'UserManagement',
    component: () => import('../views/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: () => import('../views/Assignments.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/plants',
    name: 'Plants',
    component: () => import('../views/Plants.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: () => import('../views/Groups.vue'),
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
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

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

export default router;
