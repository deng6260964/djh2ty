export const SUBJECTS = [
  '语文', '数学', '英语', '物理', '化学', '生物',
  '历史', '地理', '政治',
]

export const COURSE_STATUSES: Record<string, { label: string; color: string }> = {
  scheduled: { label: '待上课', color: 'blue' },
  completed: { label: '已完成', color: 'green' },
  cancelled: { label: '已取消', color: 'default' },
}

export const ASSIGNMENT_STATUSES: Record<string, { label: string; color: string }> = {
  pending: { label: '待提交', color: 'orange' },
  submitted: { label: '已提交', color: 'green' },
  graded: { label: '已批改', color: 'blue' },
}

export const KNOWLEDGE_STATUSES: Record<string, { label: string; color: string }> = {
  mastered: { label: '已掌握', color: '#10B981' },
  learning: { label: '学习中', color: '#F59E0B' },
  todo: { label: '待学习', color: '#9CA3AF' },
}
