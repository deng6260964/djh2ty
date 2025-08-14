<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- 页面标题 -->
      <div class="mb-8">
        <div class="flex items-center mb-4">
          <button
            @click="goBack"
            class="mr-4 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center"
            title="返回"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
          </button>
          <div>
            <h1 class="text-3xl font-bold text-gray-900">课程表</h1>
            <p class="mt-2 text-gray-600">按周/月视图展示课程安排</p>
          </div>
        </div>
      </div>

      <!-- 操作栏 -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex justify-between items-center">
          <div class="flex space-x-4">
            <button
              @click="openCreateDialog"
              class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors flex items-center"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              创建课程
            </button>
            <button
              @click="loadCourses"
              class="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 transition-colors flex items-center"
            >
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              刷新
            </button>
            <!-- 视图切换按钮 -->
            <div class="flex bg-gray-100 rounded-md p-1">
              <button
                @click="currentView = 'week'"
                :class="[
                  'px-3 py-1 rounded text-sm font-medium transition-colors',
                  currentView === 'week'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                ]"
              >
                周视图
              </button>
              <button
                @click="currentView = 'month'"
                :class="[
                  'px-3 py-1 rounded text-sm font-medium transition-colors',
                  currentView === 'month'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                ]"
              >
                月视图
              </button>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <!-- 日期导航 -->
            <div class="flex items-center space-x-2">
              <button
                @click="navigateDate(-1)"
                class="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>
              <span class="text-lg font-semibold text-gray-900 min-w-[200px] text-center">
                {{ currentPeriod }}
              </span>
              <button
                @click="navigateDate(1)"
                class="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>
              <button
                @click="goToToday"
                class="px-3 py-1 text-sm bg-blue-100 text-blue-600 rounded hover:bg-blue-200 transition-colors"
              >
                今天
              </button>
            </div>
            <div class="text-sm text-gray-500">
              共 {{ courses.length }} 门课程
            </div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-gray-600">加载中...</p>
      </div>

      <!-- 日历视图 -->
      <div v-else class="bg-white rounded-lg shadow-sm overflow-hidden">
        <!-- 周视图 -->
        <div v-if="currentView === 'week'" class="p-6">
          <div class="grid grid-cols-8 gap-1">
            <!-- 时间轴 -->
            <div class="text-center text-sm font-medium text-gray-500 py-2">时间</div>
            <div v-for="day in weekDays" :key="day.date" class="text-center">
              <div class="text-sm font-medium text-gray-900">{{ day.name }}</div>
              <div class="text-xs text-gray-500">{{ day.date }}</div>
            </div>
            
            <!-- 时间段 -->
            <template v-for="hour in timeSlots" :key="hour">
              <div class="text-xs text-gray-500 py-2 text-right pr-2">{{ hour }}:00</div>
              <div v-for="day in weekDays" :key="`${day.date}-${hour}`" 
                   class="border border-gray-100 min-h-[60px] relative hover:bg-gray-50 cursor-pointer"
                   @click="createCourseAtTime(day.date, hour)">
                <!-- 课程卡片 -->
                <div v-for="course in getCoursesForDayHour(day.date, hour)" 
                     :key="course.id"
                     :class="[
                       'absolute inset-1 rounded p-2 text-xs cursor-pointer transition-all hover:shadow-md group',
                       getCourseColor(course.subject)
                     ]"
                     @click.stop="openCourseDetail(course)">
                  <div class="font-medium truncate">{{ course.title }}</div>
                  <div class="text-xs opacity-75 truncate">{{ course.subject }}</div>
                  <div class="text-xs opacity-75">{{ formatTime(course.start_time) }}-{{ formatTime(course.end_time) }}</div>
                  <!-- 删除按钮 -->
                  <button
                    @click.stop="deleteCourse(course)"
                    class="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600"
                    title="删除课程"
                  >
                    <svg class="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 月视图 -->
        <div v-if="currentView === 'month'" class="p-6">
          <div class="grid grid-cols-7 gap-1">
            <!-- 星期标题 -->
            <div v-for="dayName in ['周日', '周一', '周二', '周三', '周四', '周五', '周六']" 
                 :key="dayName" 
                 class="text-center text-sm font-medium text-gray-500 py-2">
              {{ dayName }}
            </div>
            
            <!-- 日期格子 -->
            <div v-for="day in monthDays" 
                 :key="day.date" 
                 :class="[
                   'border border-gray-100 min-h-[120px] p-2 cursor-pointer hover:bg-gray-50',
                   day.isCurrentMonth ? 'bg-white' : 'bg-gray-50',
                   day.isToday ? 'bg-blue-50 border-blue-200' : ''
                 ]"
                 @click="createCourseAtDate(day.date)">
              <div :class="[
                'text-sm font-medium mb-1',
                day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400',
                day.isToday ? 'text-blue-600' : ''
              ]">
                {{ day.day }}
              </div>
              
              <!-- 课程列表 -->
              <div class="space-y-1">
                <div v-for="course in getCoursesForDate(day.date)" 
                     :key="course.id"
                     :class="[
                       'text-xs p-1 rounded cursor-pointer truncate transition-all hover:shadow-sm relative group',
                       getCourseColor(course.subject)
                     ]"
                     @click.stop="openCourseDetail(course)"
                     :title="`${course.title} - ${formatTime(course.start_time)}`">
                  {{ course.title }}
                  <!-- 删除按钮 -->
                  <button
                    @click.stop="deleteCourse(course)"
                    class="absolute top-0 right-0 w-3 h-3 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600"
                    title="删除课程"
                  >
                    <svg class="w-1.5 h-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="courses.length === 0" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">暂无课程</h3>
          <p class="mt-1 text-sm text-gray-500">开始创建您的第一门课程吧</p>
          <div class="mt-6">
            <button
              @click="openCreateDialog"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              创建课程
            </button>
          </div>
        </div>
      </div>

      <!-- 创建/编辑课程模态框 -->
      <div v-if="showDialog" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
          <div class="mt-3">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-gray-900">
                {{ isEditing ? '编辑课程' : '创建课程' }}
              </h3>
              <button
                @click="closeDialog"
                class="text-gray-400 hover:text-gray-600"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            
            <form @submit.prevent="submitForm" class="space-y-6">
              <!-- 基本信息 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">课程名称 *</label>
                  <input
                    v-model="formData.title"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="请输入课程名称"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">科目 *</label>
                  <select
                    v-model="formData.subject"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">请选择科目</option>
                    <option value="数学">数学</option>
                    <option value="语文">语文</option>
                    <option value="英语">英语</option>
                    <option value="物理">物理</option>
                    <option value="化学">化学</option>
                    <option value="生物">生物</option>
                    <option value="历史">历史</option>
                    <option value="地理">地理</option>
                    <option value="政治">政治</option>
                  </select>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">级别 *</label>
                  <select
                    v-model="formData.level"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">请选择级别</option>
                    <option value="小学">小学</option>
                    <option value="初中">初中</option>
                    <option value="高中">高中</option>
                    <option value="大学">大学</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">最大人数</label>
                  <input
                    v-model.number="formData.max_students"
                    type="number"
                    min="1"
                    max="100"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="30"
                  />
                </div>
              </div>

              <!-- 时间安排 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">开始时间 *</label>
                  <input
                    v-model="formData.start_time"
                    type="datetime-local"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">结束时间 *</label>
                  <input
                    v-model="formData.end_time"
                    type="datetime-local"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">上课地点</label>
                <input
                  v-model="formData.location"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入上课地点"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">课程描述</label>
                <textarea
                  v-model="formData.description"
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入课程描述"
                ></textarea>
              </div>

              <!-- 学生选择 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">选择学生</label>
                <div class="space-y-2 max-h-40 overflow-y-auto border border-gray-300 rounded-md p-3">
                  <div v-if="loadingStudents" class="text-center py-2">
                    <div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span class="ml-2 text-sm text-gray-600">加载学生列表...</span>
                  </div>
                  <div v-else-if="availableStudents.length === 0" class="text-center py-2 text-gray-500">
                    暂无可选择的学生
                  </div>
                  <div v-else>
                    <div v-for="student in availableStudents" :key="student.id" class="flex items-center">
                      <input
                        :id="`student-${student.id}`"
                        v-model="formData.selected_students"
                        :value="student.id"
                        type="checkbox"
                        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label :for="`student-${student.id}`" class="ml-2 text-sm text-gray-700">
                        {{ student.name }} ({{ student.phone }})
                      </label>
                    </div>
                  </div>
                </div>
                <p class="mt-1 text-xs text-gray-500">
                  已选择 {{ formData.selected_students.length }} 名学生
                </p>
              </div>

              <!-- 操作按钮 -->
              <div class="flex justify-between items-center pt-6 border-t border-gray-200">
                <button
                  type="button"
                  @click="goToHome"
                  class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors flex items-center"
                >
                  <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path>
                  </svg>
                  返回首页
                </button>
                <div class="flex space-x-3">
                  <button
                    type="button"
                    @click="closeDialog"
                    class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    :disabled="submitting"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {{ submitting ? '提交中...' : (isEditing ? '更新' : '创建') }}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 学生管理模态框 -->
  <div v-if="showStudentsDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
      <div class="flex justify-between items-center p-6 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ currentCourse.title }} - 学生管理
        </h3>
        <button @click="closeStudentsDialog" class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <div class="p-6">
        <div class="mb-4">
          <p class="text-sm text-gray-600">
            已报名人数: {{ enrolledStudents.length }} / {{ currentCourse.max_students }}
          </p>
        </div>
        
        <div v-if="loadingStudents" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p class="mt-2 text-gray-600">加载中...</p>
        </div>
        
        <div v-else-if="enrolledStudents.length === 0" class="text-center py-8">
          <p class="text-gray-500">暂无学生报名</p>
        </div>
        
        <div v-else class="space-y-3">
          <div v-for="student in enrolledStudents" :key="student.id" 
               class="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div class="flex-1">
              <h4 class="font-medium text-gray-900">{{ student.student_name }}</h4>
              <p class="text-sm text-gray-600">手机号: {{ student.student_phone }}</p>
              <p class="text-sm text-gray-600">报名时间: {{ formatDateTime(student.enrollment_date) }}</p>
            </div>
            <div class="flex space-x-2">
              <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                {{ student.status === 'enrolled' ? '已报名' : student.status }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'

const router = useRouter()

// 返回上一页
const goBack = () => {
  router.back()
}

// 响应式数据
const courses = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const currentCourse = ref<any>({})
const showStudentsDialog = ref(false)
const enrolledStudents = ref<any[]>([])
const loadingStudents = ref(false)
const availableStudents = ref<any[]>([])

// 日历视图相关数据
const currentView = ref<'week' | 'month'>('week')
const currentDate = ref(new Date())
const timeSlots = ref([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])

// 表单数据
const formData = ref({
  title: '',
  subject: '',
  level: '',
  start_time: '',
  end_time: '',
  location: '',
  max_students: 30,
  description: '',
  selected_students: [] as number[]
})

// 计算属性
const currentPeriod = computed(() => {
  const date = currentDate.value
  if (currentView.value === 'week') {
    const startOfWeek = new Date(date)
    startOfWeek.setDate(date.getDate() - date.getDay())
    const endOfWeek = new Date(startOfWeek)
    endOfWeek.setDate(startOfWeek.getDate() + 6)
    return `${formatDate(startOfWeek)} - ${formatDate(endOfWeek)}`
  } else {
    return `${date.getFullYear()}年${date.getMonth() + 1}月`
  }
})

const weekDays = computed(() => {
  const date = currentDate.value
  const startOfWeek = new Date(date)
  startOfWeek.setDate(date.getDate() - date.getDay())
  
  const days = []
  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek)
    day.setDate(startOfWeek.getDate() + i)
    days.push({
      name: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][i],
      date: formatDate(day)
    })
  }
  return days
})

