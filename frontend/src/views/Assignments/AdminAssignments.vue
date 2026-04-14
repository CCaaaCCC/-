<template>
  <div class="role-shell">
    <el-alert
      title="管理员视角：全校任务监管与运维兜底"
      type="error"
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
