<template>
  <div class="status-panel">
    <el-empty :image-size="80" :description="description">
      <template #default>
        <div v-if="actionText" style="margin-top: 8px; text-align: center">
          <el-button type="primary" @click="handleAction">{{ actionText }}</el-button>
        </div>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const props = defineProps<{
  description: string;
  actionText?: string;
  actionRoute?: string;
  actionCallback?: () => void;
}>();

const router = useRouter();

const handleAction = () => {
  if (props.actionCallback) {
    props.actionCallback();
    return;
  }
  if (props.actionRoute) {
    router.push(props.actionRoute);
  }
};
</script>

<style scoped>
.status-panel {
  padding: 24px 0;
}
</style>

