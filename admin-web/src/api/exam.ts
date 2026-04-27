import client from './client'
import type { PaginatedResponse } from '../types/api'

export interface ExamQuestion {
  id: number
  subject: string
  year: number
  question_type: string
  content: string
  options?: Record<string, string>
  answer: string
  explanation?: string
  difficulty: number
  tags: string[]
}

export interface VocabularyItem {
  id: number
  word: string
  phonetic?: string
  meaning: string
  example?: string
  level: string
}

export const examApi = {
  listQuestions: async (params?: {
    subject?: string
    year?: number
    question_type?: string
    difficulty?: number
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<ExamQuestion>> => {
    const response = await client.get<PaginatedResponse<ExamQuestion>>('/api/exam/questions', { params })
    return response.data
  },

  createQuestion: async (data: Omit<ExamQuestion, 'id'>): Promise<ExamQuestion> => {
    const response = await client.post<ExamQuestion>('/api/exam/questions', data)
    return response.data
  },

  listVocabulary: async (params?: {
    level?: string
    search?: string
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<VocabularyItem>> => {
    const response = await client.get<PaginatedResponse<VocabularyItem>>('/api/exam/vocabulary', { params })
    return response.data
  },
}
