import client from './client'
import type { Grade, GradeFormData, GradeTrendData, KnowledgePoint } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface GradeListParams {
  page?: number
  page_size?: number
  student_id?: number
  subject?: string
}

export const progressApi = {
  listGrades: async (params?: GradeListParams): Promise<PaginatedResponse<Grade>> => {
    const response = await client.get<PaginatedResponse<Grade>>('/api/progress/grades', { params })
    return response.data
  },

  createGrade: async (data: GradeFormData): Promise<Grade> => {
    const response = await client.post<Grade>('/api/progress/grades', data)
    return response.data
  },

  updateGrade: async (id: number, data: GradeFormData): Promise<Grade> => {
    const response = await client.put<Grade>(`/api/progress/grades/${id}`, data)
    return response.data
  },

  deleteGrade: async (id: number): Promise<void> => {
    await client.delete(`/api/progress/grades/${id}`)
  },

  getGradeTrend: async (studentId: number, subject?: string): Promise<GradeTrendData> => {
    const response = await client.get<GradeTrendData>('/api/progress/grades/trend', {
      params: { student_id: studentId, subject },
    })
    return response.data
  },

  listKnowledgePoints: async (params?: {
    student_id?: number
    subject?: string
    status?: string
  }): Promise<KnowledgePoint[]> => {
    const response = await client.get<KnowledgePoint[]>('/api/progress/knowledge-points', { params })
    return response.data
  },

  upsertKnowledgePoint: async (data: Omit<KnowledgePoint, 'id'>): Promise<KnowledgePoint> => {
    const response = await client.post<KnowledgePoint>('/api/progress/knowledge-points', data)
    return response.data
  },

  getReport: async (studentId: number): Promise<unknown> => {
    const response = await client.get(`/api/progress/report/${studentId}`)
    return response.data
  },
}
