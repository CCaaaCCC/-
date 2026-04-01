<template>
  <div class="home-page">
    <AppTopBar title="管理员工作台" :roleTagType="'danger'" :roleText="'管理员'" />

    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>系统管理</h3>
          <p>管理账号、班级、设备与权限分配，维护教学平台稳定运行。</p>
          <el-button type="warning" @click="router.push('/users')">用户与班级管理</el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>平台审计</h3>
          <p>查看操作日志，追踪关键行为并导出审计记录。</p>
          <div class="actions">
            <el-button type="primary" @click="router.push('/logs')">查看操作日志</el-button>
            <el-button @click="router.push('/assignments')">实验任务总览</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>运行监控</h3>
          <p>进入实时监控页面检查设备状态和环境数据。</p>
          <div class="actions">
            <el-button type="success" @click="router.push('/monitor')">环境监控</el-button>
            <el-button @click="router.push('/display')">数据大屏</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import AppTopBar from '../components/AppTopBar.vue';

const router = useRouter();
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.panel {
  border-radius: 12px;
  min-height: 230px;
}

.panel h3 {
  margin-top: 0;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
