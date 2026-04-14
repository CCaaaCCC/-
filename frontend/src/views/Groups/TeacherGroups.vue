<template>
  <div class="role-shell">
    <el-alert
      title="教师视角：可查看全校小组，仅可管理自己创建的小组"
      type="warning"
      :closable="false"
      class="role-alert"
    />
    <GroupsLegacy />
  </div>
</template>

<script setup lang="ts">
import GroupsLegacy from '../Groups.vue';
</script>

<style scoped>
.role-alert {
  margin: 12px 20px;
}
</style>
