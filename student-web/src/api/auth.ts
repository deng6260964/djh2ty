import client from './client'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: number
    username?: string
    role: string
    display_name: string
    student_id?: number
  }
}

export interface UserInfo {
  id: number
  username?: string
  role: string
  display_name: string
  avatar_url?: string
  is_active: boolean
}

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await client.post<LoginResponse>('/api/auth/login', data)
    return response.data
  },

  getMe: async (): Promise<UserInfo> => {
    const response = await client.get<UserInfo>('/api/auth/me')
    return response.data
  },
}
