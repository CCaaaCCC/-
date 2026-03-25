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

// 用户管理 API
export const getUsers = async (params?: {
    role?: string;
    class_id?: number;
    is_active?: boolean;
    search?: string;
}): Promise<any[]> => {
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
    const response = await api.get('/users/export', {
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

export const getContents = async (params?: any): Promise<any[]> => {
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

export const createGroup = async (group: any): Promise<any> => {
    const response = await api.post('/groups', group);
    return response.data;
};

export const addGroupMember = async (groupId: number, member: any): Promise<any> => {
    const response = await api.post(`/groups/${groupId}/members`, member);
    return response.data;
};

export const removeGroupMember = async (memberId: number): Promise<void> => {
    await api.delete(`/groups/members/${memberId}`);
};

export default api;
