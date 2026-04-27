// utils/format.js - 格式化工具

/**
 * 格式化日期
 * @param {string|Date} date - 日期字符串或 Date 对象
 * @param {string} format - 格式，默认 'YYYY-MM-DD'
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''

  const d = typeof date === 'string' ? new Date(date) : date
  if (isNaN(d.getTime())) return ''

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化时间（HH:mm）
 */
function formatTime(datetime) {
  if (!datetime) return ''
  const d = new Date(datetime)
  if (isNaN(d.getTime())) return ''
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 */
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }

  return `${size.toFixed(size < 10 && unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
}

/**
 * 获取相对时间描述（如：2天前、刚刚）
 * @param {string|Date} date
 */
function getRelativeTime(date) {
  if (!date) return ''

  const now = new Date()
  const d = new Date(date)
  const diff = now - d
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`

  return formatDate(d)
}

/**
 * 计算距截止日期剩余天数
 * @param {string} dueDate - 截止日期字符串 YYYY-MM-DD
 */
function getDaysUntilDue(dueDate) {
  if (!dueDate) return null

  const now = new Date()
  now.setHours(0, 0, 0, 0)

  const due = new Date(dueDate)
  due.setHours(0, 0, 0, 0)

  const diff = due - now
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))

  return days
}

/**
 * 截止日期状态描述
 * @param {string} dueDate
 */
function getDueDateStatus(dueDate) {
  const days = getDaysUntilDue(dueDate)
  if (days === null) return { text: '', urgent: false }

  if (days < 0) return { text: '已逾期', urgent: true, color: '#EF4444' }
  if (days === 0) return { text: '今天截止', urgent: true, color: '#EF4444' }
  if (days === 1) return { text: '明天截止', urgent: true, color: '#F59E0B' }
  if (days <= 3) return { text: `还剩 ${days} 天`, urgent: true, color: '#F59E0B' }

  return { text: `还剩 ${days} 天`, urgent: false, color: '#6B7280' }
}

/**
 * 格式化时长（分钟转文字）
 * @param {number} minutes - 时长（分钟）
 */
function formatDuration(minutes) {
  if (!minutes) return ''
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  if (remainMinutes === 0) return `${hours}小时`
  return `${hours}小时${remainMinutes}分钟`
}

/**
 * 获取文件类型图标文字（emoji）
 * @param {string} fileType - MIME 类型
 * @param {string} filename - 文件名
 */
function getFileTypeIcon(fileType, filename) {
  if (!fileType && !filename) return '📄'

  const ext = filename ? filename.split('.').pop()?.toLowerCase() : ''

  if (fileType?.includes('pdf') || ext === 'pdf') return 'PDF'
  if (fileType?.includes('word') || fileType?.includes('document') || ['doc', 'docx'].includes(ext)) return 'DOC'
  if (fileType?.includes('excel') || fileType?.includes('spreadsheet') || ['xls', 'xlsx'].includes(ext)) return 'XLS'
  if (fileType?.includes('image') || ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return 'IMG'

  return 'FILE'
}

/**
 * 获取文件类型颜色
 * @param {string} fileType
 * @param {string} filename
 */
function getFileTypeColor(fileType, filename) {
  const ext = filename ? filename.split('.').pop()?.toLowerCase() : ''

  if (fileType?.includes('pdf') || ext === 'pdf') return '#EF4444'
  if (fileType?.includes('word') || fileType?.includes('document') || ['doc', 'docx'].includes(ext)) return '#2563EB'
  if (fileType?.includes('excel') || fileType?.includes('spreadsheet') || ['xls', 'xlsx'].includes(ext)) return '#10B981'
  if (fileType?.includes('image') || ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return '#F59E0B'

  return '#6B7280'
}

/**
 * 课程状态转换
 */
function getCourseStatusInfo(status) {
  const statusMap = {
    scheduled: { text: '待上课', bgColor: '#EFF6FF', textColor: '#2563EB' },
    completed: { text: '已完成', bgColor: '#ECFDF5', textColor: '#10B981' },
    cancelled: { text: '已取消', bgColor: '#F3F4F6', textColor: '#9CA3AF' }
  }
  return statusMap[status] || { text: status, bgColor: '#F3F4F6', textColor: '#9CA3AF' }
}

/**
 * 作业状态转换
 */
function getAssignmentStatusInfo(status) {
  const statusMap = {
    pending: { text: '未提交', bgColor: '#FFFBEB', textColor: '#F59E0B' },
    submitted: { text: '已提交', bgColor: '#ECFDF5', textColor: '#10B981' },
    graded: { text: '已批改', bgColor: '#EFF6FF', textColor: '#2563EB' }
  }
  return statusMap[status] || { text: status, bgColor: '#F3F4F6', textColor: '#9CA3AF' }
}

/**
 * 知识点掌握状态
 */
function getKnowledgeStatusInfo(status) {
  const statusMap = {
    mastered: { text: '已掌握', color: '#10B981', icon: '✓' },
    learning: { text: '学习中', color: '#2563EB', icon: '○' },
    todo: { text: '待学习', color: '#9CA3AF', icon: '·' }
  }
  return statusMap[status] || { text: status, color: '#9CA3AF', icon: '·' }
}

/**
 * 格式化月份显示
 */
function formatMonth(year, month) {
  return `${year}年${month}月`
}

/**
 * 判断是否是今天
 */
function isToday(dateStr) {
  const today = new Date()
  const d = new Date(dateStr)
  return today.getFullYear() === d.getFullYear() &&
    today.getMonth() === d.getMonth() &&
    today.getDate() === d.getDate()
}

/**
 * 截取文本，超长显示省略号
 */
function truncateText(text, maxLength = 50) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

module.exports = {
  formatDate,
  formatTime,
  formatFileSize,
  getRelativeTime,
  getDaysUntilDue,
  getDueDateStatus,
  formatDuration,
  getFileTypeIcon,
  getFileTypeColor,
  getCourseStatusInfo,
  getAssignmentStatusInfo,
  getKnowledgeStatusInfo,
  formatMonth,
  isToday,
  truncateText
}
