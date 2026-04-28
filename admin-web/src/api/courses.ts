import client from './client'
import type {
  Course,
  CourseFormData,
  ConflictCheckRequest,
  ConflictCheckResponse,
  CalendarData,
  WeekCoursesResponse,
  CopyWeekPreviewRequest,
  CopyWeekPreviewResponse,
  CopyWeekConfirmResponse,
  CourseCompleteFormData,
  CourseCompleteResponse,
  CourseDetailV2,
  MakeupPoolResponse,
} from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface CourseListParams {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  student_id?: number
  status?: string
}

export const coursesApi = {
  list: async (params?: CourseListParams): Promise<PaginatedResponse<Course>> => {
    const response = await client.get<PaginatedResponse<Course>>('/api/courses', { params })
    return response.data
  },

  get: async (id: number): Promise<Course> => {
    const response = await client.get<Course>(`/api/courses/${id}`)
    return response.data
  },

  create: async (data: CourseFormData): Promise<Course> => {
    const response = await client.post<Course>('/api/courses', data)
    return response.data
  },

  update: async (id: number, data: CourseFormData): Promise<Course> => {
    const response = await client.put<Course>(`/api/courses/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await client.delete(`/api/courses/${id}`)
  },

  updateStatus: async (id: number, status: string): Promise<Course> => {
    const response = await client.patch<Course>(`/api/courses/${id}/status`, { status })
    return response.data
  },

  getDetailV2: async (id: number): Promise<CourseDetailV2> => {
    const response = await client.get<CourseDetailV2>(`/api/courses/${id}/detail-v2`)
    return response.data
  },

  complete: async (id: number, data: CourseCompleteFormData): Promise<CourseCompleteResponse> => {
    const response = await client.post<CourseCompleteResponse>(`/api/courses/${id}/complete`, data)
    return response.data
  },

  leave: async (id: number, data: { leave_type: 'student' | 'teacher'; reason?: string; turn_to_makeup: boolean }): Promise<Course> => {
    const response = await client.post<Course>(`/api/courses/${id}/leave`, data)
    return response.data
  },

  getMakeupPool: async (): Promise<MakeupPoolResponse> => {
    const response = await client.get<MakeupPoolResponse>('/api/courses/makeup-pool')
    return response.data
  },

  scheduleMakeup: async (id: number, data: { start_time: string; end_time: string; notes?: string }): Promise<Course> => {
    const response = await client.post<Course>(`/api/courses/${id}/makeup`, data)
    return response.data
  },

  checkConflict: async (data: ConflictCheckRequest): Promise<ConflictCheckResponse> => {
    const response = await client.post<ConflictCheckResponse>('/api/courses/check-conflict', data)
    return response.data
  },

  getCalendar: async (year: number, month: number): Promise<CalendarData> => {
    const response = await client.get<CalendarData>('/api/courses/calendar', {
      params: { year, month },
    })
    return response.data
  },

  getWeek: async (params: {
    week_start: string
    student_id?: number
    subject?: string
    status?: string
  }): Promise<WeekCoursesResponse> => {
    const response = await client.get<WeekCoursesResponse>('/api/courses/week', { params })
    return response.data
  },

  copyWeekPreview: async (data: CopyWeekPreviewRequest): Promise<CopyWeekPreviewResponse> => {
    const response = await client.post<CopyWeekPreviewResponse>('/api/courses/copy-week-preview', data)
    return response.data
  },

  copyWeekConfirm: async (data: CopyWeekPreviewRequest & {
    selected_course_ids: number[]
  }): Promise<CopyWeekConfirmResponse> => {
    const response = await client.post<CopyWeekConfirmResponse>('/api/courses/copy-week-confirm', data)
    return response.data
  },
}
