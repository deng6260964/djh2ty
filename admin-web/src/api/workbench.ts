import client from './client'
import type { WorkbenchResponse } from '../types/api'

export const workbenchApi = {
  get: async (): Promise<WorkbenchResponse> => {
    const response = await client.get<WorkbenchResponse>('/api/dashboard/workbench')
    return response.data
  },
}
