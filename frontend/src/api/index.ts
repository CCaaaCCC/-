import axios from 'axios';
import router from '../router';

// Create axios instance with base URL pointing to the backend
const api = axios.create({
    baseURL: 'http://localhost:8000/api',
    timeout: 10000
});

// Separate axios instance for auth endpoints (not under /api)
const authApi = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 10000
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
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
    if (error.response && error.response.status === 401) {
      // Clear local storage and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      localStorage.removeItem('username');
      router.push('/login');
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
    light_state: number;
}

export interface ControlRequest {
    pump_state?: number;
    fan_state?: number;
    light_state?: number;
}

export interface DeviceCreateRequest {
    device_name: string;
    status?: number;
    pump_state?: number;
    fan_state?: number;
    light_state?: number;
}

export interface Assignment {
    id: number;
    title: string;
    description?: string;
    class_id?: number;
    class_name?: string;
    device_id?: number;
    device_name?: string;
    due_date?: string;
    created_at: string;
    submission_count: number;
    requirement?: string;
    is_published: boolean;
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
        light_state: number;
    };
}

export interface AIScienceAskRequest {
    question: string;
    device_id?: number;
}

export interface AIScienceAskResponse {
    answer: string;
    source: 'qwen' | 'rule-based' | string;
}

export type DemoScenario = 'drought' | 'heatwave' | 'low_light' | 'healthy';

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

export const triggerDemoScenario = async (deviceId: number, scenario: DemoScenario): Promise<{ status: string; scenario: string; message: string }> => {
    const response = await api.post(`/demo/scenario/${deviceId}`, { scenario });
    return response.data;
};

export const createTelemetrySocket = (
    deviceId: number,
    onMessage: (payload: TelemetryRealtimePayload) => void,
    onClose?: () => void
): WebSocket => {
    const token = localStorage.getItem('token') || '';
    const apiBase = (api.defaults.baseURL || '').replace(/\/api\/?$/, '');
    const backendUrl = apiBase || `${window.location.protocol}//${window.location.hostname}:8000`;
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
export const getCategories = async (): Promise<any[]> => {
    const response = await api.get('/content/categories');
    return response.data;
};

export const createCategory = async (category: any): Promise<any> => {
    const response = await api.post('/content/categories', category);
    return response.data;
};

export const getCategoriesTree = async (): Promise<any[]> => {
    const response = await api.get('/content/categories/tree');
    return response.data;
};

export const updateCategory = async (id: number, category: any): Promise<any> => {
    const response = await api.put(`/content/categories/${id}`, category);
    return response.data;
};

export const deleteCategory = async (id: number): Promise<any> => {
    const response = await api.delete(`/content/categories/${id}`);
    return response.data;
};

export const getContents = async (params?: {
    category_id?: number;
    content_type?: string;
    is_published?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
}): Promise<{ items: any[]; total: number; page: number; page_size: number }> => {
    const response = await api.get('/content/contents', { params });
    return response.data;
};

export const getContent = async (id: number): Promise<any> => {
    const response = await api.get(`/content/contents/${id}`);
    return response.data;
};

export const createContent = async (content: any): Promise<any> => {
    const response = await api.post('/content/contents', content);
    return response.data;
};

export const updateContent = async (id: number, content: any): Promise<any> => {
    const response = await api.put(`/content/contents/${id}`, content);
    return response.data;
};

export const deleteContent = async (id: number): Promise<void> => {
    await api.delete(`/content/contents/${id}`);
};

export const publishContent = async (id: number): Promise<any> => {
    const response = await api.post(`/content/contents/${id}/publish`);
    return response.data;
};

export const getMyLearning = async (): Promise<any[]> => {
    const response = await api.get('/content/my-learning');
    return response.data;
};

export const startLearning = async (contentId: number): Promise<any> => {
    const response = await api.post(`/content/contents/${contentId}/start`);
    return response.data;
};

export const completeLearning = async (contentId: number): Promise<any> => {
    const response = await api.post(`/content/contents/${contentId}/complete`);
    return response.data;
};

export const getComments = async (contentId: number): Promise<any[]> => {
    const response = await api.get(`/content/contents/${contentId}/comments`);
    return response.data;
};

export const addComment = async (contentId: number, comment: string): Promise<any> => {
    const response = await api.post(`/content/contents/${contentId}/comments`, { comment });
    return response.data;
};

export const replyComment = async (commentId: number, comment: string): Promise<any> => {
    const response = await api.post(`/content/comments/${commentId}/reply`, { comment });
    return response.data;
};

export const toggleCommentLike = async (commentId: number): Promise<{ comment_id: number; liked: boolean; like_count: number }> => {
    const response = await api.post(`/content/comments/${commentId}/like`);
    return response.data;
};

export const getLearningStats = async (): Promise<any> => {
    const response = await api.get('/content/stats/overview');
    return response.data;
};

export const getStudentsProgress = async (): Promise<any[]> => {
    const response = await api.get('/content/stats/students');
    return response.data;
};

// 实验报告 API
export const getAssignments = async (params?: any): Promise<any[]> => {
    const response = await api.get('/assignments', { params });
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

export default api;
