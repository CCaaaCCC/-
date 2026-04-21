<template>
  <div class="role-dispatcher">
    <el-skeleton v-if="loadingRole" :rows="6" animated />
    <StatusPanel
      v-else-if="roleLoadError"
      :description="roleLoadError"
      :actionText="roleErrorActionText"
      :actionRoute="roleErrorActionRoute"
      :actionCallback="roleErrorActionRoute ? undefined : initRoleView"
    />
    <component v-else :is="currentView" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AdminGroups from './AdminGroups.vue';
import TeacherGroups from './TeacherGroups.vue';
import StudentGroups from './StudentGroups.vue';
import StatusPanel from '../../components/StatusPanel.vue';
import { useCurrentUser } from '../../composables/useCurrentUser';
import { getActionErrorMessage, getHttpStatus } from '../../utils/error';

const { role, ensureLoaded } = useCurrentUser();
const loadingRole = ref(true);
const roleLoadError = ref('');
const roleErrorActionText = ref('重试');
const roleErrorActionRoute = ref<string | undefined>(undefined);

const currentView = computed(() => {
  if (role.value === 'admin') return AdminGroups;
  if (role.value === 'teacher') return TeacherGroups;
  return StudentGroups;
});

onMounted(async () => {
  await initRoleView();
});

const initRoleView = async () => {
  loadingRole.value = true;
  roleLoadError.value = '';
  roleErrorActionText.value = '重试';
  roleErrorActionRoute.value = undefined;
  try {
    await ensureLoaded();
  } catch (error: unknown) {
    roleLoadError.value = getActionErrorMessage(error, {
      action: '加载小组页角色信息',
      fallback: '无法加载角色信息，请稍后重试',
    });

    if (getHttpStatus(error) === 401) {
      roleErrorActionText.value = '去登录';
      roleErrorActionRoute.value = '/login';
    }
  } finally {
    loadingRole.value = false;
  }
};
</script>
