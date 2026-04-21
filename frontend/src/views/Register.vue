<template>
  <div class="register-container">
    <div class="register-shell app-glass-card">
      <div class="register-hero">
        <div class="hero-badge">INVITE CODE SIGNUP</div>
        <h1>学生/教师注册</h1>
        <p>输入班级邀请码即可完成绑定注册，注册后可直接登录进入平台。</p>
        <ul>
          <li>支持学生、教师账号自助注册</li>
          <li>通过邀请码自动绑定班级归属</li>
          <li>注册完成后由系统分配到对应管理名下</li>
        </ul>
      </div>

      <el-card class="register-card" shadow="never">
        <template #header>
          <div class="card-header">
            <h2>创建账号</h2>
            <p>请填写基础信息并输入邀请码</p>
          </div>
        </template>

        <el-form :model="form" label-width="0px">
          <el-form-item>
            <el-radio-group v-model="form.role">
              <el-radio label="student">学生</el-radio>
              <el-radio label="teacher">教师</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item>
            <el-input v-model="form.username" placeholder="用户名（3-20 位）" :prefix-icon="User" size="large" />
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="form.confirm_password"
              type="password"
              placeholder="确认密码"
              :prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-input v-model="form.real_name" placeholder="真实姓名（可选）" size="large" />
          </el-form-item>

          <el-form-item>
            <el-input v-model="form.email" placeholder="邮箱（可选）" size="large" />
          </el-form-item>

          <el-form-item v-if="form.role === 'student'">
            <el-input v-model="form.student_id" placeholder="学号" size="large" />
          </el-form-item>

          <el-form-item v-else>
            <el-input v-model="form.teacher_id" placeholder="工号" size="large" />
          </el-form-item>

          <el-form-item>
            <el-input
              v-model="form.invite_code"
              placeholder="班级邀请码"
              size="large"
              style="text-transform: uppercase"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" class="register-btn" :loading="loading" :disabled="!canSubmit" @click="handleRegister">
              注册并绑定
            </el-button>
          </el-form-item>
        </el-form>

        <div class="footer-actions">
          <span>已有账号？</span>
          <el-button link type="primary" @click="router.push('/login')">返回登录</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Lock, User } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { registerUser, type RegisterPayload } from '../api';
import { getErrorMessage } from '../utils/error';

const router = useRouter();
const loading = ref(false);
const REMEMBERED_USERNAME_KEY = 'auth.lastUsername';

const form = ref({
  role: 'student' as 'student' | 'teacher',
  username: '',
  password: '',
  confirm_password: '',
  real_name: '',
  email: '',
  student_id: '',
  teacher_id: '',
  invite_code: ''
});

const canSubmit = computed(() => {
  const baseOk = Boolean(
    form.value.username.trim()
    && form.value.password.trim()
    && form.value.confirm_password.trim()
    && form.value.invite_code.trim()
  );
  if (!baseOk || loading.value) {
    return false;
  }

  if (form.value.role === 'student') {
    return Boolean(form.value.student_id.trim());
  }
  return Boolean(form.value.teacher_id.trim());
});

const handleRegister = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请完善必填信息');
    return;
  }

  if (form.value.password !== form.value.confirm_password) {
    ElMessage.error('两次输入的密码不一致');
    return;
  }

  const payload: RegisterPayload = {
    username: form.value.username.trim(),
    password: form.value.password,
    role: form.value.role,
    invite_code: form.value.invite_code.trim().toUpperCase(),
    real_name: form.value.real_name.trim() || undefined,
    email: form.value.email.trim() || undefined,
    student_id: form.value.role === 'student' ? (form.value.student_id.trim() || undefined) : undefined,
    teacher_id: form.value.role === 'teacher' ? (form.value.teacher_id.trim() || undefined) : undefined,
  };

  loading.value = true;
  try {
    const result = await registerUser(payload);
    localStorage.setItem(REMEMBERED_USERNAME_KEY, payload.username);
    ElMessage.success(result.message || '注册成功，请登录');
    router.push('/login');
  } catch (error: any) {
    ElMessage.error(getErrorMessage(error, '注册失败，请检查邀请码和填写信息'));
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 28px;
  background:
    radial-gradient(circle at 8% 0, var(--layout-glow-left), transparent 32%),
    radial-gradient(circle at 90% 0, var(--layout-glow-right), transparent 28%),
    linear-gradient(180deg, var(--bg-page) 0%, var(--bg-surface) 100%);
}

.register-shell {
  width: min(1050px, 100%);
  min-height: 620px;
  border-radius: 20px;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  border: 1px solid var(--el-border-color-light);
}

.register-hero {
  padding: 46px 40px;
  background: linear-gradient(
    165deg,
    color-mix(in srgb, var(--color-plant-700) 78%, var(--bg-page)) 0%,
    color-mix(in srgb, var(--color-plant-600) 70%, var(--bg-page)) 100%
  );
  color: color-mix(in srgb, var(--text-main) 18%, #ffffff 82%);
}

.hero-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.08em;
  margin-bottom: 14px;
  background: color-mix(in srgb, var(--glass-bg-strong) 76%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-border-color-light) 70%, transparent);
}

.register-hero h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.25;
}

.register-hero p {
  margin-top: 14px;
  color: rgba(236, 248, 240, 0.92);
  line-height: 1.65;
}

.register-hero ul {
  margin: 22px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
}

.register-card {
  border: 0;
  border-radius: 0;
  background: var(--glass-bg-strong);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
}

.register-card :deep(.el-card__body),
.register-card :deep(.el-card__header) {
  width: min(430px, 100%);
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

.register-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
}

.footer-actions {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: 13px;
}

@media (max-width: 900px) {
  .register-shell {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .register-hero {
    padding: 30px 24px;
  }

  .register-hero h1 {
    font-size: 28px;
  }

  .register-card {
    padding: 24px 14px;
  }
}
</style>
