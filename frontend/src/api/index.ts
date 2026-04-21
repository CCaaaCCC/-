import axios from 'axios';
import router from '../router';
import { getFetchErrorMessage } from '../utils/error';
import { clearAuthSession, getAuthToken } from '../utils/authSession';

type HttpError = Error & { status?: number };

const createHttpError = (message: string, status?: number): HttpError => {
    const error = new Error(message) as HttpError;
    error.name = 'HttpError';
    error.status = status;
    return error;
};

const normalizeApiBase = (raw: string): string => {
    const trimmed = raw.trim().replace(/\/+$/, '');
    return /\/api$/i.test(trimmed) ? trimmed : `${trimmed}/api`;
};

const resolveApiBaseCandidates = (): string[] => {
    const envBase = (import.meta as any)?.env?.VITE_API_BASE_URL as string | undefined;
    if (envBase && envBase.trim()) {
        return [normalizeApiBase(envBase)];
    }

    if (typeof window !== 'undefined') {
        const candidates: string[] = [];
        const pushCandidate = (raw: string) => {
            const normalized = normalizeApiBase(raw);
            if (!candidates.includes(normalized)) {
                candidates.push(normalized);
            }
        };

        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const origin = window.location.origin;
        const isDevFrontendPort = ['5173', '4173', '3000'].includes(window.location.port);

        if (isDevFrontendPort) {
            pushCandidate(`${protocol}//${hostname}:8000`);
            if (hostname === 'localhost') {
                pushCandidate('http://127.0.0.1:8000');
            }
            if (hostname === '127.0.0.1') {
                pushCandidate('http://localhost:8000');
            }
        } else {
            pushCandidate(`${origin}/api`);
            pushCandidate(`${protocol}//${hostname}:8000`);
            if (hostname === 'localhost') {
                pushCandidate('http://127.0.0.1:8000');
            }
            if (hostname === '127.0.0.1') {
                pushCandidate('http://localhost:8000');
            }
        }

        if (candidates.length > 0) {
            return candidates;
        }
    }

    return ['http://localhost:8000/api'];
};

const API_BASE_CANDIDATES = resolveApiBaseCandidates();
let apiBaseCandidateIndex = 0;
let API_BASE_URL = API_BASE_CANDIDATES[apiBaseCandidateIndex];
let AUTH_BASE_URL = API_BASE_URL.replace(/\/api\/?$/i, '');

export const getApiBaseUrl = (): string => API_BASE_URL;
export const getBackendOrigin = (): string => AUTH_BASE_URL;

export const resolveBackendAssetUrl = (raw?: string): string => {
    if (!raw) return '';
    if (/^(https?:|blob:|data:)/i.test(raw)) return raw;
    const normalized = raw.startsWith('/') ? raw : `/${raw}`;
    return `${AUTH_BASE_URL}${normalized}`;
};

// Create axios instance with base URL pointing to the backend
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000
});

// Separate axios instance for auth endpoints (not under /api)
const authApi = axios.create({
    baseURL: AUTH_BASE_URL,
    timeout: 10000
});

const applyApiBaseCandidate = (nextIndex: number): void => {
    apiBaseCandidateIndex = nextIndex;
    API_BASE_URL = API_BASE_CANDIDATES[apiBaseCandidateIndex];
    AUTH_BASE_URL = API_BASE_URL.replace(/\/api\/?$/i, '');
    api.defaults.baseURL = API_BASE_URL;
    authApi.defaults.baseURL = AUTH_BASE_URL;
};

const promoteApiBaseCandidate = (): boolean => {
    if (apiBaseCandidateIndex + 1 >= API_BASE_CANDIDATES.length) {
        return false;
    }
    applyApiBaseCandidate(apiBaseCandidateIndex + 1);
    return true;
};

const isNetworkFailure = (error: any): boolean => {
    if (error?.response) {
        return false;
    }
    const message = String(error?.message || '').toLowerCase();
    return (
        message.includes('network error')
        || message.includes('failed to fetch')
        || message.includes('load failed')
        || message.includes('timeout')
    );
};

const buildNetworkFailureMessage = (error: unknown, context: 'api' | 'auth' | 'stream' = 'api'): string => {
    const reason = String((error as any)?.message || '').trim();
    const contextText =
        context === 'stream'
            ? '流式请求无法连接后端'
            : context === 'auth'
                ? '认证请求无法连接后端'
                : '请求无法连接后端';
    const reasonText = reason ? `，原因：${reason}` : '';
    const candidateText = API_BASE_CANDIDATES.join(' -> ');

    return `Network Error: ${contextText}${reasonText}。当前地址：${API_BASE_URL}；候选地址：${candidateText}`;
};

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
        const token = getAuthToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
        const config = (error?.config || {}) as any;
        if (isNetworkFailure(error) && !config.__apiBaseRetried && promoteApiBaseCandidate()) {
            config.__apiBaseRetried = true;
            config.baseURL = api.defaults.baseURL;
            return api.request(config);
        }

        if (isNetworkFailure(error)) {
            return Promise.reject(createHttpError(buildNetworkFailureMessage(error, 'api')));
        }

    if (error.response && error.response.status === 401) {
      // Clear local storage and redirect to login
            clearAuthSession();
      router.push('/login');
    }
    return Promise.reject(error);
  }
);