const monthDays = computed(() => {
  const date = currentDate.value
  const year = date.getFullYear()
  const month = date.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(firstDay.getDate() - firstDay.getDay())
  
  const days = []
  for (let i = 0; i < 42; i++) {
    const day = new Date(startDate)
    day.setDate(startDate.getDate() + i)
    const isCurrentMonth = day.getMonth() === month
    const isToday = formatDate(day) === formatDate(new Date())
    
    days.push({
      date: formatDate(day),
      day: day.getDate(),
      isCurrentMonth,
      isToday
    })
  }
  return days
})

// 生命周期
onMounted(() => {
  loadCourses()
})

// 日历视图方法
const switchView = (view: 'week' | 'month') => {
  currentView.value = view
}

const goToPrevious = () => {
  const date = new Date(currentDate.value)
  if (currentView.value === 'week') {
    date.setDate(date.getDate() - 7)
  } else {
    date.setMonth(date.getMonth() - 1)
  }
  currentDate.value = date
}

const goToNext = () => {
  const date = new Date(currentDate.value)
  if (currentView.value === 'week') {
    date.setDate(date.getDate() + 7)
  } else {
    date.setMonth(date.getMonth() + 1)
  }
  currentDate.value = date
}

const goToToday = () => {
  currentDate.value = new Date()
}

