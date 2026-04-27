import client from './client'
import type { Assignment, AssignmentDetail, AssignmentFormData, GradeRequest } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface AssignmentListParams {
  page?: number
  page_size?: number
  subject?: string
  status?: string
  student_id?: number
}

export const assignmentsApi = {
  list: async (params?: AssignmentListParams): Promise<PaginatedResponse<Assignment>> => {
    const response = await client.get<PaginatedResponse<Assignment>>('/api/assignments', { params })
    return response.data
  },

  get: async (id: number): Promise<AssignmentDetail> => {
    const response = await client.get<AssignmentDetail>(`/api/assignments/${id}`)
    return response.data
  },

  create: async (data: AssignmentFormData): Promise<Assignment> => {
    const response = await client.post<Assignment>('/api/assignments', data)
    return response.data
  },

  update: async (id: number, data: AssignmentFormData): Promise<Assignment> => {
    const response = await client.put<Assignment>(`/api/assignments/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/assignments/${id}`)
  },

  grade: async (id: number, data: GradeRequest): Promise<void> => {
    await client.post(`/api/assignments/${id}/grade`, data)
  },
}
