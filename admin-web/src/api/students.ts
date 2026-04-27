import client from './client'
import type { Student, StudentAccount, StudentFormData } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface StudentListParams {
  page?: number
  page_size?: number
  search?: string
  subject?: string
  grade?: string
  is_active?: boolean
}

export const studentsApi = {
  list: async (params?: StudentListParams): Promise<PaginatedResponse<Student>> => {
    const response = await client.get<PaginatedResponse<Student>>('/api/students', { params })
    return response.data
  },

  get: async (id: number): Promise<Student> => {
    const response = await client.get<Student>(`/api/students/${id}`)
    return response.data
  },

  create: async (data: StudentFormData): Promise<Student> => {
    const response = await client.post<Student>('/api/students', data)
    return response.data
  },

  update: async (id: number, data: StudentFormData): Promise<Student> => {
    const response = await client.put<Student>(`/api/students/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/students/${id}`)
  },

  getCourses: async (id: number, params?: { status?: string; page?: number; page_size?: number }) => {
    const response = await client.get(`/api/students/${id}/courses`, { params })
    return response.data
  },

  getAssignments: async (id: number, params?: { page?: number; page_size?: number }) => {
    const response = await client.get(`/api/students/${id}/assignments`, { params })
    return response.data
  },

  getBillingSummary: async (id: number) => {
    const response = await client.get(`/api/students/${id}/billing-summary`)
    return response.data
  },

  getAccount: async (id: number): Promise<StudentAccount> => {
    const response = await client.get<StudentAccount>(`/api/billing/students/${id}/account`)
    return response.data
  },
}