authApi.interceptors.response.use(
    (response) => response,
    async (error) => {
        const config = (error?.config || {}) as any;
        if (isNetworkFailure(error) && !config.__apiBaseRetried && promoteApiBaseCandidate()) {
            config.__apiBaseRetried = true;
            config.baseURL = authApi.defaults.baseURL;
            return authApi.request(config);
        }

        if (isNetworkFailure(error)) {
            return Promise.reject(createHttpError(buildNetworkFailureMessage(error, 'auth')));
        }

        return Promise.reject(error);
    }
);

// Login function
export const login = async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await authApi.post('/token', formData);
    return response.data;
};

export interface RegisterPayload {
    username: string;
    password: string;
    role: 'student' | 'teacher';
    invite_code: string;
    real_name?: string;
    email?: string;
    student_id?: string;
    teacher_id?: string;
}

export interface RegisterResult {
    id: number;
    username: string;
    role: string;
    class_id?: number | null;
    created_by?: number | null;
    message: string;
}

export const registerUser = async (payload: RegisterPayload): Promise<RegisterResult> => {
    const response = await api.post<RegisterResult>('/auth/register', payload);
    return response.data;
};

// Logout function
export const logoutUser = async () => {
    try {
        await api.post('/auth/logout');
    } catch (e) {
        console.error('Logout failed:', e);
    }
};

// Interfaces matching the backend Pydantic models
export interface Telemetry {
    id: number;
    device_id: number;
    temp: number;
    humidity: number;
    soil_moisture: number;
    light: number;
    timestamp: string;
}

export interface Device {
    id: number;
    device_name: string;
    status: number;
    last_seen: string | null;
    pump_state: number;
    fan_state: number;
    fan_speed: number;
    light_state: number;
    light_brightness: number;
}

export interface ControlRequest {
    pump_state?: number;
    fan_state?: number;
    fan_speed?: number;
    light_state?: number;
    light_brightness?: number;
}

export interface DeviceCreateRequest {
    device_name: string;
    status?: number;
    pump_state?: number;
    fan_state?: number;
    fan_speed?: number;
    light_state?: number;
    light_brightness?: number;
}

export interface Assignment {
    id: number;
    title: string;
    description?: string;
    teacher_id?: number;
    teacher_name?: string;
    class_id?: number;
    class_name?: string;
    device_id?: number;
    device_name?: string;
    start_date?: string;
    due_date?: string;
    created_at: string;
    submission_count: number;
    requirement?: string;
    template?: string;
    is_published: boolean;
    can_manage?: boolean;
    can_grade?: boolean;
}

export interface AssignmentListResponse {
    items: Assignment[];
    total: number;
    page: number;
    page_size: number;
}

export interface PlantProfileItem {
    id: number;
    plant_name: string;
    species?: string;
    class_id?: number;
    class_name?: string;
    group_id?: number;
    group_name?: string;
    device_id?: number;
    device_name?: string;
    plant_date?: string;
    cover_image?: string;
    status?: string;
    expected_harvest_date?: string;
    description?: string;
    growth_record_count?: number;
    created_by?: number | null;
    can_manage?: boolean;
    created_at?: string;
}

export interface GroupItem {
    id: number;
    group_name: string;
    class_id: number;
    class_name?: string;
    device_id?: number;
    device_name?: string;
    description?: string;
    created_by?: number | null;
    can_manage?: boolean;
    member_count?: number;
    members?: Array<{
        id: number;
        student_id: number;
        student_name?: string;
        username?: string;
        role: string;
    }>;
    created_at?: string;
}

export interface UserProfile {
    id: number;
    username: string;
    role: string;
    real_name?: string;
    avatar_url?: string;
    email?: string;
    class_id?: number;
    class_name?: string;
    todos: {
        pending_assignments: number;
        overdue_assignments: number;
        assignments_to_grade: number;
        plants_in_class: number;
    };
    upcoming_assignments: Assignment[];
}

export interface NotificationItem {
    id: number;
    user_id: number;
    actor_id?: number;
    actor_name?: string;
    notification_type: string;
    title: string;
    content?: string;
    content_id?: number;
    comment_id?: number;
    is_read: boolean;
    created_at: string;
}

export interface OperationLogItem {
    id: number;
    operator_id: number;
    operator_name?: string;
    operation_type: string;
    target_user_id?: number;
    target_user_name?: string;
    details?: string;
    created_at: string;
}

