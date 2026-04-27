import client from './client'
import type { SubjectPrice, BillingRecord, PaymentRequest, BillingSummary, OutstandingStudent } from '../types/models'
import type { PaginatedResponse } from '../types/api'

export interface BillingListParams {
  page?: number
  page_size?: number
  student_id?: number
  status?: string
  start_date?: string
  end_date?: string
}

export const billingApi = {
  listSubjectPrices: async (): Promise<SubjectPrice[]> => {
    const response = await client.get<SubjectPrice[]>('/api/billing/subject-prices')
    return response.data
  },

  updateSubjectPrice: async (subject: string, pricePerHour: number): Promise<SubjectPrice> => {
    const response = await client.put<SubjectPrice>(`/api/billing/subject-prices/${subject}`, {
      price_per_hour: pricePerHour,
    })
    return response.data
  },

  createSubjectPrice: async (data: Omit<SubjectPrice, 'id'>): Promise<SubjectPrice> => {
    const response = await client.post<SubjectPrice>('/api/billing/subject-prices', data)
    return response.data
  },

  deleteSubjectPrice: async (id: number): Promise<void> => {
    await client.delete(`/api/billing/subject-prices/${id}`)
  },

  listRecords: async (params?: BillingListParams): Promise<PaginatedResponse<BillingRecord>> => {
    const response = await client.get<PaginatedResponse<BillingRecord>>('/api/billing/records', { params })
    return response.data
  },

  createRecord: async (data: {
    student_id: number
    amount: number
    notes?: string
  }): Promise<BillingRecord> => {
    const response = await client.post<BillingRecord>('/api/billing/records', data)
    return response.data
  },

  recordPayment: async (id: number, data: PaymentRequest): Promise<BillingRecord> => {
    const response = await client.patch<BillingRecord>(`/api/billing/records/${id}/pay`, data)
    return response.data
  },

  recharge: async (data: {
    student_id: number
    paid_amount: number
    payment_method: string
    paid_at: string
    notes?: string
  }): Promise<BillingRecord> => {
    const response = await client.post<BillingRecord>('/api/billing/recharge', data)
    return response.data
  },

  getSummary: async (startDate: string, endDate: string): Promise<BillingSummary> => {
    const response = await client.get<BillingSummary>('/api/billing/summary', {
      params: { start_date: startDate, end_date: endDate },
    })
    return response.data
  },

  getOutstanding: async (): Promise<OutstandingStudent[]> => {
    const response = await client.get<OutstandingStudent[]>('/api/billing/outstanding')
    return response.data
  },
}
