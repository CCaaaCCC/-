<template>
  <div class="role-shell">
    <el-alert
      title="学生视角：可查看小组信息与成员分工"
      type="success"
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
