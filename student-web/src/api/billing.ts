import client from './client'

export interface AccountPaymentRecord {
  record_id: number
  amount: number
  paid_at?: string | null
  payment_method?: string | null
  notes?: string | null
}

export interface AccountChargeRecord {
  record_id: number
  course_id?: number | null
  subject?: string | null
  amount: number
  created_at: string
  notes?: string | null
}

export interface StudentAccount {
  student_id: number
  student_name: string
  grade: string
  current_balance: number
  total_received: number
  total_charged: number
  estimated_lessons_left: number
  main_subject?: string | null
  main_subject_hourly_rate?: number | null
  has_payment_alert: boolean
  next_course_id?: number | null
  next_course_time?: string | null
  next_course_subject?: string | null
  next_course_projected_charge?: number | null
  recent_payments: AccountPaymentRecord[]
  recent_charges: AccountChargeRecord[]
}

export const billingApi = {
  getMyAccount: async (): Promise<StudentAccount> => {
    const response = await client.get<StudentAccount>('/api/billing/my/account')
    return response.data
  },
}
