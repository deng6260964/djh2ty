// API 通用响应类型

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ApiError {
  code: string
  message: string
  detail?: Record<string, unknown>
}

// 认证
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
    username: string
    role: string
    display_name: string
  }
}

export interface RefreshTokenResponse {
  access_token: string
  expires_in: number
}

// 仪表盘
export interface DashboardOverview {
  today_courses: TodayCourse[]
  stats: DashboardStats
  upcoming_courses: TodayCourse[]
  recent_feedback: RecentFeedback[]
}

export interface TodayCourse {
  id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  status: string
}

export interface DashboardStats {
  active_students: number
  this_month_courses: number
  this_month_income: number
  pending_grading: number
  outstanding_fee: number
  unread_notifications: number
}

export interface RecentFeedback {
  id: number
  student_name: string
  subject: string
  created_at: string
}

export interface WorkbenchCourseItem {
  id: number
  student_id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  status: string
  current_balance: number
  projected_charge: number
  needs_payment: boolean
}

export interface WorkbenchPendingRecordItem {
  id: number
  student_id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  status: string
  current_balance: number
  projected_charge: number
  needs_payment: boolean
}

export interface WorkbenchPaymentAlertItem {
  student_id: number
  student_name: string
  grade: string
  current_balance: number
  next_course_id: number
  next_course_time: string
  next_course_subject: string
  projected_charge: number
  shortage_amount: number
}

export interface WorkbenchAssignmentItem {
  assignment_id: number
  assignment_title: string
  student_id: number
  student_name: string
  subject: string
  submitted_at?: string
  status: string
}

export interface WorkbenchResponse {
  today: string
  summary: {
    pending_record_count: number
    today_course_count: number
    payment_alert_count: number
    assignment_review_count: number
  }
  today_courses: WorkbenchCourseItem[]
  pending_records: WorkbenchPendingRecordItem[]
  payment_alerts: WorkbenchPaymentAlertItem[]
  assignment_reviews: WorkbenchAssignmentItem[]
}
