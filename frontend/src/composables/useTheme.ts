import { computed, ref } from 'vue';

export type ThemeMode = 'light' | 'dark' | 'modern' | 'system';
export type AppliedTheme = Exclude<ThemeMode, 'system'>;

export const THEME_STORAGE_KEY = 'ui.theme.mode';
export const THEME_MODES: ThemeMode[] = ['light', 'dark', 'modern', 'system'];

const currentTheme = ref<ThemeMode>('light');
const effectiveTheme = ref<AppliedTheme>('light');
let themeInitialized = false;

const hasWindow = typeof window !== 'undefined';
const hasDocument = typeof document !== 'undefined';
const hasMatchMedia = hasWindow && typeof window.matchMedia === 'function';
const systemThemeQuery = hasMatchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

export const isThemeMode = (value: string): value is ThemeMode => {
  return (THEME_MODES as string[]).includes(value);
};

const getSystemAppliedTheme = (): AppliedTheme => {
  return systemThemeQuery?.matches ? 'dark' : 'light';
};

const resolveAppliedTheme = (theme: ThemeMode): AppliedTheme => {
  return theme === 'system' ? getSystemAppliedTheme() : theme;
};

const readStoredTheme = (): ThemeMode => {
  if (!hasWindow) {
    return 'light';
  }

  try {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (saved && isThemeMode(saved)) {
      return saved;
    }
  } catch {
    // Ignore localStorage read errors.
  }

  return 'light';
};

const persistTheme = (theme: ThemeMode) => {
  if (!hasWindow) {
    return;
  }

  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Ignore localStorage write errors.
  }
};

const applyThemeToDom = (theme: ThemeMode) => {
  if (!hasDocument) {
    return;
  }

  const appliedTheme = resolveAppliedTheme(theme);
  effectiveTheme.value = appliedTheme;

  const root = document.documentElement;
  root.classList.remove('theme-light', 'dark', 'theme-modern', 'theme-system');

  if (theme === 'system') {
    root.classList.add('theme-system');
  }

  if (appliedTheme === 'light') {
    root.classList.add('theme-light');
  } else if (appliedTheme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.add('theme-modern');
  }

  root.setAttribute('data-theme', theme);
  root.setAttribute('data-theme-resolved', appliedTheme);
  root.style.colorScheme = appliedTheme === 'dark' ? 'dark' : 'light';
};

const applyThemeInternal = (
  theme: ThemeMode,
  options: {
    persist?: boolean;
  } = {}
) => {
  const shouldPersist = options.persist !== false;
  currentTheme.value = theme;
  applyThemeToDom(theme);
  if (shouldPersist) {
    persistTheme(theme);
  }
};

export const initTheme = () => {
  if (!themeInitialized) {
    const initialTheme = readStoredTheme();
    applyThemeInternal(initialTheme, { persist: false });
    themeInitialized = true;
  } else {
    applyThemeToDom(currentTheme.value);
  }

  return currentTheme.value;
};

if (hasWindow) {
  window.addEventListener('storage', (event) => {
    if (event.key !== THEME_STORAGE_KEY || !event.newValue || !isThemeMode(event.newValue)) {
      return;
    }

    applyThemeInternal(event.newValue, { persist: false });
  });

  const syncSystemTheme = () => {
    if (currentTheme.value === 'system') {
      applyThemeToDom('system');
    }
  };

  if (systemThemeQuery) {
    if ('addEventListener' in systemThemeQuery) {
      systemThemeQuery.addEventListener('change', syncSystemTheme);
    } else if ('addListener' in systemThemeQuery) {
      systemThemeQuery.addListener(syncSystemTheme);
    }
  }
}

export const useTheme = () => {
  const isDark = computed(() => effectiveTheme.value === 'dark');

  const setTheme = (theme: ThemeMode) => {
    if (theme === currentTheme.value) {
      return;
    }

    applyThemeInternal(theme);
  };

  return {
    theme: currentTheme,
    effectiveTheme: computed(() => effectiveTheme.value),
    isDark,
    setTheme,
  };
};
