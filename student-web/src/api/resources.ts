import client from './client'
import { getToken } from './client'
import type { PaginatedResponse } from '../types/api'
import type { SharedResource } from '../types/models'

export const resourcesApi = {
  getShared: async (params?: { subject?: string; page?: number; page_size?: number }): Promise<PaginatedResponse<SharedResource>> => {
    const response = await client.get<PaginatedResponse<SharedResource>>('/api/resources/shared', { params })
    return response.data
  },

  download: async (id: number, fileName: string): Promise<void> => {
    const token = getToken()
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const response = await fetch(`${baseUrl}/api/resources/${id}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      throw new Error('下载失败')
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}
