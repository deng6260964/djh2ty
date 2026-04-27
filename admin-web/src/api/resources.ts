import client from './client'
import type { Resource } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface ResourceListParams {
  page?: number
  page_size?: number
  subject?: string
  grade?: string
  resource_type?: string
}

export const resourcesApi = {
  list: async (params?: ResourceListParams): Promise<PaginatedResponse<Resource>> => {
    const response = await client.get<PaginatedResponse<Resource>>('/api/resources', { params })
    return response.data
  },

  get: async (id: number): Promise<Resource> => {
    const response = await client.get<Resource>(`/api/resources/${id}`)
    return response.data
  },

  upload: async (
    formData: FormData,
    onUploadProgress?: (progressEvent: { loaded: number; total?: number }) => void
  ): Promise<Resource> => {
    const response = await client.post<Resource>('/api/resources/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    })
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/resources/${id}`)
  },

  share: async (id: number, studentIds: number[]): Promise<void> => {
    await client.post(`/api/resources/${id}/share`, { student_ids: studentIds })
  },

  unshare: async (id: number, studentId: number): Promise<void> => {
    await client.delete(`/api/resources/${id}/share/${studentId}`)
  },

  getDownloadUrl: (id: number): string => {
    return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/resources/${id}/download`
  },
}
