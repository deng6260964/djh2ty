export interface User {
  id: string
  email: string
  name: string
  role: "student" | "teacher" | "admin"
  avatar?: string
  phone?: string
  createdAt: string
  updatedAt: string
  isActive: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
  role: "student" | "teacher"
  phone?: string
}

export interface AuthResponse {
  user: User
  token: string
  refreshToken?: string
}
