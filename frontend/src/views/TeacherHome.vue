<template>
  <div class="home-page">
    <AppTopBar title="教师工作台" :roleTagType="'warning'" :roleText="'教师'" />

    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>教学任务</h3>
          <p>布置实验任务并查看学生提交的实验文档，完成批改和评分。</p>
          <el-button type="primary" @click="router.push('/assignments')">进入实验报告管理</el-button>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>班级协作</h3>
          <p>管理小组、查看植物档案，组织学生开展分组观察与讨论。</p>
          <div class="actions">
            <el-button @click="router.push('/groups')">小组管理</el-button>
            <el-button @click="router.push('/plants')">植物档案</el-button>
            <el-button @click="router.push('/market')">线下商城</el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="panel" shadow="hover">
          <h3>教学分析</h3>
          <p>通过数据分析查看作业完成度与课堂表现。</p>
          <div class="actions">
            <el-button type="success" @click="router.push('/analytics')">教学分析</el-button>
            <el-button @click="router.push('/monitor')">环境监控</el-button>
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
