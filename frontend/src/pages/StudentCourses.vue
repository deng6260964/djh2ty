<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">课程中心</h1>
        <p class="mt-2 text-gray-600">浏览和报名感兴趣的课程</p>
      </div>

      <!-- 筛选器 -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">科目</label>
            <select v-model="filters.subject" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部科目</option>
              <option value="英语">英语</option>
              <option value="数学">数学</option>
              <option value="语文">语文</option>
              <option value="物理">物理</option>
              <option value="化学">化学</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">级别</label>
            <select v-model="filters.level" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部级别</option>
              <option value="小学">小学</option>
              <option value="初中">初中</option>
              <option value="高中">高中</option>
              <option value="大学">大学</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">状态</label>
            <select v-model="filters.status" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部状态</option>
              <option value="active">进行中</option>
              <option value="upcoming">即将开始</option>
            </select>
          </div>
          <div class="flex items-end">
            <button @click="searchCourses" class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
              搜索
            </button>
          </div>
        </div>
      </div>

      <!-- 课程列表 -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">加载中...</p>
      </div>

      <div v-else-if="courses.length === 0" class="text-center py-12">
        <div class="text-gray-400 mb-4">
          <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">暂无课程</h3>
        <p class="text-gray-600">当前没有符合条件的课程</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="course in courses" :key="course.id" class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
          <div class="p-6">
            <div class="flex justify-between items-start mb-4">
              <h3 class="text-lg font-semibold text-gray-900">{{ course.title }}</h3>
              <span :class="getStatusClass(course.status)" class="px-2 py-1 rounded text-xs font-medium">
                {{ getStatusText(course.status) }}
              </span>
            </div>
            
            <div class="space-y-2 mb-4">
              <div class="flex items-center text-sm text-gray-600">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                </svg>
                {{ course.subject }} · {{ course.level }}
              </div>
              <div class="flex items-center text-sm text-gray-600">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {{ formatDateTime(course.start_time) }} - {{ formatDateTime(course.end_time) }}
              </div>
              <div v-if="course.location" class="flex items-center text-sm text-gray-600">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                {{ course.location }}
              </div>
              <div class="flex items-center text-sm text-gray-600">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                </svg>
                {{ course.enrolled_count || 0 }} / {{ course.max_students }} 人
              </div>
            </div>
            
            <p v-if="course.description" class="text-sm text-gray-600 mb-4 line-clamp-2">
              {{ course.description }}
            </p>
            
            <div class="flex space-x-2">
              <button 
                v-if="!isEnrolled(course.id)"
                @click="enrollCourse(course)"
                :disabled="course.enrolled_count >= course.max_students || enrolling === course.id"
                class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {{ enrolling === course.id ? '报名中...' : '报名' }}
              </button>
              <button 
                v-else
                @click="dropCourse(course)"
                :disabled="dropping === course.id"
                class="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {{ dropping === course.id ? '退课中...' : '退课' }}
              </button>
              <button 
                @click="viewCourseDetails(course)"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors text-sm"
              >
                详情
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiService from '@/services/api'

// 响应式数据
const courses = ref<any[]>([])
const loading = ref(false)
const enrolling = ref<number | null>(null)
const dropping = ref<number | null>(null)
const myEnrollments = ref<number[]>([])

// 筛选器
const filters = ref({
  subject: '',
  level: '',
  status: ''
})

// 生命周期
onMounted(() => {
  loadCourses()
  loadMyEnrollments()
})

// 方法
const loadCourses = async () => {
  try {
    loading.value = true
    const response = await apiService.get('/api/courses')
    if (response.success) {
      courses.value = response.data.courses || []
    } else {
      console.error('获取课程列表失败:', response.message)
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadMyEnrollments = async () => {
  try {
    const user = apiService.getCurrentUser()
    if (user && user.role === 'student') {
      // 这里需要一个获取学生已报名课程的API
      // 暂时使用空数组
      myEnrollments.value = []
    }
  } catch (error) {
    console.error('获取报名信息失败:', error)
  }
}

const searchCourses = async () => {
  try {
    loading.value = true
    const params = Object.fromEntries(
      Object.entries(filters.value).filter(([_, value]) => value !== '')
    )
    const response = await apiService.get('/api/courses', params)
    if (response.success) {
      courses.value = response.data.courses || []
    } else {
      console.error('搜索课程失败:', response.message)
    }
  } catch (error) {
    console.error('搜索课程失败:', error)
  } finally {
    loading.value = false
  }
}

const enrollCourse = async (course: any) => {
  try {
    enrolling.value = course.id
    const response = await apiService.enrollCourse(course.id)
    if (response.success) {
      alert('报名成功！')
      myEnrollments.value.push(course.id)
      // 更新课程的报名人数
      course.enrolled_count = (course.enrolled_count || 0) + 1
    } else {
      alert(`报名失败: ${response.message}`)
    }
  } catch (error) {
    console.error('报名失败:', error)
    alert('报名失败，请稍后重试')
  } finally {
    enrolling.value = null
  }
}

const dropCourse = async (course: any) => {
  if (!confirm(`确定要退出课程"${course.title}"吗？`)) {
    return
  }
  
  try {
    dropping.value = course.id
    const response = await apiService.dropCourse(course.id)
    if (response.success) {
      alert('退课成功！')
      myEnrollments.value = myEnrollments.value.filter(id => id !== course.id)
      // 更新课程的报名人数
      course.enrolled_count = Math.max((course.enrolled_count || 0) - 1, 0)
    } else {
      alert(`退课失败: ${response.message}`)
    }
  } catch (error) {
    console.error('退课失败:', error)
    alert('退课失败，请稍后重试')
  } finally {
    dropping.value = null
  }
}

const viewCourseDetails = (course: any) => {
  // 这里可以跳转到课程详情页面或显示详情模态框
  alert(`课程详情：\n标题：${course.title}\n科目：${course.subject}\n级别：${course.level}\n描述：${course.description || '暂无描述'}`)
}

const isEnrolled = (courseId: number) => {
  return myEnrollments.value.includes(courseId)
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

const getStatusText = (status: string) => {
  const statusMap = {
    'active': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getStatusClass = (status: string) => {
  const classMap = {
    'active': 'bg-green-100 text-green-800',
    'completed': 'bg-gray-100 text-gray-800',
    'cancelled': 'bg-red-100 text-red-800'
  }
  return classMap[status] || 'bg-gray-100 text-gray-800'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

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