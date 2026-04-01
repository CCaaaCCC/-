import api from './index';

// ================= 类型定义 =================
export interface User {
    id: number;
    username: string;
    role: 'student' | 'teacher' | 'admin';
    email?: string;
    real_name?: string;
    student_id?: string;
    teacher_id?: string;
    class_id?: number;
    class_name?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface UserCreate {
    username: string;
    password: string;
    role: 'student' | 'teacher' | 'admin';
    email?: string;
    real_name?: string;
    student_id?: string;
    teacher_id?: string;
    class_id?: number;
    is_active?: boolean;
}

export interface UserUpdate {
    email?: string;
    real_name?: string;
    student_id?: string;
    teacher_id?: string;
    class_id?: number;
    is_active?: boolean;
    role?: string;
}

export interface Class {
    id: number;
    class_name: string;
    grade?: string;
    description?: string;
    teacher_id?: number;
    teacher_name?: string;
    student_count: number;
    is_active: boolean;
    created_at: string;
}

export interface UserStats {
    total_users: number;
    admin_count: number;
    teacher_count: number;
    student_count: number;
    active_count: number;
    inactive_count: number;
}

export interface ImportResult {
    success_count: number;
    error_rows: any[];
    message: string;
}

export interface UsersListResponse {
    items: User[];
    total: number;
    page: number;
    page_size: number;
}

// ================= 用户管理 API =================
export const getUsers = async (params?: {
    role?: string;
    class_id?: number;
    is_active?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
}): Promise<UsersListResponse> => {
    const response = await api.get('/users', { params });
    return response.data;
};

export const getUser = async (id: number): Promise<User> => {
    const response = await api.get(`/users/${id}`);
    return response.data;
};

export const createUser = async (user: UserCreate): Promise<User> => {
    const response = await api.post('/users', user);
    return response.data;
};

export const updateUser = async (id: number, user: UserUpdate): Promise<User> => {
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

export const getUserStats = async (): Promise<UserStats> => {
    const response = await api.get('/stats/users');
    return response.data;
};

export const batchCreateUsers = async (users: UserCreate[]): Promise<ImportResult> => {
    const response = await api.post('/users/batch-create', users);
    return response.data;
};

export const importUsers = async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/users/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const exportUsers = async (): Promise<{ blob: Blob; filename: string | null }> => {
    const response = await api.get('/users-export', {
        responseType: 'blob',
        timeout: 60000
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

// ================= 批量操作 API =================
export const batchDeleteUsers = async (userIds: number[]): Promise<{
    message: string;
    deleted_count: number;
    failed_users: any[];
}> => {
    const response = await api.post('/users/batch-delete', { user_ids: userIds });
    return response.data;
};

export const batchUpdateClass = async (userIds: number[], classId: number | null): Promise<{
    message: string;
    updated_count: number;
}> => {
    const response = await api.post('/users/batch-update-class', { 
        user_ids: userIds, 
        class_id: classId 
    });
    return response.data;
};

export const batchResetPassword = async (userIds: number[], newPassword: string): Promise<{
    message: string;
    reset_count: number;
    failed_users: any[];
}> => {
    const response = await api.post('/users/batch-reset-password', { 
        user_ids: userIds, 
        new_password: newPassword 
    });
    return response.data;
};

// ================= 班级管理 API =================
export const getClasses = async (params?: {
    grade?: string;
    is_active?: boolean;
}): Promise<Class[]> => {
    const response = await api.get('/classes', { params });
    return response.data;
};

export const createClass = async (cls: {
    class_name: string;
    grade?: string;
    description?: string;
    teacher_id?: number;
}): Promise<Class> => {
    const response = await api.post('/classes', cls);
    return response.data;
};

export const updateClass = async (id: number, cls: {
    class_name?: string;
    grade?: string;
    description?: string;
    teacher_id?: number;
    is_active?: boolean;
}): Promise<Class> => {
    const response = await api.put(`/classes/${id}`, cls);
    return response.data;
};

export const deleteClass = async (id: number): Promise<void> => {
    await api.delete(`/classes/${id}`);
};

export const getClassStudents = async (classId: number): Promise<User[]> => {
    const response = await api.get(`/classes/${classId}/students`);
    return response.data;
};
