import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Token 存储键
const TOKEN_KEY = 'access_token'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

// 创建 axios 实例
const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 是否正在刷新 token
let isRefreshing = false
// 等待刷新的请求队列
let refreshSubscribers: Array<(token: string) => void> = []

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

const addRefreshSubscriber = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb)
}

// 请求拦截器：自动添加 Authorization header
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => {
    // 检查 token 剩余天数，不足 1 天时自动刷新
    const remainingDays = response.headers['x-token-remaining-days']
    if (remainingDays && parseInt(remainingDays) < 1) {
      refreshToken()
    }
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401) {
      if (!originalRequest._retry) {
        if (isRefreshing) {
          // 等待 token 刷新完成
          return new Promise((resolve) => {
            addRefreshSubscriber((token: string) => {
              originalRequest.headers['Authorization'] = `Bearer ${token}`
              resolve(client(originalRequest))
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const newToken = await refreshToken()
          if (newToken) {
            onRefreshed(newToken)
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            return client(originalRequest)
          }
        } catch {
          // Token 刷新失败，跳转登录
        } finally {
          isRefreshing = false
        }

        // 跳转登录页
        removeToken()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    if (error.response?.status === 500) {
      message.error('服务器繁忙，请稍后重试')
    } else if (error.response?.status === 403) {
      message.error('权限不足，无法执行此操作')
    } else if (!error.response) {
      message.error('网络异常，请检查网络后重试')
    }

    return Promise.reject(error)
  }
)

// 刷新 token
export const refreshToken = async (): Promise<string | null> => {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/auth/refresh`,
      {},
      {
        headers: {
          Authorization: `Bearer ${getToken()}`,
        },
      }
    )
    const newToken = response.data.access_token
    setToken(newToken)
    return newToken
  } catch {
    removeToken()
    return null
  }
}

export default client