export interface OperationLogsResponse {
    items: OperationLogItem[];
    total: number;
}

export interface AssignmentSubmission {
    id: number;
    assignment_id: number;
    student_id: number;
    student_name?: string;
    status: string;
    observations?: string;
    conclusion?: string;
    experiment_date?: string;
    submitted_at?: string;
    score?: number | null;
    teacher_comment?: string;
    temp_records?: string;
    humidity_records?: string;
    soil_moisture_records?: string;
    light_records?: string;
    photos?: string;
    report_file_name?: string;
    report_file_path?: string;
    report_file_size?: number;
}

export interface AssignmentAIFeedback {
    score_band: string;
    strengths: string[];
    improvements: string[];
    teacher_comment_draft: string;
    source: string;
    debug_context?: {
        assignment_id: number;
        submission_id: number;
    };
}

export type TeachingContentType = 'article' | 'video' | 'image' | 'document' | 'pdf';

export interface TeachingContentBasePayload {
    title: string;
    tags: string[];
    content_type: TeachingContentType | string;
    content?: string;
    video_url?: string;
    file_path?: string;
    cover_image?: string;
}

export interface TeachingContentCreatePayload extends TeachingContentBasePayload {
    is_published?: boolean;
}

export type TeachingContentUpdatePayload = Partial<TeachingContentBasePayload> & {
    is_published?: boolean;
};

export interface TeachingContentListItem {
    id: number;
    title: string;
    tags: string[];
    content_type: TeachingContentType | string;
    content?: string | null;
    video_url?: string | null;
    file_path?: string | null;
    cover_image?: string | null;
    author_id: number;
    author_name?: string | null;
    author_username?: string | null;
    publisher_name?: string | null;
    view_count: number;
    is_published: boolean;
    published_at?: string | null;
    created_at: string;
    updated_at: string;
    can_edit?: boolean;
    can_delete?: boolean;
    can_publish?: boolean;
}

export interface TeachingContentDetail extends TeachingContentListItem {}

export interface ContentListParams {
    tag?: string;
    content_type?: string;
    is_published?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
}

export interface ContentListResponse {
    items: TeachingContentListItem[];
    total: number;
    page: number;
    page_size: number;
}

export interface ContentAIPolishPayload {
    bullet_points: string;
    mode?: 'conservative' | 'expanded' | 'article';
    tone?: string;
    target_length?: string;
}

export interface ContentAIPolishResult {
    title_suggestion: string;
    organized_content: string;
    source: string;
}

export interface StudentLearningRecord {
    id: number;
    student_id: number;
    content_id: number;
    status: 'not_started' | 'in_progress' | 'completed' | string;
    progress_percent: number;
    time_spent_seconds: number;
    last_accessed: string;
    completed_at?: string | null;
}

export interface ContentComment {
    id: number;
    content_id: number;
    student_id: number;
    student_name?: string | null;
    student_avatar_url?: string | null;
    parent_id?: number | null;
    comment: string;
    like_count: number;
    liked: boolean;
    teacher_reply?: string | null;
    reply_at?: string | null;
    created_at: string;
    replies: ContentComment[];
}

export interface ContentCommentLikeResponse {
    comment_id: number;
    liked: boolean;
    like_count: number;
}

export interface LearningStatsResponse {
    total_students: number;
    total_contents: number;
    total_learning_records: number;
    completed_count: number;
    in_progress_count: number;
    not_started_count: number;
    completion_rate: number;
    average_progress: number;
}

export interface StudentProgress {
    student_id: number;
    student_name: string;
    total_contents: number;
    completed_count: number;
    in_progress_count: number;
    completion_rate: number;
    total_time_spent: number;
}

export type MarketProductStatus = 'on_sale' | 'sold' | 'off_shelf';

export interface MarketProduct {
    id: number;
    title: string;
    description?: string | null;
    price?: number | null;
    location: string;
    contact_info: string;
    image_url?: string | null;
    seller_id: number;
    seller_name?: string | null;
    status: MarketProductStatus | string;
    view_count: number;
    created_at: string;
    updated_at: string;
    can_edit?: boolean;
    can_delete?: boolean;
}

export interface MarketProductCreatePayload {
    title: string;
    description?: string;
    price?: number;
    location: string;
    contact_info: string;
    image_url?: string;
    status?: MarketProductStatus;
}

export interface MarketProductUpdatePayload {
    title?: string;
    description?: string;
    price?: number;
    location?: string;
    contact_info?: string;
    image_url?: string;
    status?: MarketProductStatus;
}

export interface MarketProductListResponse {
    items: MarketProduct[];
    total: number;
    page: number;
    page_size: number;
}

