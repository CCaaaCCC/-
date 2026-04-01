// 从 index.ts 导入 API 函数
export {
    getCategories,
    createCategory,
    getContents,
    getContent,
    createContent,
    updateContent,
    deleteContent,
    publishContent,
    getMyLearning,
    startLearning,
    completeLearning,
    getComments,
    addComment,
    replyComment,
    toggleCommentLike,
    getLearningStats,
    getStudentsProgress,
    getAssignments,
    createAssignment,
    getSubmissions,
    getMySubmission,
    submitAssignment,
    gradeAssignment,
    getPlants,
    createPlant,
    getPlantRecords,
    createPlantRecord,
    getGroups,
    createGroup,
    addGroupMember,
    removeGroupMember,
    getClasses,
    getDevices
} from './index';

// ================= 类型定义 =================
export interface Assignment {
    id: number;
    title: string;
    description?: string;
    device_id?: number;
    class_id?: number;
    teacher_id: number;
    teacher_name?: string;
    device_name?: string;
    class_name?: string;
    start_date?: string;
    due_date?: string;
    requirement?: string;
    template?: string;
    is_published: boolean;
    created_at: string;
    submission_count: number;
}

export interface AssignmentSubmission {
    id: number;
    assignment_id: number;
    student_id: number;
    student_name?: string;
    status: 'draft' | 'submitted' | 'graded';
    experiment_date?: string;
    observations?: string;
    conclusion?: string;
    temp_records?: string;
    humidity_records?: string;
    soil_moisture_records?: string;
    light_records?: string;
    photos?: string;
    score?: number;
    teacher_comment?: string;
    graded_at?: string;
    submitted_at?: string;
    created_at: string;
    updated_at: string;
}

export interface PlantProfile {
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
    status: 'growing' | 'harvested' | 'withered';
    expected_harvest_date?: string;
    description?: string;
    growth_record_count: number;
    created_at: string;
}

export interface GrowthRecord {
    id: number;
    plant_id: number;
    record_date: string;
    stage?: string;
    height_cm?: number;
    leaf_count?: number;
    flower_count?: number;
    fruit_count?: number;
    description?: string;
    photos?: string;
    recorder_name?: string;
    created_at: string;
}

export interface StudyGroup {
    id: number;
    group_name: string;
    class_id: number;
    class_name?: string;
    device_id?: number;
    device_name?: string;
    description?: string;
    member_count: number;
    members: Array<{
        id: number;
        student_id: number;
        student_name?: string;
        role: string;
    }>;
    created_at: string;
}
