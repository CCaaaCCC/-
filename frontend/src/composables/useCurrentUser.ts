import { computed, ref } from 'vue';
import { getMyProfile, type UserProfile } from '../api/profile';

let cachedProfile: UserProfile | null = null;
let loadingPromise: Promise<UserProfile> | null = null;
let cachedError: unknown = null;
let lastFailedAt = 0;

const PROFILE_RETRY_COOLDOWN_MS = 3000;

export function useCurrentUser() {
  const profile = ref<UserProfile | null>(cachedProfile);
  const loading = ref(false);
  const error = ref<unknown>(cachedError);

  const role = computed(() => profile.value?.role || 'student');
  const isTeacher = computed(() => ['teacher', 'admin'].includes(role.value));

  const ensureLoaded = async () => {
    if (cachedProfile) return cachedProfile;
    if (loadingPromise) return loadingPromise;

    const now = Date.now();
    if (cachedError && now - lastFailedAt < PROFILE_RETRY_COOLDOWN_MS) {
      throw cachedError;
    }

    if (!loadingPromise) {
      loading.value = true;
      error.value = null;
      loadingPromise = getMyProfile()
        .then((p) => {
          cachedProfile = p;
          cachedError = null;
          lastFailedAt = 0;
          profile.value = p;
          return p;
        })
        .catch((e) => {
          cachedError = e;
          lastFailedAt = Date.now();
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