export interface TelemetryRealtimePayload {
    type: 'snapshot' | 'telemetry_update' | 'control_update';
    device_id: number;
    timestamp?: string;
    telemetry: {
        temp: number | null;
        humidity: number | null;
        soil_moisture: number | null;
        light: number | null;
    };
    actuators: {
        pump_state: number;
        fan_state: number;
        fan_speed: number;
        light_state: number;
        light_brightness: number;
    };
}

export interface AIScienceAskRequest {
    question: string;
    device_id?: number;
    conversation_history?: Array<{
        role: 'user' | 'assistant';
        content: string;
    }>;
    enable_deep_thinking?: boolean;
    enable_web_search?: boolean;
}

export interface AIConversationAskRequest {
    question: string;
    device_id?: number;
    enable_deep_thinking?: boolean;
    enable_web_search?: boolean;
}

export interface AISourceLink {
    title: string;
    url: string;
    snippet?: string | null;
}

export interface AIScienceAskResponse {
    answer: string;
    source: string;
    model: string;
    deep_thinking: boolean;
    web_search_enabled: boolean;
    web_search_used: boolean;
    web_search_notice?: string | null;
    citations: AISourceLink[];
}

export interface AIScienceStreamMeta {
    source?: string;
    model?: string;
    deep_thinking?: boolean;
    web_search_enabled?: boolean;
    web_search_used?: boolean;
    web_search_notice?: string | null;
    citations?: AISourceLink[];
}

export interface AIConversationSummary {
    id: number;
    title: string;
    is_pinned: boolean;
    pinned_at?: string | null;
    created_at: string;
    updated_at: string;
    last_message_at?: string | null;
    message_count: number;
    preview?: string | null;
}

export interface AIConversationMessage {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    reasoning?: string | null;
    source?: string | null;
    model?: string | null;
    citations: AISourceLink[];
    web_search_notice?: string | null;
    status: 'done' | 'error';
    created_at: string;
}

export interface AIConversationDetail {
    id: number;
    title: string;
    is_pinned: boolean;
    pinned_at?: string | null;
    created_at: string;
    updated_at: string;
    last_message_at?: string | null;
    messages: AIConversationMessage[];
}

// API functions
export const getDevices = async (): Promise<Device[]> => {
    const response = await api.get<Device[]>('/devices');
    return response.data;
};

export const createDevice = async (data: DeviceCreateRequest): Promise<Device> => {
    const response = await api.post<Device>('/devices', data);
    return response.data;
};

export const getHistory = async (deviceId: number): Promise<Telemetry[]> => {
    const response = await api.get<Telemetry[]>(`/history/${deviceId}`);
    return response.data;
};

export const controlDevice = async (deviceId: number, data: ControlRequest): Promise<void> => {
    await api.post(`/control/${deviceId}`, data);
};

export const askScienceAssistant = async (data: AIScienceAskRequest): Promise<AIScienceAskResponse> => {
    const response = await api.post<AIScienceAskResponse>('/ai/science-assistant', data);
    return response.data;
};