const formatDate = (date: Date) => {
  return date.toISOString().split('T')[0]
}

const getCoursesForDay = (date: string) => {
  return courses.value.filter(course => {
    const courseDate = new Date(course.start_time).toISOString().split('T')[0]
    return courseDate === date
  })
}

const getCoursesForTimeSlot = (date: string, hour: number) => {
  return courses.value.filter(course => {
    const courseDate = new Date(course.start_time)
    const courseHour = courseDate.getHours()
    const courseDateStr = courseDate.toISOString().split('T')[0]
    return courseDateStr === date && courseHour === hour
  })
}

const getCoursesForDate = (date: string) => {
  return courses.value.filter(course => {
    const courseDate = new Date(course.start_time).toISOString().split('T')[0]
    return courseDate === date
  })
}

const getCourseColor = (subject: string) => {
  const colors: { [key: string]: string } = {
    '英语': 'level-beginner',
    '数学': 'level-intermediate', 
    '物理': 'level-advanced',
    '化学': 'level-beginner',
    '生物': 'level-intermediate'
  }
  return colors[subject] || ''
}

const formatTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const openCourseDetail = (course: any) => {
  currentCourse.value = course
  openEditDialog(course)
}

const navigateDate = (direction: number) => {
  if (direction > 0) {
    goToNext()
  } else {
    goToPrevious()
  }
}

