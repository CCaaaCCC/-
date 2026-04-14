<template>
  <div class="role-shell">
    <el-alert
      title="教师视角：可查看全校任务与提交，非本人任务自动只读"
      type="warning"
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
