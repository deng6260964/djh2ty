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

export interface MyAssignment {
  id: number
  title: string
  subject: string
  due_date: string
  status: 'pending' | 'submitted' | 'graded'
  score?: number | null
  comment?: string | null
  created_at: string
}

export interface MyAssignmentDetail {
  id: number
  title: string
  content: string
  subject: string
  due_date: string
  status: 'pending' | 'submitted' | 'graded'
  submitted_at?: string
  score?: number | null
  comment?: string | null
  graded_at?: string
  created_at: string
}

export interface MyFeedback {
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

export interface SharedResource {
  id: number
  title: string
  subject?: string
  grade?: string
  description?: string
  file_type: string
  original_name: string
  file_size: number
  created_at: string
}

export interface KnowledgePoint {
  id: number
  subject: string
  chapter: string
  point_name: string
  status: 'mastered' | 'learning' | 'todo'
  notes?: string
}
