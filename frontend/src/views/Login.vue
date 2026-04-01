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
            <el-input v-model="loginForm.username" placeholder="用户名" :prefix-icon="User" size="large" />
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
            <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading">
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { User, Lock } from '@element-plus/icons-vue';
import { login } from '../api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();
const loginForm = ref({
  username: '',
  password: ''
});
const loading = ref(false);

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码');
    return;
  }

  loading.value = true;
  try {
    const response = await login(loginForm.value.username, loginForm.value.password);

    // Store token and role
    localStorage.setItem('token', response.access_token);
    localStorage.setItem('role', response.role);
    localStorage.setItem('username', loginForm.value.username);

    ElMessage.success('登录成功');
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
    router.push(redirect);
  } catch (error: any) {
    const status = error?.response?.status;
    if (status === 401) {
      ElMessage.error('用户名或密码错误，请重新输入');
    } else if (status >= 500) {
      ElMessage.error('服务暂时不可用，请稍后重试');
    } else {
      ElMessage.error('登录失败，请检查网络或后端服务状态');
    }
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 28px;
}

.login-shell {
  width: min(980px, 100%);
  min-height: 560px;
  border-radius: 20px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
}

.card-header {
  text-align: left;
}

.card-header h2 {
  margin: 0;
  font-size: 24px;
}

.card-header p {
  margin: 8px 0 0;
  color: #6f8578;
}

.login-hero {
  padding: 46px 40px;
  background: linear-gradient(165deg, rgba(39, 117, 71, 0.9), rgba(22, 82, 52, 0.85));
  color: #ecf8f0;
}

.hero-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.08em;
  margin-bottom: 14px;
  background: rgba(255, 255, 255, 0.18);
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
  background: rgba(250, 255, 252, 0.92);
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
