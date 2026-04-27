import client from './client'
import type { PaginatedResponse } from '../types/api'
import type { Course } from '../types/models'

export interface MyCoursesParams {
  page?: number
  page_size?: number
  status?: string
  start_date?: string
  end_date?: string
}

export const coursesApi = {
  getMyCourses: async (params?: MyCoursesParams): Promise<PaginatedResponse<Course>> => {
    const response = await client.get<PaginatedResponse<Course>>('/api/courses/my', { params })
    return response.data
  },
}
