import client from './client'
import type { LoginRequest, LoginResponse } from '../types/api'

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await client.post<LoginResponse>('/api/auth/login', data)
    return response.data
  },

  refresh: async (): Promise<{ access_token: string; expires_in: number }> => {
    const response = await client.post('/api/auth/refresh')
    return response.data
  },

  logout: async (): Promise<void> => {
    // 无需后端接口，清空本地 token 即可
  },
}
