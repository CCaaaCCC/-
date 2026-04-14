<template>
  <div class="role-dispatcher">
    <el-skeleton v-if="!ready" :rows="6" animated />
    <component v-else :is="currentView" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AdminPlants from './AdminPlants.vue';
import TeacherPlants from './TeacherPlants.vue';
import StudentPlants from './StudentPlants.vue';
import { useCurrentUser } from '../../composables/useCurrentUser';

const { role, ensureLoaded } = useCurrentUser();
const ready = ref(false);

const currentView = computed(() => {
  if (role.value === 'admin') return AdminPlants;
  if (role.value === 'teacher') return TeacherPlants;
  return StudentPlants;
});

onMounted(async () => {
  try {
    await ensureLoaded();
  } finally {
    ready.value = true;
  }
});
</script>