const createCourseAtTime = (date: string, hour: number) => {
  console.log('在指定时间创建课程:', date, hour)
  
  // 重置表单数据
  formData.value = {
    title: '',
    subject: '',
    level: '',
    start_time: `${date}T${hour.toString().padStart(2, '0')}:00`,
    end_time: `${date}T${(hour + 1).toString().padStart(2, '0')}:00`,
    location: '',
    max_students: 30,
    description: '',
    selected_students: []
  }
  
  isEditing.value = false
  showDialog.value = true
  loadAvailableStudents()
}

const getCoursesForDayHour = (date: string, hour: number) => {
  return getCoursesForTimeSlot(date, hour)
}

const createCourseAtDate = (date: string) => {
  console.log('在指定日期创建课程:', date)
  
  // 重置表单数据，默认设置为当天上午9点到10点
  formData.value = {
    title: '',
    subject: '',
    level: '',
    start_time: `${date}T09:00`,
    end_time: `${date}T10:00`,
    location: '',
    max_students: 30,
    description: '',
    selected_students: []
  }
  
  isEditing.value = false
  showDialog.value = true
  loadAvailableStudents()
}

// 方法
const loadCourses = async () => {
  try {
    loading.value = true
    const response = await apiService.getCourses()
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

const openCreateDialog = () => {
  console.log('=== 创建按钮被点击 ===')
  try {
    isEditing.value = false
    currentCourse.value = {}
    console.log('设置编辑状态为false')
    
    // 重置表单数据
    formData.value = {
      title: '',
      subject: '',
      level: '',
      start_time: '',
      end_time: '',
      location: '',
      max_students: 30,
      description: '',
      selected_students: []
    }
    console.log('表单数据已重置:', formData.value)
    
    // 加载学生列表
    loadAvailableStudents()
    console.log('开始加载学生列表')
    
    showDialog.value = true
    console.log('对话框状态设置为:', showDialog.value)
    console.log('=== 创建对话框打开完成 ===')
  } catch (error) {
    console.error('打开创建对话框时出错:', error)
  }
}

const openEditDialog = async (course: any) => {
  console.log('=== 编辑对话框打开开始 ===', course)
  try {
    isEditing.value = true
    currentCourse.value = course
    console.log('设置编辑模式和当前课程:', { isEditing: isEditing.value, currentCourse: currentCourse.value })
    
    formData.value = {
      title: course.title || '',
      subject: course.subject || '',
      level: course.level || '',
      start_time: course.start_time ? formatDateTimeForInput(course.start_time) : '',
      end_time: course.end_time ? formatDateTimeForInput(course.end_time) : '',
      location: course.location || '',
      max_students: course.max_students || 30,
      description: course.description || '',
      selected_students: []
    }
    console.log('表单数据已设置:', formData.value)
    
    // 加载学生列表
    await loadAvailableStudents()
    console.log('开始加载学生列表')
    
    // 加载已报名的学生并设置为选中状态
    try {
      const response = await apiService.get(`/courses/${course.id}`)
      if (response.success && response.data.course && response.data.course.students) {
        const enrolledStudentIds = response.data.course.students.map(s => s.student_id)
        formData.value.selected_students = enrolledStudentIds
        console.log('已报名学生ID列表:', enrolledStudentIds)
      }
    } catch (error) {
      console.error('加载已报名学生失败:', error)
    }
    
    showDialog.value = true
    console.log('对话框状态设置为:', showDialog.value)
    console.log('=== 编辑对话框打开完成 ===')
  } catch (error) {
    console.error('打开编辑对话框时出错:', error)
  }
}

const closeDialog = () => {
  showDialog.value = false
  isEditing.value = false
  currentCourse.value = {}
}

const goToHome = () => {
  router.push('/')
}

const submitForm = async () => {
  console.log('表单提交开始，当前表单数据:', formData.value)
  try {
    submitting.value = true
    console.log('设置提交状态为true')
    
    // 验证时间
    if (new Date(formData.value.start_time) >= new Date(formData.value.end_time)) {
      console.log('时间验证失败：开始时间必须早于结束时间')
      alert('开始时间必须早于结束时间')
      return
    }
    console.log('时间验证通过')
    
    // 转换时间格式为ISO字符串
    const submitData = {
      ...formData.value,
      start_time: new Date(formData.value.start_time).toISOString(),
      end_time: new Date(formData.value.end_time).toISOString()
    }
    console.log('准备提交的数据:', submitData)
    
    if (isEditing.value) {
      console.log('执行更新课程操作')
      const response = await apiService.updateCourse(currentCourse.value.id, submitData)
      console.log('更新课程API响应:', response)
      if (response.success) {
        console.log('更新课程成功')
        alert('更新课程成功！')
        // 编辑课程时也需要处理学生关联
        if (formData.value.selected_students.length > 0) {
          console.log('编辑课程时为选中的学生报名:', formData.value.selected_students)
          await enrollStudentsToCourse(currentCourse.value.id, formData.value.selected_students)
        }
      } else {
        console.error('更新课程失败:', response.message)
        alert('更新课程失败: ' + response.message)
        return
      }
    } else {
      console.log('执行创建课程操作')
      const response = await apiService.createCourse(submitData)
      console.log('创建课程API响应:', response)
      if (response.success) {
        console.log('创建课程成功')
        alert('创建课程成功！')
        // 如果选择了学生，自动为他们报名
        if (formData.value.selected_students.length > 0) {
          console.log('开始为选中的学生报名:', formData.value.selected_students)
          await enrollStudentsToCourse(response.data.id, formData.value.selected_students)
        }
      } else {
        console.error('创建课程失败:', response.message)
        alert('创建课程失败: ' + response.message)
        return
      }
    }
    
    console.log('关闭对话框并重新加载课程列表')
    closeDialog()
    await loadCourses()
    console.log('表单提交完成')
  } catch (error) {
    console.error('提交失败:', error)
    alert('提交失败: ' + (error.message || error))
  } finally {
    submitting.value = false
    console.log('重置提交状态为false')
  }
}

const deleteCourse = async (course: any) => {
  console.log('删除按钮被点击，课程:', course)
  
  if (!confirm(`确定要删除课程"${course.title}"吗？`)) {
    console.log('用户取消删除')
    return
  }
  
  try {
    console.log('开始删除课程，ID:', course.id)
    const response = await apiService.deleteCourse(course.id)
    console.log('删除API响应:', response)
    
    if (response.success) {
      console.log('删除课程成功')
      alert('删除课程成功！')
      await loadCourses()
    } else {
      console.error('删除课程失败:', response.message)
      alert(`删除课程失败: ${response.message}`)
    }
  } catch (error) {
    console.error('删除课程失败:', error)
    alert(`删除课程失败: ${error.message || error}`)
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

const formatDateTimeForInput = (dateTime: string) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const getStatusText = (status: string) => {
  const statusMap = {
    'active': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

// 学生管理相关方法
const viewStudents = async (course: any) => {
  currentCourse.value = course
  showStudentsDialog.value = true
  await loadEnrolledStudents(course.id)
}

const closeStudentsDialog = () => {
  showStudentsDialog.value = false
  enrolledStudents.value = []
  currentCourse.value = {}
}

const loadEnrolledStudents = async (courseId: number) => {
  try {
    loadingStudents.value = true
    const response = await apiService.get(`/courses/${courseId}`)
    if (response.success && response.data.course) {
      enrolledStudents.value = response.data.course.students || []
    } else {
      console.error('获取学生列表失败:', response.message)
      enrolledStudents.value = []
    }
  } catch (error) {
    console.error('获取学生列表失败:', error)
    enrolledStudents.value = []
  } finally {
    loadingStudents.value = false
  }
}

const loadAvailableStudents = async () => {
  try {
    console.log('=== 开始加载可用学生列表 ===')
    
    // 检查当前用户角色
    const currentUser = apiService.getCurrentUser()
    console.log('当前用户信息:', currentUser)
    
    if (!currentUser) {
      console.error('用户未登录')
      availableStudents.value = []
      return
    }
    
    if (currentUser.role !== 'teacher') {
      console.error('当前用户不是教师，无权访问学生列表')
      availableStudents.value = []
      return
    }
    
    console.log('用户角色验证通过，开始获取学生列表')
    loadingStudents.value = true
    
    // 使用正确的API方法
    const response = await apiService.getStudents()
    console.log('学生API响应:', response)
    
    if (response.success) {
      const students = response.data?.students || []
      availableStudents.value = students
      console.log('成功加载学生列表，数量:', students.length)
      console.log('学生列表详情:', students)
    } else {
      console.error('获取学生列表失败:', response.message)
      console.error('错误代码:', response.code)
      availableStudents.value = []
    }
  } catch (error) {
    console.error('获取学生列表异常:', error)
    console.error('错误详情:', error.response?.data || error.message)
    availableStudents.value = []
  } finally {
    loadingStudents.value = false
    console.log('=== 学生列表加载完成 ===')
  }
}

const enrollStudentsToCourse = async (courseId: number, studentIds: number[]) => {
  try {
    console.log('开始为学生批量报名课程:', { courseId, studentIds })
    const response = await apiService.post(`/courses/${courseId}/enroll-students`, { 
      student_ids: studentIds 
    })
    
    console.log('批量报名API响应:', response)
    
    if (response.success) {
      const { success_count, failed_count, failed_students } = response.data
      console.log(`批量报名完成: 成功${success_count}人，失败${failed_count}人`)
      
      if (failed_count > 0) {
        console.warn('部分学生报名失败:', failed_students)
        alert(`批量报名完成！成功: ${success_count}人，失败: ${failed_count}人`)
      } else {
        alert(`所有学生报名成功！共${success_count}人`)
      }
    } else {
      console.error('批量报名失败:', response.message)
      alert(`批量报名失败: ${response.message}`)
    }
  } catch (error) {
    console.error('批量报名失败:', error)
    alert(`批量报名失败: ${error.message || error}`)
  }
}

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

/* 日历视图样式 */
.calendar-view {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 周视图样式 */
.week-view {
  display: flex;
  flex-direction: column;
}

.week-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.time-label {
  padding: 12px 8px;
  font-weight: 600;
  color: #374151;
  text-align: center;
  border-right: 1px solid #e5e7eb;
}

.day-header {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  color: #374151;
  border-right: 1px solid #e5e7eb;
}

.week-body {
  display: flex;
  flex-direction: column;
}

.time-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #e5e7eb;
  min-height: 60px;
}

.time-slot {
  padding: 8px;
  border-right: 1px solid #e5e7eb;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.day-cell {
  padding: 4px;
  border-right: 1px solid #e5e7eb;
  position: relative;
}

/* 月视图样式 */
.month-view {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: #e5e7eb;
}

.month-day {
  background: white;
  min-height: 120px;
  padding: 8px;
  position: relative;
}

.month-day.other-month {
  background: #f9fafb;
  color: #9ca3af;
}

.month-day.today {
  background: #eff6ff;
}

.day-number {
  font-weight: 600;
  margin-bottom: 4px;
}

.month-day.today .day-number {
  color: #3b82f6;
}

/* 课程卡片样式 */
.course-card {
  background: #3b82f6;
  color: white;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-bottom: 2px;
  cursor: pointer;
  transition: all 0.2s;
}

.course-card:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

.course-card.level-beginner {
  background: #10b981;
}

.course-card.level-intermediate {
  background: #f59e0b;
}

.course-card.level-advanced {
  background: #ef4444;
}

.course-time {
  font-size: 10px;
  opacity: 0.9;
}

.course-subject {
  font-weight: 600;
  margin-bottom: 1px;
}
</style>