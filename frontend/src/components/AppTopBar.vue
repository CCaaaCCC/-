<template>
  <div class="page-title-banner">
    <div class="title-block">
      <h2 class="app-page-title">{{ title }}</h2>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <el-tag :type="roleTagType" effect="plain" class="role-tag">{{ roleText }}</el-tag>
    <slot name="extra-actions" />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  roleTagType: string;
  roleText: string;
  subtitle?: string;
}>();
</script>

<style scoped>
.page-title-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.title-block {
  display: flex;
  flex-direction: column;
}

.app-page-title {
  margin: 0;
  font-size: var(--font-size-h2);
  background: linear-gradient(120deg, var(--text-main), var(--color-plant-700));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}

.subtitle {
  color: var(--text-tertiary);
  font-size: var(--font-size-body);
  margin-top: 4px;
}

.role-tag {
  align-self: center;
  border-radius: 8px;
}
</style>
