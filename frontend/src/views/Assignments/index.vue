<template>
  <div class="role-dispatcher">
    <el-skeleton v-if="!ready" :rows="6" animated />
    <component v-else :is="currentView" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AdminAssignments from './AdminAssignments.vue';
import TeacherAssignments from './TeacherAssignments.vue';
import StudentAssignments from './StudentAssignments.vue';
import { useCurrentUser } from '../../composables/useCurrentUser';

const { role, ensureLoaded } = useCurrentUser();
const ready = ref(false);

const currentView = computed(() => {
  if (role.value === 'admin') return AdminAssignments;
  if (role.value === 'teacher') return TeacherAssignments;
  return StudentAssignments;
});

onMounted(async () => {
  try {
    await ensureLoaded();
  } finally {
    ready.value = true;
  }
});
</script>
