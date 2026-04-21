type FastApiValidationItem = {
  loc?: Array<string | number>;
  msg?: string;
};

type MaybeAxiosLikeError = {
  status?: number;
  message?: string;
  response?: {
    data?: any;
    status?: number;
  };
};

type ActionErrorMessageOptions = {
  action?: string;
  fallback?: string;
  unauthorizedMessage?: string;
  forbiddenMessage?: string;
  serverErrorMessage?: string;
  networkErrorMessage?: string;
};

const normalizeDetail = (detail: unknown): string | null => {
  if (!detail) {
    return null;
  }

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const first = detail[0] as FastApiValidationItem | undefined;
    if (!first) {
      return null;
    }

    const location = Array.isArray(first.loc) ? first.loc.join('.') : '';
    if (first.msg && location) {
      return `${location}: ${first.msg}`;
    }
    if (first.msg) {
      return first.msg;
    }
    return null;
  }

  if (typeof detail === 'object') {
    const maybeMessage = (detail as any).message;
    if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
      return maybeMessage;
    }
  }

  return null;
};

export const getErrorMessage = (error: unknown, fallback = '操作失败'): string => {
  const axiosLike = error as MaybeAxiosLikeError;
  const detail = normalizeDetail(axiosLike?.response?.data?.detail ?? axiosLike?.response?.data);
  if (detail) {
    return detail;
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  return fallback;
};

export const getHttpStatus = (error: unknown): number | null => {
  const axiosLike = error as MaybeAxiosLikeError;
  const status = Number(axiosLike?.response?.status ?? axiosLike?.status);
  return Number.isFinite(status) && status > 0 ? status : null;
};

export const isLikelyNetworkError = (error: unknown): boolean => {
  const axiosLike = error as MaybeAxiosLikeError;
  if (axiosLike?.response) {
    return false;
  }

  const message = String(axiosLike?.message || '').toLowerCase();
  return (
    message.includes('network error')
    || message.includes('failed to fetch')
    || message.includes('load failed')
    || message.includes('timeout')
    || message.includes('ecconnrefused')
  );
};

export const getActionErrorMessage = (
  error: unknown,
  options: ActionErrorMessageOptions = {}
): string => {
  const {
    action = '操作',
    fallback = `${action}失败，请稍后重试`,
    unauthorizedMessage,
    forbiddenMessage,
    serverErrorMessage,
    networkErrorMessage,
  } = options;

  const status = getHttpStatus(error);
  if (status === 401) {
    return unauthorizedMessage || `${action}失败：登录已过期，请重新登录`;
  }
  if (status === 403) {
    return forbiddenMessage || `${action}失败：当前账号暂无权限`;
  }
  if (status !== null && status >= 500) {
    return serverErrorMessage || `${action}失败：服务暂不可用，请稍后重试`;
  }
  if (isLikelyNetworkError(error)) {
    return networkErrorMessage || `${action}失败：无法连接服务，请检查网络或后端状态`;
  }

  return getErrorMessage(error, fallback);
};

export const getFetchErrorMessage = async (response: Response, fallback?: string): Promise<string> => {
  const defaultMessage = fallback || `请求失败 (${response.status})`;

  try {
    const data = await response.json();
    const detail = normalizeDetail(data?.detail ?? data);
    return detail || defaultMessage;
  } catch {
    return defaultMessage;
  }
};
