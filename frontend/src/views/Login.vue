<template>
  <div class="login-container">
    <div class="login-shell app-glass-card">
      <div class="login-hero">
        <div class="hero-badge">SMART GREENHOUSE</div>
        <h1>智慧大棚教学平台</h1>
        <p>实时监控、课程实践、实验分析，一体化连接课堂与植物生长过程。</p>
        <ul>
          <li>实时查看温湿度与设备状态</li>
          <li>一键进入实验报告与植物档案</li>
          <li>支持教师与学生分角色使用</li>
        </ul>
      </div>

      <el-card class="login-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h2>账号登录</h2>
            <p>欢迎回来，请先登录</p>
          </div>
        </template>
        <el-form :model="loginForm" label-width="0px">
          <el-form-item>
            <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" size="large" autofocus />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading" :disabled="!canSubmit">
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="register-entry">
          <span>还没有账号？</span>
          <el-button link type="primary" @click="goRegister">学生/教师注册</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { User, Lock } from '@element-plus/icons-vue';
import { login } from '../api';
import { ElMessage } from 'element-plus';
import { getActionErrorMessage } from '../utils/error';

const router = useRouter();
const route = useRoute();
const loginForm = ref({
  username: '',
  password: ''
});
const loading = ref(false);
const REMEMBERED_USERNAME_KEY = 'auth.lastUsername';

const canSubmit = computed(() => {
  return Boolean(loginForm.value.username.trim() && loginForm.value.password.trim() && !loading.value);
});

const handleLogin = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请输入用户名和密码');
    return;
  }

  loading.value = true;
  try {
    const username = loginForm.value.username.trim();
    const response = await login(username, loginForm.value.password);

    // Store token and role
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('role', response.role);
    localStorage.setItem('username', username);
    localStorage.setItem(REMEMBERED_USERNAME_KEY, username);

    ElMessage.success('登录成功');
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    router.push(redirect);
  } catch (error: any) {
    ElMessage.error(getActionErrorMessage(error, {
      action: '登录',
      fallback: '登录失败，请检查网络或后端服务状态',
      unauthorizedMessage: '用户名或密码错误，请重新输入',
      serverErrorMessage: '登录服务暂不可用，请稍后重试',
      networkErrorMessage: '无法连接登录服务，请确认后端已启动',
    }));
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const goRegister = () => {
  router.push('/register');
};

onMounted(() => {
  const remembered = localStorage.getItem(REMEMBERED_USERNAME_KEY);
  if (remembered && !loginForm.value.username) {
    loginForm.value.username = remembered;
  }
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at 10% 0, var(--layout-glow-left), transparent 32%),
    radial-gradient(circle at 90% 0, var(--layout-glow-right), transparent 28%),
    linear-gradient(180deg, var(--bg-page) 0%, var(--bg-surface) 100%);
}

.login-shell {
  width: min(980px, 100%);
  min-height: 560px;
  border-radius: 20px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  border: 1px solid var(--el-border-color-light);
}

.card-header {
  text-align: left;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
  color: var(--text-main);
}

.card-header p {
  margin: 8px 0 0;
  color: var(--text-tertiary);
}

.login-hero {
  padding: 46px 40px;
  background: linear-gradient(165deg, var(--color-plant-700) 0%, var(--color-plant-600) 100%);
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--color-plant-700) 78%, var(--bg-page)) 0%,
    color-mix(in srgb, var(--color-plant-600) 70%, var(--bg-page)) 100%
  );
  color: var(--el-color-white);
  color: color-mix(in srgb, var(--text-main) 18%, #ffffff 82%);
}

.hero-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.08em;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.16);
  background: color-mix(in srgb, var(--glass-bg-strong) 76%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.26);
  border: 1px solid color-mix(in srgb, var(--el-border-color-light) 70%, transparent);
}

.login-hero h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.25;
}

.login-hero p {
  margin-top: 14px;
  color: rgba(236, 248, 240, 0.92);
  line-height: 1.65;
}

.login-hero ul {
  margin: 22px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
}

.login-card {
  border: 0;
  border-radius: 0;
  background: var(--glass-bg-strong);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}

.login-card :deep(.el-card__body),
.login-card :deep(.el-card__header) {
  width: min(420px, 100%);
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  transition: transform var(--motion-fast) var(--ease-standard);
}

.login-btn:not(:disabled):hover {
  transform: translateY(-1px);
}

.register-entry {
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: 13px;
}

@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .login-hero {
    padding: 30px 24px;
  }

  .login-hero h1 {
    font-size: 28px;
  }

  .login-card {
    padding: 26px 14px;
  }
}
</style>
