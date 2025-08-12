import axios, { type AxiosInstance, type AxiosResponse } from 'axios'

// API响应接口
interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  code?: number
  errors?: Record<string, string[]>
}

// 用户信息接口
interface UserInfo {
  id: number
  phone: string
  name: string
  role: 'teacher' | 'student'
  avatar_url?: string
}

// 登录响应接口
interface LoginResponse {
  token: string
  user_info: UserInfo
}

// 注册请求接口
interface RegisterRequest {
  phone: string
  password: string
  name: string
  role: 'teacher' | 'student'
  invite_code?: string
}

// 登录请求接口
interface LoginRequest {
  phone: string
  password: string
}

class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: 'http://localhost:5000/api',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // 请求拦截器 - 添加token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器 - 处理错误
    this.api.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        return response
      },
      (error) => {
        if (error.response?.status === 401) {
          // token过期，清除本地存储并跳转到登录页
          localStorage.removeItem('token')
          localStorage.removeItem('user_info')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // 健康检查
  async healthCheck(): Promise<ApiResponse> {
    const response = await this.api.get('/health')
    return response.data
  }

  // 用户注册
  async register(data: RegisterRequest): Promise<ApiResponse<UserInfo>> {
    const response = await this.api.post('/auth/register', data)
    return response.data
  }

  // 用户登录
  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    const response = await this.api.post('/auth/login', data)
    if (response.data.success && response.data.data) {
      // 保存token和用户信息到本地存储
      localStorage.setItem('token', response.data.data.access_token)
      localStorage.setItem('user_info', JSON.stringify(response.data.data.user))
    }
    return response.data
  }

  // 获取用户信息
  async getProfile(): Promise<ApiResponse<UserInfo>> {
    const response = await this.api.get('/auth/profile')
    return response.data
  }

  // 退出登录
  logout(): void {
    localStorage.removeItem('token')
    localStorage.removeItem('user_info')
    window.location.href = '/login'
  }

  // 获取当前用户信息（从本地存储）
  getCurrentUser(): UserInfo | null {
    try {
      const userInfo = localStorage.getItem('user_info')
      return userInfo && userInfo !== 'undefined' ? JSON.parse(userInfo) : null
    } catch (error) {
      console.error('解析用户信息失败:', error)
      // 清除无效的用户信息
      localStorage.removeItem('user_info')
      localStorage.removeItem('token')
      return null
    }
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!localStorage.getItem('token')
  }

  // 课程相关API
  async getCourses(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/courses', { params })
    return response.data
  }

  async createCourse(data: any): Promise<ApiResponse> {
    const response = await this.api.post('/course-management', data)
    return response.data
  }

  async updateCourse(id: number, data: any): Promise<ApiResponse> {
    const response = await this.api.put(`/course-management/${id}`, data)
    return response.data
  }

  async deleteCourse(id: number): Promise<ApiResponse> {
    const response = await this.api.delete(`/course-management/${id}`)
    return response.data
  }

  // 课程管理API
  async getCourseManagement(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/course-management', { params })
    return response.data
  }

  async getCourseManagementById(id: number): Promise<ApiResponse> {
    const response = await this.api.get(`/course-management/${id}`)
    return response.data
  }

  // 题目相关API
  async getQuestions(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/questions', { params })
    return response.data
  }

  async getQuestion(id: number): Promise<ApiResponse> {
    const response = await this.api.get(`/questions/${id}`)
    return response.data
  }

  async createQuestion(data: any): Promise<ApiResponse> {
    const response = await this.api.post('/questions', data)
    return response.data
  }

  async updateQuestion(id: number, data: any): Promise<ApiResponse> {
    const response = await this.api.put(`/questions/${id}`, data)
    return response.data
  }

  async deleteQuestion(id: number): Promise<ApiResponse> {
    const response = await this.api.delete(`/questions/${id}`)
    return response.data
  }

  async autoGenerateQuestions(data: any): Promise<ApiResponse> {
    const response = await this.api.post('/questions/auto-generate', data)
    return response.data
  }

  // 作业相关API
  async getHomeworks(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/homework', { params })
    return response.data
  }

  async createHomework(data: any): Promise<ApiResponse> {
    const response = await this.api.post('/homework', data)
    return response.data
  }

  async deleteHomework(id: number): Promise<ApiResponse> {
    const response = await this.api.delete(`/homework/${id}`)
    return response.data
  }

  async getHomeworkSubmissions(homeworkId: number): Promise<ApiResponse> {
    const response = await this.api.get(`/homework/${homeworkId}/submissions`)
    return response.data
  }

  async gradeHomework(homeworkId: number, data: any): Promise<ApiResponse> {
    const response = await this.api.post(`/homework/${homeworkId}/grade`, data)
    return response.data
  }

  async submitHomework(homeworkId: number, data: any): Promise<ApiResponse> {
    const response = await this.api.post(`/homework/${homeworkId}/submit`, data)
    return response.data
  }

  // 考试相关API
  async getExams(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/exams', { params })
    return response.data
  }

  async createExam(data: any): Promise<ApiResponse> {
    const response = await this.api.post('/exams', data)
    return response.data
  }

  async updateExam(id: number, data: any): Promise<ApiResponse> {
    const response = await this.api.put(`/exams/${id}`, data)
    return response.data
  }

  async deleteExam(id: number): Promise<ApiResponse> {
    const response = await this.api.delete(`/exams/${id}`)
    return response.data
  }

  async getExamSubmissions(examId: number): Promise<ApiResponse> {
    const response = await this.api.get(`/exams/${examId}/submissions`)
    return response.data
  }

  async getExamDetails(id: number): Promise<ApiResponse> {
    const response = await this.api.get(`/exams/${id}`)
    return response.data
  }

  async submitExam(examId: number, data: any): Promise<ApiResponse> {
    const response = await this.api.post(`/exams/${examId}/submit`, data)
    return response.data
  }

  async getExamResults(examId: number): Promise<ApiResponse> {
    const response = await this.api.get(`/exams/${examId}/results`)
    return response.data
  }

  // 学生相关API
  async getStudents(params?: Record<string, any>): Promise<ApiResponse> {
    const response = await this.api.get('/students', { params })
    return response.data
  }

  async getStudentDetails(id: number): Promise<ApiResponse> {
    const response = await this.api.get(`/students/${id}`)
    return response.data
  }

  async getStudentProgress(id: number): Promise<ApiResponse> {
    const response = await this.api.get(`/students/${id}/progress`)
    return response.data
  }

  // 统计相关API
  async getTeachingStatistics(): Promise<ApiResponse> {
    const response = await this.api.get('/statistics/teaching')
    return response.data
  }

  // 文件上传API
  async uploadFile(file: File, type: string): Promise<ApiResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    
    const response = await this.api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}

// 导出单例实例
export const apiService = new ApiService()
export default apiService

// 导出类型
export type {
  ApiResponse,
  UserInfo,
  LoginResponse,
  RegisterRequest,
  LoginRequest
}