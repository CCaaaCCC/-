<template>
  <div class="home-page app-page-shell app-fade-up">
    <AppTopBar title="管理员工作台" :roleTagType="'danger'" :roleText="'管理员'" />

    <!-- 概览与无用说明已移除，仅保留核心模块入口 -->

    <el-row :gutter="16">
      <el-col v-for="module in modules" :key="module.title" :xs="24" :md="8">
        <el-card class="panel app-hover-lift" shadow="hover">
          <div class="panel-head">
            <h3>{{ module.title }}</h3>
            <el-tag :type="module.tagType" effect="plain">{{ module.tag }}</el-tag>
          </div>
          <p>{{ module.description }}</p>
          <div class="actions">
            <el-button :type="module.primaryType" @click="router.push(module.primaryRoute)">
              {{ module.primaryLabel }}
            </el-button>
            <el-button plain @click="router.push(module.secondaryRoute)">
              {{ module.secondaryLabel }}
            </el-button>
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

const kpis = [
  { label: '核心模块', value: '3' },
  { label: '重点流程', value: '6' },
  { label: '关键入口', value: '8' }
];

const modules = [
  {
    title: '系统管理',
    tag: '治理',
    tagType: 'warning',
    description: '管理账号、班级、设备与权限分配，保障教学平台稳定运行。',
    primaryLabel: '用户与班级管理',
    primaryRoute: '/users',
    primaryType: 'warning',
    secondaryLabel: '学习小组管理',
    secondaryRoute: '/groups'
  },
  {
    title: '平台审计',
    tag: '追踪',
    tagType: 'primary',
    description: '查看操作日志，追踪关键行为并建立审计留痕。',
    primaryLabel: '查看操作日志',
    primaryRoute: '/logs',
    primaryType: 'primary',
    secondaryLabel: '实验任务总览',
    secondaryRoute: '/assignments'
  },
  {
    title: '运行监控',
    tag: '实时',
    tagType: 'success',
    description: '进入实时监控页面检查设备状态与环境数据趋势。',
    primaryLabel: '环境监控',
    primaryRoute: '/monitor',
    primaryType: 'success',
    secondaryLabel: '数据大屏',
    secondaryRoute: '/display'
  },
  {
    title: '线下商城',
    tag: '交易',
    tagType: 'warning',
    description: '查看学生发布的线下售卖信息，辅助进行校园农产品展示与秩序管理。',
    primaryLabel: '进入线下商城',
    primaryRoute: '/market',
    primaryType: 'warning',
    secondaryLabel: '教学资源',
    secondaryRoute: '/teaching'
  }
] as const;
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

.overview {
  border-radius: 16px;
  padding: var(--space-4);
  margin-bottom: var(--space-4);
}

.overview-intro h3 {
  margin: 0;
  color: #234536;
}

.overview-intro p {
  margin: 6px 0 0;
  color: #5d776b;
  font-size: 14px;
}

.overview-kpis {
  margin-top: var(--space-4);
}

.kpi-card {
  border-radius: 12px;
  background: rgba(45, 157, 120, 0.08);
  border: 1px solid rgba(45, 157, 120, 0.14);
  padding: 12px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #2d9d78;
}

.kpi-label {
  margin-top: 4px;
  font-size: 12px;
  color: #5e7a6d;
}

.panel {
  border-radius: 14px;
  min-height: 250px;
  border: 1px solid rgba(45, 157, 120, 0.14);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-2);
}

.panel h3 {
  margin: 0;
  color: #264a3a;
}

.panel p {
  color: #587367;
  line-height: 1.7;
  margin: 12px 0 0;
}

.actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .home-page {
    padding-top: var(--space-3);
  }

  .overview {
    padding: var(--space-3);
  }
}
</style>
