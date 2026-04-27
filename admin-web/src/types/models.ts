// 数据模型类型定义

// 学生
export interface Student {
  id: number
  name: string
  grade: string
  subjects: string[]
  parent_name: string
  parent_phone: string
  school?: string
  notes?: string
  is_active: boolean
  user_id?: number | null
  parent_user_id?: number | null
  username?: string
  created_at: string
  stats?: StudentStats
}

export interface StudentStats {
  total_courses: number
  completed_courses: number
  pending_assignments: number
  total_paid: number
  outstanding: number
}

export interface StudentFormData {
  name: string
  grade: string
  subjects: string[]
  parent_name: string
  parent_phone: string
  school?: string
  notes?: string
  username?: string
  password?: string
}

// 课程
export interface Course {
  id: number
  student_id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  duration: number
  status: 'scheduled' | 'completed' | 'cancelled'
  location?: string
  hourly_rate?: number
  notes?: string
}

export interface CourseFormData {
  student_id: number
  subject: string
  start_time: string
  end_time: string
  location?: string
  notes?: string
}

export interface ConflictCheckRequest {
  start_time: string
  end_time: string
  exclude_id?: number | null
}

export interface ConflictCheckResponse {
  has_conflict: boolean
  conflict?: {
    course_id: number
    student_name: string
    start_time: string
    end_time: string
  }
}

export interface CalendarData {
  [date: string]: CalendarCourse[]
}

export interface CalendarCourse {
  id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  status: string
}

export interface WeekCourseItem {
  id: number
  student_id: number
  student_name: string
  subject: string
  start_time: string
  end_time: string
  duration: number
  status: string
  hourly_rate: number
  projected_charge: number
  current_balance: number
  needs_payment: boolean
  is_weekend: boolean
}

export interface WeekCoursesResponse {
  week_start: string
  week_end: string
  items: WeekCourseItem[]
}

export interface CopyWeekPreviewRequest {
  source_week_start: string
  target_week_start: string
}

export interface CopyWeekPreviewItem {
  source_course_id: number
  student_id: number
  student_name: string
  subject: string
  source_start_time: string
  source_end_time: string
  target_start_time: string
  target_end_time: string
  duration: number
  projected_charge: number
  current_balance: number
  needs_payment: boolean
  has_conflict: boolean
  status: 'copyable' | 'needs_payment' | 'conflict'
  conflict?: {
    course_id: number
    student_name: string
    start_time: string
    end_time: string
  }
}

export interface CopyWeekPreviewResponse {
  source_week_start: string
  target_week_start: string
  items: CopyWeekPreviewItem[]
  total_count: number
  copyable_count: number
  conflict_count: number
  needs_payment_count: number
}

export interface CopyWeekConfirmResponse {
  created_count: number
  skipped_count: number
  created_course_ids: number[]
  skipped_items: Array<{
    source_course_id: number
    reason: string
    conflict?: {
      course_id: number
      student_name: string
      start_time: string
      end_time: string
    }
  }>
}

// 作业
export interface Assignment {
  id: number
  title: string
  subject: string
  content?: string
  due_date: string
  created_at: string
  student_count: number
  submitted_count: number
  graded_count: number
}

export interface AssignmentDetail {
  id: number
  title: string
  content: string
  subject: string
  due_date: string
  created_at: string
  students: AssignmentStudent[]
}

export interface AssignmentStudent {
  student_id: number
  student_name: string
  status: 'pending' | 'submitted' | 'graded'
  submitted_at?: string
  score?: number | null
  comment?: string | null
}

export interface AssignmentFormData {
  title: string
  subject: string
  content: string
  due_date: string
  student_ids: number[]
}

export interface GradeRequest {
  student_id: number
  score: number
  comment: string
}

// 课堂反馈
export interface Feedback {
  id: number
  course_id: number
  student_id: number
  student_name: string
  subject: string
  course_date: string
  performance: string
  knowledge_mastery: string
  problems: string
  next_plan: string
  rating?: number
  is_pushed: boolean
  pushed_at?: string
  created_at: string
}

export interface FeedbackFormData {
  course_id: number
  student_id: number
  performance: string
  knowledge_mastery: string
  problems: string
  next_plan: string
  rating?: number
}

export interface FeedbackTemplate {
  id: number
  title: string
  performance?: string
  knowledge_mastery?: string
  problems?: string
  next_plan?: string
}

// 学习进度
export interface Grade {
  id: number
  student_id: number
  student_name: string
  subject: string
  exam_type: string
  exam_name: string
  score: number
  full_score: number
  exam_date: string
  notes?: string
}

export interface GradeFormData {
  student_id: number
  subject: string
  exam_type: string
  exam_name: string
  score: number
  full_score: number
  exam_date: string
  notes?: string
}

export interface GradeTrendData {
  student_name: string
  subject: string
  data: GradeTrendPoint[]
}

export interface GradeTrendPoint {
  exam_date: string
  score: number
  full_score: number
  percentage: number
  exam_name: string
}

export interface KnowledgePoint {
  id: number
  student_id: number
  subject: string
  chapter: string
  point_name: string
  status: 'mastered' | 'learning' | 'todo'
  notes?: string
}

// 收费管理
export interface SubjectPrice {
  id: number
  subject: string
  price_per_hour: number
}

export interface BillingRecord {
  id: number
  student_id: number
  student_name: string
  course_id?: number
  amount: number
  paid_amount?: number
  status: 'unpaid' | 'paid' | 'partial'
  payment_method?: string
  paid_at?: string
  notes?: string
  created_at: string
}

export interface OutstandingStudent {
  student_id: number
  student_name: string
  grade: string
  outstanding_amount: number
  unpaid_count: number
}

export interface StudentAccountPaymentRecord {
  record_id: number
  amount: number
  paid_at?: string
  payment_method?: string
  notes?: string
}

export interface StudentAccountChargeRecord {
  record_id: number
  course_id?: number
  subject?: string
  amount: number
  created_at: string
  notes?: string
}

export interface StudentAccount {
  student_id: number
  student_name: string
  grade: string
  current_balance: number
  total_received: number
  total_charged: number
  estimated_lessons_left: number
  main_subject?: string
  main_subject_hourly_rate?: number
  has_payment_alert: boolean
  next_course_id?: number
  next_course_time?: string
  next_course_subject?: string
  next_course_projected_charge?: number
  recent_payments: StudentAccountPaymentRecord[]
  recent_charges: StudentAccountChargeRecord[]
}

export interface PaymentRequest {
  paid_amount: number
  payment_method: string
  paid_at: string
  notes?: string
}

export interface BillingSummary {
  period: { start: string; end: string }
  total_receivable: number
  total_paid: number
  total_outstanding: number
  by_student: BillingByStudent[]
  by_subject: BillingBySubject[]
  monthly_trend: MonthlyTrend[]
}

export interface BillingByStudent {
  student_id: number
  student_name: string
  receivable: number
  paid: number
  outstanding: number
}

export interface BillingBySubject {
  subject: string
  total: number
}

export interface MonthlyTrend {
  month: string
  paid: number
}

// 资料管理
export interface Resource {
  id: number
  title: string
  subject?: string
  grade?: string
  description?: string
  file_type: string
  original_name: string
  file_size: number
  created_at: string
  shared_students?: SharedStudent[]
}

export interface SharedStudent {
  student_id: number
  student_name: string
}

// 通知
export interface Notification {
  id: number
  title: string
  content: string
  is_read: boolean
  created_at: string
}
