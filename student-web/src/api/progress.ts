import client from './client'
import type { KnowledgePoint } from '../types/models'

export interface MyProgressResponse {
  student_name: string
  recent_grades: Array<{
    id: number
    subject: string
    exam_type: string
    exam_name: string
    score: number
    full_score: number
    percentage: number
    exam_date: string
  }>
  knowledge_points: {
    mastered: number
    learning: number
    todo: number
  }
}

export interface GradeTrendResponse {
  student_name: string
  subject: string
  data: Array<{
    exam_date: string
    score: number
    full_score: number
    percentage: number
    exam_type: string
    exam_name: string
  }>
}

export const progressApi = {
  getMyProgress: async (): Promise<MyProgressResponse> => {
    const response = await client.get<MyProgressResponse>('/api/progress/my')
    return response.data
  },

  getGradeTrend: async (subject: string): Promise<GradeTrendResponse> => {
    const response = await client.get<GradeTrendResponse>('/api/progress/my/grades/trend', {
      params: { subject }
    })
    return response.data
  },

  getKnowledgePoints: async (subject?: string): Promise<KnowledgePoint[]> => {
    const response = await client.get<KnowledgePoint[]>('/api/progress/my/knowledge-points', {
      params: { subject }
    })
    return response.data
  },
}
