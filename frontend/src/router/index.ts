import { createRouter, createWebHistory } from 'vue-router';
import { ElMessage } from 'element-plus';
import Login from '../views/Login.vue';
import Dashboard from '../components/Dashboard.vue';
import TeachingContents from '../views/TeachingContents.vue';
import UserManagement from '../views/UserManagement.vue';
import Assignments from '../views/Assignments.vue';
import Plants from '../views/Plants.vue';
import DashboardDisplay from '../views/DashboardDisplay.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/teaching',
    name: 'TeachingContents',
    component: TeachingContents,
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: UserManagement,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/assignments',
    name: 'Assignments',
    component: Assignments,
    meta: { requiresAuth: true }
  },
  {
    path: '/plants',
    name: 'Plants',
    component: Plants,
    meta: { requiresAuth: true }
  },
  {
    path: '/display',
    name: 'DashboardDisplay',
    component: DashboardDisplay,
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
    next('/login');
  } else if (to.meta.requiresAdmin && role !== 'admin') {
    ElMessage.error('需要管理员权限');
    next('/');
  } else {
    next();
  }
});

export default router;
