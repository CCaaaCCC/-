<template>
  <div class="role-dispatcher">
    <el-skeleton v-if="!ready" :rows="6" animated />
    <component v-else :is="currentView" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AdminGroups from './AdminGroups.vue';
import TeacherGroups from './TeacherGroups.vue';
import StudentGroups from './StudentGroups.vue';
import { useCurrentUser } from '../../composables/useCurrentUser';

const { role, ensureLoaded } = useCurrentUser();
const ready = ref(false);

const currentView = computed(() => {
  if (role.value === 'admin') return AdminGroups;
  if (role.value === 'teacher') return TeacherGroups;
  return StudentGroups;
});

onMounted(async () => {
  try {
    await ensureLoaded();
  } finally {
    ready.value = true;
  }
});
</script>
