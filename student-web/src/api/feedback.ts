import client from './client'
import type { PaginatedResponse } from '../types/api'
import type { MyFeedback } from '../types/models'

export const feedbackApi = {
  getMyFeedback: async (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<MyFeedback>> => {
    const response = await client.get<PaginatedResponse<MyFeedback>>('/api/feedback/my', { params })
    return response.data
  },

  getDetail: async (id: number): Promise<MyFeedback> => {
    const response = await client.get<MyFeedback>(`/api/feedback/my/${id}`)
    return response.data
  },
}
