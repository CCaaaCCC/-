import { computed, ref } from 'vue';
import { getMyProfile, type UserProfile } from '../api/profile';

let cachedProfile: UserProfile | null = null;
let loadingPromise: Promise<UserProfile> | null = null;

export function useCurrentUser() {
  const profile = ref<UserProfile | null>(cachedProfile);
  const loading = ref(false);
  const error = ref<any>(null);

  const role = computed(() => profile.value?.role || 'student');
  const isTeacher = computed(() => ['teacher', 'admin'].includes(role.value));

  const ensureLoaded = async () => {
    if (cachedProfile) return cachedProfile;
    if (!loadingPromise) {
      loading.value = true;
      loadingPromise = getMyProfile()
        .then((p) => {
          cachedProfile = p;
          profile.value = p;
          return p;
        })
        .catch((e) => {
          error.value = e;
          throw e;
        })
        .finally(() => {
          loading.value = false;
          loadingPromise = null;
        });
    }
    return loadingPromise;
  };

  return {
    profile,
    role,
    isTeacher,
    loading,
    error,
    ensureLoaded,
  };
}

