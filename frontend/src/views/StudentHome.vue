<template>
  <div class="home-page">
    <AppTopBar title="学生工作台" :roleTagType="'success'" :roleText="'学生'" />

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card class="panel" shadow="hover">
          <h3>本周学习重点</h3>
          <p>围绕当前课程完成实验报告、补充植物生长记录，并查看教师反馈。</p>
          <div class="actions">
            <el-button type="primary" @click="router.push('/assignments')">去提交实验报告</el-button>
            <el-button @click="router.push('/plants')">查看植物档案</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="panel" shadow="hover">
          <h3>实时观察</h3>
          <p>进入监控页面，观察温湿度变化并与实验现象进行对照分析。</p>
          <div class="actions">
            <el-button type="success" @click="router.push('/monitor')">进入环境监控</el-button>
            <el-button @click="router.push('/teaching')">查看教学资源</el-button>
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
  min-height: 220px;
}

.panel h3 {
  margin-top: 0;
}

.actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
