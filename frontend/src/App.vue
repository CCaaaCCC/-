<template>
  <el-config-provider>
    <AppLayout v-if="!isFullScreenPage">
      <router-view v-slot="{ Component }">
        <transition name="route-fade-slide" mode="out-in" appear>
          <component :is="Component" :key="route.fullPath" />
        </transition>
      </router-view>
    </AppLayout>
    <router-view v-else v-slot="{ Component }">
      <transition name="route-fade-slide" mode="out-in" appear>
        <component :is="Component" :key="route.fullPath" />
      </transition>
    </router-view>
    <FloatingAIAssistant />
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';
import { useRoute } from 'vue-router';
import AppLayout from './components/AppLayout.vue';

const FloatingAIAssistant = defineAsyncComponent(() => import('./components/FloatingAIAssistant.vue'));

const route = useRoute();
const isFullScreenPage = computed(() => {
  return ['Login', 'DashboardDisplay', 'HomeRedirect'].includes(route.name?.toString() || '');
});
</script>

<style>
.route-fade-slide-enter-active,
.route-fade-slide-leave-active {
  transition:
    opacity var(--motion-base) var(--ease-standard),
    transform var(--motion-base) var(--ease-standard),
    filter var(--motion-base) var(--ease-standard);
}

.route-fade-slide-enter-from,
.route-fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.992);
  filter: blur(2px);
}

@media (prefers-reduced-motion: reduce) {
  .route-fade-slide-enter-active,
  .route-fade-slide-leave-active {
    transition-duration: 0ms;
  }

  .route-fade-slide-enter-from,
  .route-fade-slide-leave-to {
    transform: none;
    filter: none;
  }
}
</style>
