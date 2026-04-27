import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const TOKEN_KEY = 'student_access_token'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

const addRefreshSubscriber = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb)
}

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

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401) {
      if (!originalRequest._retry) {
        if (isRefreshing) {
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
          // Token refresh failed
        } finally {
          isRefreshing = false
        }

        removeToken()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    if (error.response?.status === 500) {
      message.error('服务器繁忙，请稍后重试')
    } else if (error.response?.status === 403) {
      message.error('权限不足')
    } else if (!error.response) {
      message.error('网络异常，请检查网络')
    }

    return Promise.reject(error)
  }
)

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