const streamScienceAssistantByPath = async (
    path: string,
    data: AIScienceAskRequest | AIConversationAskRequest,
    onToken: (text: string, reasoning?: string) => void,
    onMeta?: (meta: AIScienceStreamMeta) => void,
    options?: { signal?: AbortSignal }
): Promise<void> => {
    const token = getAuthToken();
    let response: Response | null = null;
    let streamBaseRetried = false;

    while (!response) {
        const baseUrl = api.defaults.baseURL || API_BASE_URL;
        try {
            response = await fetch(`${baseUrl}${path}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {})
                },
                body: JSON.stringify(data),
                signal: options?.signal
            });
        } catch (error: any) {
            if (error?.name === 'AbortError') {
                throw error;
            }

            if (!streamBaseRetried && isNetworkFailure(error) && promoteApiBaseCandidate()) {
                streamBaseRetried = true;
                continue;
            }

            throw createHttpError(buildNetworkFailureMessage(error, 'stream'));
        }
    }

    if (!response.ok) {
        const message = await getFetchErrorMessage(response, `请求失败 (${response.status})`);
        throw createHttpError(message, response.status);
    }

    if (!response.body) {
        throw createHttpError('浏览器不支持流式响应');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    const processBlock = (blockText: string): boolean => {
        const block = blockText.trim();
        if (!block) {
            return false;
        }

        let eventName = 'message';
        const dataLines: string[] = [];

        for (const line of block.split('\n')) {
            if (line.startsWith('event:')) {
                eventName = line.slice('event:'.length).trim();
            } else if (line.startsWith('data:')) {
                dataLines.push(line.slice('data:'.length).trim());
            }
        }

        if (dataLines.length === 0) {
            return false;
        }

        const payloadText = dataLines.join('\n');
        let payload: any = {};
        try {
            payload = JSON.parse(payloadText);
        } catch {
            payload = { text: payloadText };
        }

        if (eventName === 'meta') {
            onMeta?.(payload);
            return false;
        }

        if (eventName === 'token') {
            if (typeof payload.text === 'string' || typeof payload.reasoning === 'string') {
                onToken(payload.text || '', payload.reasoning || '');
            }
            return false;
        }

        if (eventName === 'error') {
            throw createHttpError(String(payload.message || '流式响应异常'));
        }

        return eventName === 'done';
    };

    while (true) {
        const { value, done } = await reader.read();
        if (done) {
            buffer += decoder.decode();
            break;
        }

        buffer += decoder.decode(value, { stream: true });
        buffer = buffer.replace(/\r\n/g, '\n');

        let sepIndex = buffer.indexOf('\n\n');
        while (sepIndex !== -1) {
            const block = buffer.slice(0, sepIndex);
            buffer = buffer.slice(sepIndex + 2);

            if (processBlock(block)) {
                return;
            }

            sepIndex = buffer.indexOf('\n\n');
        }
    }

    buffer = buffer.replace(/\r\n/g, '\n');

    if (buffer.trim()) {
        processBlock(buffer);
    }
};

export const streamScienceAssistant = async (
    data: AIScienceAskRequest,
    onToken: (text: string, reasoning?: string) => void,
    onMeta?: (meta: AIScienceStreamMeta) => void,
    options?: { signal?: AbortSignal }
): Promise<void> => {
    await streamScienceAssistantByPath('/ai/science-assistant/stream', data, onToken, onMeta, options);
};

export const getAIConversations = async (): Promise<AIConversationSummary[]> => {
    const response = await api.get<AIConversationSummary[]>('/ai/conversations');
    return response.data;
};

export const createAIConversation = async (payload?: { title?: string }): Promise<AIConversationSummary> => {
    const response = await api.post<AIConversationSummary>('/ai/conversations', payload || {});
    return response.data;
};

export const getAIConversationDetail = async (conversationId: number): Promise<AIConversationDetail> => {
    const response = await api.get<AIConversationDetail>(`/ai/conversations/${conversationId}`);
    return response.data;
};

export const renameAIConversation = async (conversationId: number, title: string): Promise<AIConversationSummary> => {
    const response = await api.patch<AIConversationSummary>(`/ai/conversations/${conversationId}/title`, { title });
    return response.data;
};

export const pinAIConversation = async (conversationId: number, isPinned: boolean): Promise<AIConversationSummary> => {
    const response = await api.patch<AIConversationSummary>(`/ai/conversations/${conversationId}/pin`, { is_pinned: isPinned });
    return response.data;
};

export const deleteAIConversation = async (conversationId: number): Promise<void> => {
    await api.delete(`/ai/conversations/${conversationId}`);
};

export const askScienceAssistantInConversation = async (
    conversationId: number,
    data: AIConversationAskRequest
): Promise<AIScienceAskResponse> => {
    const response = await api.post<AIScienceAskResponse>(`/ai/conversations/${conversationId}/science-assistant`, data);
    return response.data;
};

export const streamScienceAssistantInConversation = async (
    conversationId: number,
    data: AIConversationAskRequest,
    onToken: (text: string, reasoning?: string) => void,
    onMeta?: (meta: AIScienceStreamMeta) => void,
    options?: { signal?: AbortSignal }
): Promise<void> => {
    await streamScienceAssistantByPath(
        `/ai/conversations/${conversationId}/science-assistant/stream`,
        data,
        onToken,
        onMeta,
        options
    );
};

export const createTelemetrySocket = (
    deviceId: number,
    onMessage: (payload: TelemetryRealtimePayload) => void,
    onClose?: () => void
): WebSocket => {
    const token = getAuthToken();
    const backendUrl = (api.defaults.baseURL || API_BASE_URL).replace(/\/api\/?$/, '') || AUTH_BASE_URL;
    const backend = new URL(backendUrl, window.location.origin);
    const wsProtocol = backend.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${wsProtocol}//${backend.host}/ws/telemetry/${deviceId}?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data) as TelemetryRealtimePayload;
            onMessage(payload);
        } catch (e) {
            console.error('解析实时数据失败:', e);
        }
    };
    ws.onclose = () => {
        if (onClose) onClose();
    };
    return ws;
};

// Export function
export const exportTelemetry = async (
    deviceId: number,
    startDate: string,
    endDate: string,
    format: 'csv' | 'xlsx' = 'csv'
): Promise<Blob> => {
    const response = await api.post(
        '/telemetry/export',
        {
            device_id: deviceId,
            start_date: startDate,
            end_date: endDate
        },
        {
            params: { export_format: format },
            responseType: 'blob'
        }
    );
    return response.data;
};

// 班级 API
export const updateClass = async (id: number, cls: {
    class_name?: string;
    grade?: string;
    description?: string;
    teacher_id?: number;
    is_active?: boolean;
}): Promise<any> => {
    const response = await api.put(`/classes/${id}`, cls);
    return response.data;
};

export const deleteClass = async (id: number): Promise<void> => {
    await api.delete(`/classes/${id}`);
};

export const getClasses = async (params?: {
    grade?: string;
    is_active?: boolean;
}): Promise<any[]> => {
    const response = await api.get('/classes', { params });
    return response.data;
};

export const createClass = async (cls: {
    class_name: string;
    grade?: string;
    description?: string;
    teacher_id?: number;
}): Promise<any> => {
    const response = await api.post('/classes', cls);
    return response.data;
};

export const refreshClassInviteCode = async (classId: number): Promise<any> => {
    const response = await api.post(`/classes/${classId}/refresh-invite-code`);
    return response.data;
};

// 班级设备绑定 API
export const getClassDevices = async (classId: number): Promise<any[]> => {
    const response = await api.get(`/classes/${classId}/devices`);
    return response.data;
};

export const bindClassDevice = async (classId: number, deviceId: number): Promise<any> => {
    const response = await api.post(`/classes/${classId}/devices/bind`, { class_id: classId, device_id: deviceId });
    return response.data;
};

export const unbindClassDevice = async (classId: number, bindId: number): Promise<any> => {
    const response = await api.delete(`/classes/${classId}/devices/unbind/${bindId}`);
    return response.data;
};

export const getStudentDevice = async (studentId: number): Promise<any[]> => {
    const response = await api.get(`/students/${studentId}/device`);
    return response.data;
};

// 用户管理 API
export const getUsers = async (params?: {
    role?: string;
    class_id?: number;
    is_active?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
}): Promise<any> => {
    const response = await api.get('/users', { params });
    return response.data;
};

export const createUser = async (user: any): Promise<any> => {
    const response = await api.post('/users', user);
    return response.data;
};

export const updateUser = async (id: number, user: any): Promise<any> => {
    const response = await api.put(`/users/${id}`, user);
    return response.data;
};

export const deleteUser = async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
};

export const resetPassword = async (id: number, newPassword: string): Promise<void> => {
    await api.post(`/users/${id}/reset-password`, null, {
        params: { new_password: newPassword }
    });
};

export const toggleUserActive = async (id: number): Promise<{ message: string; is_active: boolean }> => {
    const response = await api.post(`/users/${id}/toggle-active`);
    return response.data;
};

export const getUserStats = async (): Promise<any> => {
    const response = await api.get('/stats/users');
    return response.data;
};

export const importUsers = async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/users/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const exportUsers = async (): Promise<Blob> => {
    const response = await api.get('/users-export', {
        responseType: 'blob'
    });
    return response.data;
};

// 批量操作 API
export const batchDeleteUsers = async (userIds: number[]): Promise<any> => {
    const response = await api.post('/users/batch-delete', { user_ids: userIds });
    return response.data;
};

export const batchUpdateClass = async (userIds: number[], classId: number | null): Promise<any> => {
    const response = await api.post('/users/batch-update-class', {
        user_ids: userIds,
        class_id: classId
    });
    return response.data;
};

export const batchResetPassword = async (userIds: number[], newPassword: string): Promise<any> => {
    const response = await api.post('/users/batch-reset-password', {
        user_ids: userIds,
        new_password: newPassword
    });
    return response.data;
};

// 教学内容管理 API
export const getContents = async (params?: ContentListParams): Promise<ContentListResponse> => {
    const response = await api.get<ContentListResponse>('/content/contents', { params });
    return response.data;
};

export const uploadTeachingContentFile = async (
    file: File
): Promise<{ url: string; filename: string; size: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/content/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const getContent = async (id: number): Promise<TeachingContentDetail> => {
    const response = await api.get<TeachingContentDetail>(`/content/contents/${id}`);
    return response.data;
};

export const createContent = async (content: TeachingContentCreatePayload): Promise<TeachingContentDetail> => {
    const response = await api.post<TeachingContentDetail>('/content/contents', content);
    return response.data;
};

export const updateContent = async (id: number, content: TeachingContentUpdatePayload): Promise<TeachingContentDetail> => {
    const response = await api.put<TeachingContentDetail>(`/content/contents/${id}`, content);
    return response.data;
};

export const deleteContent = async (id: number): Promise<void> => {
    await api.delete(`/content/contents/${id}`);
};

export const publishContent = async (id: number): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(`/content/contents/${id}/publish`);
    return response.data;
};

export const polishTeachingContent = async (payload: ContentAIPolishPayload): Promise<ContentAIPolishResult> => {
    const response = await api.post<ContentAIPolishResult>('/content/ai/polish', payload);
    return response.data;
};

export const getMyLearning = async (): Promise<StudentLearningRecord[]> => {
    const response = await api.get<StudentLearningRecord[]>('/content/my-learning');
    return response.data;
};

export const startLearning = async (contentId: number): Promise<StudentLearningRecord> => {
    const response = await api.post<StudentLearningRecord>(`/content/contents/${contentId}/start`);
    return response.data;
};

export const completeLearning = async (contentId: number): Promise<StudentLearningRecord> => {
    const response = await api.post<StudentLearningRecord>(`/content/contents/${contentId}/complete`);
    return response.data;
};

export const getComments = async (contentId: number): Promise<ContentComment[]> => {
    const response = await api.get<ContentComment[]>(`/content/contents/${contentId}/comments`);
    return response.data;
};

export const addComment = async (contentId: number, comment: string): Promise<ContentComment> => {
    const response = await api.post<ContentComment>(`/content/contents/${contentId}/comments`, { comment });
    return response.data;
};

export const replyComment = async (commentId: number, comment: string): Promise<ContentComment> => {
    const response = await api.post<ContentComment>(`/content/comments/${commentId}/reply`, { comment });
    return response.data;
};

export const toggleCommentLike = async (commentId: number): Promise<ContentCommentLikeResponse> => {
    const response = await api.post<ContentCommentLikeResponse>(`/content/comments/${commentId}/like`);
    return response.data;
};

export const getLearningStats = async (): Promise<LearningStatsResponse> => {
    const response = await api.get<LearningStatsResponse>('/content/stats/overview');
    return response.data;
};

export const getStudentsProgress = async (): Promise<StudentProgress[]> => {
    const response = await api.get<StudentProgress[]>('/content/stats/students');
    return response.data;
};

// 线下商城 API
export const getMarketProducts = async (params?: {
    search?: string;
    status?: MarketProductStatus | string;
    mine?: boolean;
    page?: number;
    page_size?: number;
}): Promise<MarketProductListResponse> => {
    const response = await api.get<MarketProductListResponse>('/market/products', { params });
    return response.data;
};

export const getMarketProduct = async (id: number): Promise<MarketProduct> => {
    const response = await api.get<MarketProduct>(`/market/products/${id}`);
    return response.data;
};

export const createMarketProduct = async (payload: MarketProductCreatePayload): Promise<MarketProduct> => {
    const response = await api.post<MarketProduct>('/market/products', payload);
    return response.data;
};

export const updateMarketProduct = async (
    id: number,
    payload: MarketProductUpdatePayload
): Promise<MarketProduct> => {
    const response = await api.put<MarketProduct>(`/market/products/${id}`, payload);
    return response.data;
};

export const deleteMarketProduct = async (id: number): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`/market/products/${id}`);
    return response.data;
};

export const uploadMarketImage = async (
    file: File
): Promise<{ url: string; filename: string; size: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/market/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

// 实验报告 API
export const getAssignments = async (params?: any): Promise<Assignment[] | AssignmentListResponse> => {
    const response = await api.get<Assignment[] | AssignmentListResponse>('/assignments', { params });
    return response.data;
};

export const createAssignment = async (assignment: any): Promise<any> => {
    const response = await api.post('/assignments', assignment);
    return response.data;
};

export const setAssignmentPublishStatus = async (assignmentId: number, isPublished: boolean): Promise<any> => {
    const response = await api.post(`/assignments/${assignmentId}/publish`, {
        is_published: isPublished
    });
    return response.data;
};

export const deleteAssignment = async (assignmentId: number): Promise<any> => {
    const response = await api.delete(`/assignments/${assignmentId}`);
    return response.data;
};

export const getSubmissions = async (assignmentId: number, params?: any): Promise<any[]> => {
    const response = await api.get(`/assignments/${assignmentId}/submissions`, { params });
    return response.data;
};

export const getMySubmission = async (assignmentId: number): Promise<any> => {
    const response = await api.get(`/assignments/${assignmentId}/my-submission`);
    return response.data;
};

export const submitAssignment = async (assignmentId: number, submission: any): Promise<any> => {
    const response = await api.post(`/assignments/${assignmentId}/submit`, submission);
    return response.data;
};

export const submitAssignmentWithFile = async (
    assignmentId: number,
    payload: {
        experiment_date?: string;
        observations?: string;
        conclusion?: string;
        temp_records?: string;
        humidity_records?: string;
        soil_moisture_records?: string;
        light_records?: string;
        photos?: string;
    },
    file: File
): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    Object.entries(payload).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            formData.append(key, String(value));
        }
    });

    const response = await api.post(`/assignments/${assignmentId}/submit-with-file`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const downloadSubmissionReport = async (submissionId: number): Promise<Blob> => {
    const response = await api.get(`/assignments/submissions/${submissionId}/file`, {
        responseType: 'blob'
    });
    return response.data;
};

export const gradeAssignment = async (assignmentId: number, submissionId: number, grade: any): Promise<any> => {
    const response = await api.post(`/assignments/${assignmentId}/grade`, {
        submission_id: submissionId,
        ...grade
    });
    return response.data;
};

export const getAssignmentAIFeedback = async (
    assignmentId: number,
    submissionId: number
): Promise<AssignmentAIFeedback> => {
    const response = await api.post<AssignmentAIFeedback>(`/assignments/${assignmentId}/ai-feedback`, {
        submission_id: submissionId
    });
    return response.data;
};

// 植物档案 API
export const getPlants = async (params?: any): Promise<any[]> => {
    const response = await api.get('/plants', { params });
    return response.data;
};

export const createPlant = async (plant: any): Promise<any> => {
    const response = await api.post('/plants', plant);
    return response.data;
};

export const uploadPlantImage = async (file: File): Promise<{ url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/plants/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const getPlantRecords = async (plantId: number): Promise<any[]> => {
    const response = await api.get(`/plants/${plantId}/records`);
    return response.data;
};

export const createPlantRecord = async (plantId: number, record: any): Promise<any> => {
    const response = await api.post(`/plants/${plantId}/records`, record);
    return response.data;
};

export const migratePlant = async (
    plantId: number,
    payload: { target_class_id: number; target_group_id?: number | null; target_device_id?: number | null }
): Promise<any> => {
    const response = await api.post(`/admin/plants/${plantId}/migrate`, payload);
    return response.data;
};

// 小组 API
export const getGroups = async (params?: any): Promise<any[]> => {
    const response = await api.get('/groups', { params });
    return response.data;
};

export const getGroupDetail = async (groupId: number): Promise<any> => {
    const response = await api.get(`/groups/${groupId}`);
    return response.data;
};

export const createGroup = async (group: any): Promise<any> => {
    const response = await api.post('/groups', group);
    return response.data;
};

export const updateGroup = async (groupId: number, group: any): Promise<any> => {
    const response = await api.put(`/groups/${groupId}`, group);
    return response.data;
};

export const deleteGroup = async (groupId: number): Promise<void> => {
    await api.delete(`/groups/${groupId}`);
};

export const addGroupMember = async (groupId: number, member: any): Promise<any> => {
    const response = await api.post(`/groups/${groupId}/members`, member);
    return response.data;
};

export const updateGroupMemberRole = async (memberId: number, role: string): Promise<any> => {
    const response = await api.put(`/groups/members/${memberId}`, { role });
    return response.data;
};

export const removeGroupMember = async (memberId: number): Promise<void> => {
    await api.delete(`/groups/members/${memberId}`);
};

export const migrateGroup = async (
    groupId: number,
    payload: { target_class_id: number; target_device_id?: number | null }
): Promise<any> => {
    const response = await api.post(`/admin/groups/${groupId}/migrate`, payload);
    return response.data;
};

export const batchUpdateGroupMemberRoles = async (
    groupId: number,
    updates: Array<{ member_id: number; role: string }>
): Promise<{ updated: number; group_id: number }> => {
    const response = await api.post(`/admin/groups/${groupId}/members/batch-role`, { updates });
    return response.data;
};

export const getMyProfile = async (): Promise<UserProfile> => {
    const response = await api.get('/profile/me');
    return response.data;
};

export const updateMyProfile = async (payload: { real_name: string }): Promise<UserProfile> => {
    const response = await api.patch('/profile/me', payload);
    return response.data;
};

export const uploadProfileAvatar = async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/profile/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const getNotifications = async (params?: { page?: number; page_size?: number }): Promise<{ items: NotificationItem[]; total: number; page: number; page_size: number }> => {
    const response = await api.get('/notifications', { params });
    return response.data;
};

export const getNotificationUnreadCount = async (): Promise<{ unread_count: number }> => {
    const response = await api.get('/notifications/unread-count');
    return response.data;
};

export const markNotificationRead = async (notificationId: number): Promise<{ message: string }> => {
    const response = await api.post(`/notifications/${notificationId}/read`);
    return response.data;
};

export const markAllNotificationsRead = async (): Promise<{ message: string; updated: number }> => {
    const response = await api.post('/notifications/read-all');
    return response.data;
};

export const getOperationLogs = async (params?: {
    operation_type?: string;
    operator_id?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
}): Promise<OperationLogsResponse> => {
    const response = await api.get('/logs/operations', { params });
    return response.data;
};

export const exportOperationLogs = async (params?: {
    start_date?: string;
    end_date?: string;
}): Promise<{ blob: Blob; filename: string | null }> => {
    const response = await api.post('/logs/operations/export', null, {
        params,
        responseType: 'blob',
    });

    const contentDisposition = response.headers['content-disposition'] as string | undefined;
    let filename: string | null = null;
    if (contentDisposition) {
        const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
        const plainMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
        const rawName = utf8Match?.[1] || plainMatch?.[1];
        if (rawName) {
            try {
                filename = decodeURIComponent(rawName);
            } catch {
                filename = rawName;
            }
        }
    }

    return { blob: response.data, filename };
};

export default api;
