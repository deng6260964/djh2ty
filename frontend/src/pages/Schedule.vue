<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">课程表</h1>
        <p class="mt-2 text-gray-600">查看和管理您的课程安排</p>
      </div>

      <!-- 筛选器 -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">开始日期</label>
            <input
              v-model="filters.startDate"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">结束日期</label>
            <input
              v-model="filters.endDate"
              type="date"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">科目</label>
            <select
              v-model="filters.subject"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">全部科目</option>
              <option value="数学">数学</option>
              <option value="语文">语文</option>
              <option value="英语">英语</option>
              <option value="物理">物理</option>
              <option value="化学">化学</option>
              <option value="生物">生物</option>
            </select>
          </div>
          <div class="flex items-end">
            <button
              @click="loadCourses"
              class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              筛选
            </button>
          </div>
        </div>
      </div>

      <!-- 视图切换 -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex space-x-4">
          <button
            @click="viewMode = 'calendar'"
            :class="[
              'px-4 py-2 rounded-md transition-colors',
              viewMode === 'calendar'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            日历视图
          </button>
          <button
            @click="viewMode = 'list'"
            :class="[
              'px-4 py-2 rounded-md transition-colors',
              viewMode === 'list'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            ]"
          >
            列表视图
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-gray-600">加载中...</p>
      </div>

      <!-- 日历视图 -->
      <div v-else-if="viewMode === 'calendar'" class="bg-white rounded-lg shadow-sm p-6">
        <div class="grid grid-cols-7 gap-1 mb-4">
          <div v-for="day in weekDays" :key="day" class="p-3 text-center font-medium text-gray-700 bg-gray-50">
            {{ day }}
          </div>
        </div>
        <div class="grid grid-cols-7 gap-1">
          <div
            v-for="date in calendarDates"
            :key="date.date"
            class="min-h-[120px] p-2 border border-gray-200"
            :class="{
              'bg-gray-50': !date.isCurrentMonth,
              'bg-blue-50': date.isToday
            }"
          >
            <div class="text-sm font-medium mb-2" :class="{
              'text-gray-400': !date.isCurrentMonth,
              'text-blue-600': date.isToday
            }">
              {{ date.day }}
            </div>
            <div class="space-y-1">
              <div
                v-for="course in getCoursesForDate(date.date)"
                :key="course.id"
                class="text-xs p-1 rounded bg-blue-100 text-blue-800 cursor-pointer hover:bg-blue-200"
                @click="showCourseDetail(course)"
              >
                {{ course.title }}
                <br>
                {{ formatTime(course.start_time) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 列表视图 -->
      <div v-else class="bg-white rounded-lg shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  课程名称
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  科目
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  级别
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  时间
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  地点
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  报名人数
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="course in courses" :key="course.id" class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="text-sm font-medium text-gray-900">{{ course.title }}</div>
                  <div class="text-sm text-gray-500">{{ course.description }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ course.subject }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ course.level }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>{{ formatDateTime(course.start_time) }}</div>
                  <div class="text-gray-500">至 {{ formatDateTime(course.end_time) }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ course.location || '未设置' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ course.enrolled_count || 0 }} / {{ course.max_students }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    :class="[
                      'inline-flex px-2 py-1 text-xs font-semibold rounded-full',
                      course.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    ]"
                  >
                    {{ getStatusText(course.status) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    @click="showCourseDetail(course)"
                    class="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    查看详情
                  </button>
                  <button
                    v-if="userRole === 'student' && !isEnrolled(course.id)"
                    @click="enrollCourse(course.id)"
                    class="text-green-600 hover:text-green-900"
                  >
                    报名
                  </button>
                  <button
                    v-if="userRole === 'student' && isEnrolled(course.id)"
                    @click="dropCourse(course.id)"
                    class="text-red-600 hover:text-red-900"
                  >
                    退课
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div v-if="pagination.pages > 1" class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
          <div class="flex items-center justify-between">
            <div class="flex-1 flex justify-between sm:hidden">
              <button
                @click="changePage(pagination.page - 1)"
                :disabled="pagination.page <= 1"
                class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                @click="changePage(pagination.page + 1)"
                :disabled="pagination.page >= pagination.pages"
                class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
            <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p class="text-sm text-gray-700">
                  显示第 {{ (pagination.page - 1) * pagination.limit + 1 }} 到
                  {{ Math.min(pagination.page * pagination.limit, pagination.total) }} 条，
                  共 {{ pagination.total }} 条记录
                </p>
              </div>
              <div>
                <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    @click="changePage(pagination.page - 1)"
                    :disabled="pagination.page <= 1"
                    class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    上一页
                  </button>
                  <button
                    v-for="page in getPageNumbers()"
                    :key="page"
                    @click="changePage(page)"
                    :class="[
                      'relative inline-flex items-center px-4 py-2 border text-sm font-medium',
                      page === pagination.page
                        ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                    ]"
                  >
                    {{ page }}
                  </button>
                  <button
                    @click="changePage(pagination.page + 1)"
                    :disabled="pagination.page >= pagination.pages"
                    class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    下一页
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 课程详情模态框 -->
      <div v-if="showDetailModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
          <div class="mt-3">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-gray-900">课程详情</h3>
              <button
                @click="showDetailModal = false"
                class="text-gray-400 hover:text-gray-600"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            <div v-if="selectedCourse" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">课程名称</label>
                <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.title }}</p>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">科目</label>
                  <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.subject }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">级别</label>
                  <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.level }}</p>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">开始时间</label>
                  <p class="mt-1 text-sm text-gray-900">{{ formatDateTime(selectedCourse.start_time) }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">结束时间</label>
                  <p class="mt-1 text-sm text-gray-900">{{ formatDateTime(selectedCourse.end_time) }}</p>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">地点</label>
                <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.location || '未设置' }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">课程描述</label>
                <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.description || '暂无描述' }}</p>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">最大人数</label>
                  <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.max_students }}</p>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">已报名人数</label>
                  <p class="mt-1 text-sm text-gray-900">{{ selectedCourse.enrolled_count || 0 }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiService from '@/services/api'

// 响应式数据
const loading = ref(false)
const courses = ref([])
const viewMode = ref('list')
const showDetailModal = ref(false)
const selectedCourse = ref(null)
const userRole = ref('')
const enrolledCourses = ref([])

// 筛选器
const filters = ref({
  startDate: '',
  endDate: '',
  subject: ''
})

// 分页
const pagination = ref({
  page: 1,
  limit: 20,
  total: 0,
  pages: 0
})

// 日历相关
const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const currentDate = ref(new Date())

// 计算属性
const calendarDates = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())
  
  const dates = []
  const today = new Date()
  
  for (let i = 0; i < 42; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    
    dates.push({
      date: date.toISOString().split('T')[0],
      day: date.getDate(),
      isCurrentMonth: date.getMonth() === month,
      isToday: date.toDateString() === today.toDateString()
    })
  }
  
  return dates
})

