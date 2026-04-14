<template>
  <div class="role-shell">
    <el-alert
      title="教师视角：可查看全校植物档案，仅可管理自己创建的档案"
      type="warning"
      :closable="false"
      class="role-alert"
    />
    <PlantsLegacy />
  </div>
</template>

<script setup lang="ts">
import PlantsLegacy from '../Plants.vue';
</script>

<style scoped>
.role-alert {
  margin: 12px 20px;
}
</style>
