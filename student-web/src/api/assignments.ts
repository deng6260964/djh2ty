import client from './client'
import type { PaginatedResponse } from '../types/api'
import type { MyAssignment, MyAssignmentDetail } from '../types/models'

export interface MyAssignmentsParams {
  status?: string
  page?: number
  page_size?: number
}

export const assignmentsApi = {
  getMyAssignments: async (params?: MyAssignmentsParams): Promise<PaginatedResponse<MyAssignment>> => {
    const response = await client.get<PaginatedResponse<MyAssignment>>('/api/assignments/my', { params })
    return response.data
  },

  getDetail: async (id: number): Promise<MyAssignmentDetail> => {
    const response = await client.get<MyAssignmentDetail>(`/api/assignments/${id}/my`)
    return response.data
  },
}
