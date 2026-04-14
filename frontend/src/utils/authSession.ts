export type UserRole = 'admin' | 'teacher' | 'student' | '';

const TOKEN_KEY = 'token';
const ROLE_KEY = 'role';
const USERNAME_KEY = 'username';

const KNOWN_ROLES = new Set<UserRole>(['admin', 'teacher', 'student', '']);

const readStorage = (key: string): string => {
  try {
    return localStorage.getItem(key) || '';
  } catch {
    return '';
  }
};

const removeStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage errors and keep the app usable.
  }
};

export const getAuthToken = (): string => readStorage(TOKEN_KEY);

export const getUserRole = (): UserRole => {
  const role = readStorage(ROLE_KEY) as UserRole;
  return KNOWN_ROLES.has(role) ? role : '';
};

export const clearAuthSession = (): void => {
  removeStorage(TOKEN_KEY);
  removeStorage(ROLE_KEY);
  removeStorage(USERNAME_KEY);
};
