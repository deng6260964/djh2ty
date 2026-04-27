import client from './client'
import type { Feedback, FeedbackFormData, FeedbackTemplate } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface FeedbackListParams {
  page?: number
  page_size?: number
  student_id?: number
  is_pushed?: boolean
}

export const feedbackApi = {
  list: async (params?: FeedbackListParams): Promise<PaginatedResponse<Feedback>> => {
    const response = await client.get<PaginatedResponse<Feedback>>('/api/feedback', { params })
    return response.data
  },

  get: async (id: number): Promise<Feedback> => {
    const response = await client.get<Feedback>(`/api/feedback/${id}`)
    return response.data
  },

  create: async (data: FeedbackFormData): Promise<Feedback> => {
    const response = await client.post<Feedback>('/api/feedback', data)
    return response.data
  },

  update: async (id: number, data: FeedbackFormData): Promise<Feedback> => {
    const response = await client.put<Feedback>(`/api/feedback/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/feedback/${id}`)
  },

  push: async (id: number): Promise<{ pushed: boolean; pushed_to: string[]; pushed_at: string }> => {
    const response = await client.post(`/api/feedback/${id}/push`)
    return response.data
  },

  getTemplates: async (): Promise<FeedbackTemplate[]> => {
    const response = await client.get<FeedbackTemplate[]>('/api/feedback/templates')
    return response.data
  },

  createTemplate: async (data: Omit<FeedbackTemplate, 'id'>): Promise<FeedbackTemplate> => {
    const response = await client.post<FeedbackTemplate>('/api/feedback/templates', data)
    return response.data
  },

  deleteTemplate: async (id: number): Promise<void> => {
    await client.delete(`/api/feedback/templates/${id}`)
  },
}
