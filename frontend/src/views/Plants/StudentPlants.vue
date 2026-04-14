<template>
  <div class="role-shell">
    <el-alert
      title="学生视角：可查看档案并提交生长记录"
      type="success"
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
