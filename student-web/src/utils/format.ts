import dayjs from 'dayjs'

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

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export const formatDuration = (minutes: number): string => {
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (mins === 0) return `${hours}小时`
  return `${hours}小时${mins}分钟`
}

export const getCourseStatusLabel = (status: string): string => {
  const map: Record<string, string> = {
    scheduled: '待上课',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

export const getCourseStatusColor = (status: string): string => {
  const map: Record<string, string> = {
    scheduled: 'blue',
    completed: 'green',
    cancelled: 'default',
  }
  return map[status] || 'default'
}

export const getFileTypeLabel = (fileType: string): string => {
  if (fileType.includes('pdf')) return 'PDF'
  if (fileType.includes('word') || fileType.includes('document')) return 'Word'
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return 'Excel'
  if (fileType.includes('image')) return '图片'
  return '文件'
}

export const getFileTypeColor = (fileType: string): string => {
  if (fileType.includes('pdf')) return '#EF4444'
  if (fileType.includes('word') || fileType.includes('document')) return '#2563EB'
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return '#10B981'
  if (fileType.includes('image')) return '#F59E0B'
  return '#6B7280'
}
