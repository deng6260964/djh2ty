<template>
  <div class="dashboard-view">
    <div class="max-w-7xl mx-auto p-6">
      <!-- 欢迎区域 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">欢迎回来，{{ user?.name }}！</h1>
        <p class="text-gray-600 mt-2">这是您的学习仪表板</p>
      </div>
      
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
              </svg>
            </div>
            <div class="ml-4">
              <h3 class="text-lg font-semibold text-gray-900">课程总数</h3>
              <p class="text-2xl font-bold text-blue-600">{{ stats.totalCourses }}</p>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-green-100 text-green-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div class="ml-4">
              <h3 class="text-lg font-semibold text-gray-900">已完成作业</h3>
              <p class="text-2xl font-bold text-green-600">{{ stats.completedAssignments }}</p>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <div class="ml-4">
              <h3 class="text-lg font-semibold text-gray-900">待完成作业</h3>
              <p class="text-2xl font-bold text-yellow-600">{{ stats.pendingAssignments }}</p>
            </div>
          </div>
        </div>
        
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <div class="ml-4">
              <h3 class="text-lg font-semibold text-gray-900">练习次数</h3>
              <p class="text-2xl font-bold text-purple-600">{{ stats.exerciseCount }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 最近活动 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- 最近课程 -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">最近课程</h2>
          <div class="space-y-4">
            <div v-for="course in recentCourses" :key="course.id" class="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
              <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                </svg>
              </div>
              <div class="ml-4 flex-1">
                <h3 class="font-medium text-gray-900">{{ course.title }}</h3>
                <p class="text-sm text-gray-500">{{ course.description }}</p>
              </div>
              <div class="text-sm text-gray-400">{{ course.progress }}%</div>
            </div>
          </div>
          <div class="mt-4">
            <router-link to="/courses" class="text-blue-600 hover:text-blue-500 text-sm font-medium">
              查看所有课程 →
            </router-link>
          </div>
        </div>
        
        <!-- 待办事项 -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">待办事项</h2>
          <div class="space-y-4">
            <div v-for="todo in todoList" :key="todo.id" class="flex items-center p-4 border border-gray-200 rounded-lg">
              <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div class="ml-4 flex-1">
                <h3 class="font-medium text-gray-900">{{ todo.title }}</h3>
                <p class="text-sm text-gray-500">截止时间：{{ todo.dueDate }}</p>
              </div>
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getPriorityClass(todo.priority)">
                {{ todo.priority }}
              </span>
            </div>
          </div>
          <div class="mt-4">
            <router-link to="/assignments" class="text-blue-600 hover:text-blue-500 text-sm font-medium">
              查看所有作业 →
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const user = computed(() => authStore.user)

// 模拟数据
const stats = ref({
  totalCourses: 8,
  completedAssignments: 12,
  pendingAssignments: 3,
  exerciseCount: 45
})

const recentCourses = ref([
  {
    id: '1',
    title: 'Vue.js 基础教程',
    description: '学习Vue.js框架的基础知识',
    progress: 75
  },
  {
    id: '2',
    title: 'TypeScript 进阶',
    description: '深入学习TypeScript高级特性',
    progress: 45
  },
  {
    id: '3',
    title: '前端工程化',
    description: '现代前端开发工具链',
    progress: 30
  }
])

const todoList = ref([
  {
    id: '1',
    title: 'Vue组件作业',
    dueDate: '2024-01-20',
    priority: '高'
  },
  {
    id: '2',
    title: 'TypeScript练习',
    dueDate: '2024-01-22',
    priority: '中'
  },
  {
    id: '3',
    title: '项目实战',
    dueDate: '2024-01-25',
    priority: '低'
  }
])

const getPriorityClass = (priority: string) => {
  switch (priority) {
    case '高':
      return 'bg-red-100 text-red-800'
    case '中':
      return 'bg-yellow-100 text-yellow-800'
    case '低':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

onMounted(() => {
  // 这里可以加载实际的仪表板数据
})
</script>