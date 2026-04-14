<template>
  <div class="role-shell">
    <el-alert
      title="学生视角：任务浏览与提交闭环"
      type="success"
      :closable="false"
      class="role-alert"
    />
    <AssignmentsLegacy />
  </div>
</template>

<script setup lang="ts">
import AssignmentsLegacy from '../Assignments.vue';
</script>

<style scoped>
.role-alert {
  margin: 12px 20px;
}
</style>
