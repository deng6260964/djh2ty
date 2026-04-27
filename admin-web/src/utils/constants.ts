// 全局常量

export const GRADES = [
  '小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
  '初一', '初二', '初三',
  '高一', '高二', '高三',
]

export const SUBJECTS = [
  '语文', '数学', '英语', '物理', '化学', '生物',
  '历史', '地理', '政治', '音乐', '美术', '体育',
]

export const COURSE_STATUSES = [
  { value: 'scheduled', label: '待上课', color: 'blue' },
  { value: 'completed', label: '已完成', color: 'green' },
  { value: 'cancelled', label: '已取消', color: 'default' },
]

export const ASSIGNMENT_STATUSES = [
  { value: 'pending', label: '待提交', color: 'orange' },
  { value: 'submitted', label: '待批改', color: 'green' },
  { value: 'graded', label: '已批改', color: 'blue' },
]

export const PAYMENT_METHODS = [
  { value: 'wechat', label: '微信转账' },
  { value: 'alipay', label: '支付宝' },
  { value: 'cash', label: '现金' },
  { value: 'bank', label: '银行转账' },
]

export const KNOWLEDGE_POINT_STATUSES = [
  { value: 'mastered', label: '已掌握', color: '#10B981' },
  { value: 'learning', label: '学习中', color: '#F59E0B' },
  { value: 'todo', label: '待学习', color: '#9CA3AF' },
]

export const RESOURCE_TYPES = [
  { value: 'lecture', label: '讲义' },
  { value: 'exercise', label: '练习题' },
  { value: 'exam', label: '真题' },
  { value: 'reference', label: '参考资料' },
  { value: 'note', label: '笔记' },
]

export const EXAM_TYPES = [
  { value: 'quiz', label: '随堂测' },
  { value: 'midterm', label: '期中考试' },
  { value: 'final', label: '期末考试' },
  { value: 'mock', label: '模拟考试' },
  { value: 'monthly', label: '月测' },
  { value: 'other', label: '其他' },
]

export const PAGE_SIZE = 20

export const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'image/jpeg',
  'image/png',
  'image/gif',
]

export const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
