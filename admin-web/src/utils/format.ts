import dayjs from 'dayjs'

// 日期格式化
export const formatDate = (date: string | Date | null | undefined): string => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

export const formatDateTime = (date: string | Date | null | undefined): string => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

export const formatTime = (date: string | Date | null | undefined): string => {
  if (!date) return '-'
  return dayjs(date).format('HH:mm')
}

export const formatMonthYear = (date: string | Date | null | undefined): string => {
  if (!date) return '-'
  return dayjs(date).format('YYYY年MM月')
}

export const formatRelativeTime = (date: string | Date | null | undefined): string => {
  if (!date) return '-'
  const d = dayjs(date)
  const now = dayjs()
  const diffMinutes = now.diff(d, 'minute')
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  const diffHours = now.diff(d, 'hour')
  if (diffHours < 24) return `${diffHours}小时前`
  const diffDays = now.diff(d, 'day')
  if (diffDays < 7) return `${diffDays}天前`
  return formatDate(date)
}

// 金额格式化
export const formatMoney = (amount: number | null | undefined): string => {
  if (amount == null) return '-'
  return `¥${amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
}

export const formatMoneyShort = (amount: number | null | undefined): string => {
  if (amount == null) return '-'
  if (amount >= 10000) return `¥${(amount / 10000).toFixed(1)}万`
  return `¥${amount.toFixed(0)}`
}

// 文件大小格式化
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// 时长格式化（分钟）
export const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (mins === 0) return `${hours}小时`
  return `${hours}小时${mins}分钟`
}

// 课程状态标签
export const getCourseStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    scheduled: '待上课',
    completed: '已完成',
    cancelled: '已取消',
    student_leave_pending_makeup: '学生请假待补',
    teacher_leave_pending_makeup: '老师请假待补',
    makeup_scheduled: '已安排补课',
  }
  return map[status] || status
}

export const getCourseStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    scheduled: 'blue',
    completed: 'green',
    cancelled: 'default',
    student_leave_pending_makeup: 'orange',
    teacher_leave_pending_makeup: 'gold',
    makeup_scheduled: 'purple',
  }
  return map[status] || 'default'
}

// 作业状态
export const getAssignmentStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    pending: '待提交',
    submitted: '待批改',
    graded: '已批改',
  }
  return map[status] || status
}

export const getAssignmentStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    pending: 'orange',
    submitted: 'green',
    graded: 'blue',
  }
  return map[status] || 'default'
}

// 知识点状态
export const getKnowledgeStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    mastered: '已掌握',
    learning: '学习中',
    todo: '待学习',
  }
  return map[status] || status
}

export const getKnowledgeStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    mastered: '#10B981',
    learning: '#F59E0B',
    todo: '#9CA3AF',
  }
  return map[status] || '#9CA3AF'
}

// 文件类型图标颜色
export const getFileTypeColor = (fileType: string): string => {
  if (fileType.includes('pdf')) return '#EF4444'
  if (fileType.includes('word') || fileType.includes('document')) return '#2563EB'
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '#10B981'
  if (fileType.includes('image')) return '#F59E0B'
  return '#6B7280'
}

export const getFileTypeLabel = (fileType: string): string => {
  if (fileType.includes('pdf')) return 'PDF'
  if (fileType.includes('word') || fileType.includes('document')) return 'Word'
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return 'Excel'
  if (fileType.includes('image')) return '图片'
  return '文件'
}
