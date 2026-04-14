type FastApiValidationItem = {
  loc?: Array<string | number>;
  msg?: string;
};

type MaybeAxiosLikeError = {
  message?: string;
  response?: {
    data?: any;
    status?: number;
  };
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