// 方法
const loadCourses = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.value.page,
      limit: pagination.value.limit,
      start_date: filters.value.startDate,
      end_date: filters.value.endDate
    }
    
    const response = await apiService.get('/api/courses', { params })
    if (response.success) {
      courses.value = response.data.courses
      pagination.value = response.data.pagination
    }
  } catch (error) {
    console.error('加载课程失败:', error)
  } finally {
    loading.value = false
  }
}

const loadEnrolledCourses = async () => {
  if (userRole.value === 'student') {
    try {
      const response = await apiService.get('/api/courses')
      if (response.success) {
        enrolledCourses.value = response.data.courses.map(course => course.id)
      }
    } catch (error) {
      console.error('加载已报名课程失败:', error)
    }
  }
}

const changePage = (page: number) => {
  if (page >= 1 && page <= pagination.value.pages) {
    pagination.value.page = page
    loadCourses()
  }
}

const getPageNumbers = () => {
  const pages = []
  const total = pagination.value.pages
  const current = pagination.value.page
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...', total)
    } else if (current >= total - 3) {
      pages.push(1, '...')
      for (let i = total - 4; i <= total; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1, '...')
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i)
      }
      pages.push('...', total)
    }
  }
  
  return pages
}

const getCoursesForDate = (date: string) => {
  return courses.value.filter(course => {
    const courseDate = new Date(course.start_time).toISOString().split('T')[0]
    return courseDate === date
  })
}

const showCourseDetail = (course: any) => {
  selectedCourse.value = course
  showDetailModal.value = true
}

const isEnrolled = (courseId: number) => {
  return enrolledCourses.value.includes(courseId)
}

const enrollCourse = async (courseId: number) => {
  try {
    const response = await apiService.post(`/api/courses/${courseId}/enroll`)
    if (response.success) {
      enrolledCourses.value.push(courseId)
      await loadCourses() // 重新加载课程列表以更新报名人数
    }
  } catch (error) {
    console.error('报名失败:', error)
  }
}

const dropCourse = async (courseId: number) => {
  try {
    const response = await apiService.post(`/api/courses/${courseId}/drop`)
    if (response.success) {
      const index = enrolledCourses.value.indexOf(courseId)
      if (index > -1) {
        enrolledCourses.value.splice(index, 1)
      }
      await loadCourses() // 重新加载课程列表以更新报名人数
    }
  } catch (error) {
    console.error('退课失败:', error)
  }
}

const formatDateTime = (dateTime: string) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (dateTime: string) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusText = (status: string) => {
  const statusMap = {
    'active': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 生命周期
onMounted(async () => {
  const user = apiService.getCurrentUser()
  userRole.value = user?.role || ''
  
  // 设置默认日期范围（当前月份）
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  
  filters.value.startDate = firstDay.toISOString().split('T')[0]
  filters.value.endDate = lastDay.toISOString().split('T')[0]
  
  await loadCourses()
  await loadEnrolledCourses()
})
</script>

<style scoped>
/* 自定义样式 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>