import { ElMessage } from 'element-plus';

let guardsInstalled = false;
let lastNotificationAt = 0;

const shouldNotify = (throttleMs: number): boolean => {
  const now = Date.now();
  if (now - lastNotificationAt < throttleMs) {
    return false;
  }
  lastNotificationAt = now;
  return true;
};

const getReasonMessage = (reason: unknown): string => {
  if (reason instanceof Error) {
    return reason.message || reason.name;
  }
  return String(reason || '');
};

const isAbortLikeError = (reason: unknown): boolean => {
  const message = getReasonMessage(reason).toLowerCase();
  return message.includes('aborterror') || message.includes('aborted');
};

export const installRuntimeGuards = (throttleMs = 4000): void => {
  if (guardsInstalled || typeof window === 'undefined') {
    return;
  }

  guardsInstalled = true;

  window.addEventListener('error', (event) => {
    const message = event?.message || 'Unknown runtime error';
    console.error('[runtime:error]', message, event?.error);
    if (shouldNotify(throttleMs)) {
      ElMessage.error('页面运行异常，请刷新后重试');
    }
  });

  window.addEventListener('unhandledrejection', (event) => {
    if (isAbortLikeError(event?.reason)) {
      return;
    }

    console.error('[runtime:unhandledrejection]', event?.reason);
    if (shouldNotify(throttleMs)) {
      ElMessage.error('请求处理异常，请稍后重试');
    }
  });
};
