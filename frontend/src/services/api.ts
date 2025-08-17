import axios from "axios"
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios"
import type { LoginRequest, RegisterRequest, AuthResponse, User } from "../types/user"

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json"
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token过期，清除本地存储并跳转到登录页
      localStorage.removeItem("token")
      window.location.href = "/login"
    }
    
    const message = error.response?.data?.message || error.message || "请求失败"
    return Promise.reject(new Error(message))
  }
)

// 认证相关API
export const authApi = {
  login: (data: LoginRequest): Promise<AuthResponse> => {
    return apiClient.post("/auth/login", data)
  },
  
  register: (data: RegisterRequest): Promise<AuthResponse> => {
    return apiClient.post("/auth/register", data)
  },
  
  logout: (): Promise<void> => {
    return apiClient.post("/auth/logout")
  },
  
  getProfile: (): Promise<User> => {
    return apiClient.get("/auth/profile")
  },
  
  refreshToken: (): Promise<{ token: string }> => {
    return apiClient.post("/auth/refresh")
  }
}

// 课程相关API
export const courseApi = {
  getCourses: (params?: any) => {
    return apiClient.get("/courses", { params })
  },
  
  getCourse: (id: string) => {
    return apiClient.get(`/courses/${id}`)
  },
  
  createCourse: (data: any) => {
    return apiClient.post("/courses", data)
  },
  
  updateCourse: (id: string, data: any) => {
    return apiClient.put(`/courses/${id}`, data)
  },
  
  deleteCourse: (id: string) => {
    return apiClient.delete(`/courses/${id}`)
  }
}

// 作业相关API
export const assignmentApi = {
  getAssignments: (params?: any) => {
    return apiClient.get("/assignments", { params })
  },
  
  getAssignment: (id: string) => {
    return apiClient.get(`/assignments/${id}`)
  },
  
  createAssignment: (data: any) => {
    return apiClient.post("/assignments", data)
  },
  
  submitAssignment: (id: string, data: any) => {
    return apiClient.post(`/assignments/${id}/submit`, data)
  }
}

// 练习相关API
export const exerciseApi = {
  getExercises: (params?: any) => {
    return apiClient.get("/exercises", { params })
  },
  
  getExercise: (id: string) => {
    return apiClient.get(`/exercises/${id}`)
  },
  
  submitExercise: (id: string, data: any) => {
    return apiClient.post(`/exercises/${id}/submit`, data)
  }
}

export default apiClient
