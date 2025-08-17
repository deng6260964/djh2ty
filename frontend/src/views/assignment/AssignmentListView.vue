<template>
  <div class="assignment-list-view">
    <div class="max-w-7xl mx-auto p-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">作业列表</h1>
        <p class="text-gray-600 mt-2">管理和提交您的作业</p>
      </div>
      
      <!-- 筛选和搜索 -->
      <div class="mb-6 flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索作业..."
              class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
          </div>
        </div>
        <div class="sm:w-48">
          <select
            v-model="selectedStatus"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有状态</option>
            <option value="pending">待提交</option>
            <option value="submitted">已提交</option>
            <option value="graded">已评分</option>
            <option value="overdue">已逾期</option>
          </select>
        </div>
      </div>
      
      <!-- 作业列表 -->
      <div class="space-y-4" v-if="filteredAssignments.length > 0">
        <div
          v-for="assignment in filteredAssignments"
          :key="assignment.id"
          class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300"
        >
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <!-- 作业信息 -->
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="text-xl font-semibold text-gray-900">{{ assignment.title }}</h3>
                <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getStatusClass(assignment.status)">
                  {{ getStatusText(assignment.status) }}
                </span>
                <span v-if="assignment.priority === 'high'" class="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                  高优先级
                </span>
              </div>
              
              <p class="text-gray-600 mb-3">{{ assignment.description }}</p>
              
              <div class="flex flex-wrap gap-4 text-sm text-gray-500">
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                  </svg>
                  {{ assignment.courseName }}
                </div>
                <div class="flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  截止时间：{{ formatDate(assignment.dueDate) }}
                </div>
                <div v-if="assignment.submittedAt" class="flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  提交时间：{{ formatDate(assignment.submittedAt) }}
                </div>
                <div v-if="assignment.score !== null" class="flex items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                  </svg>
                  得分：{{ assignment.score }}/{{ assignment.maxScore }}
                </div>
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="mt-4 lg:mt-0 lg:ml-6 flex flex-col sm:flex-row gap-2">
              <button
                v-if="assignment.status === 'pending'"
                @click="startAssignment(assignment.id)"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                开始作业
              </button>
              <button
                v-else-if="assignment.status === 'submitted'"
                @click="viewSubmission(assignment.id)"
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200"
              >
                查看提交
              </button>
              <button
                v-else-if="assignment.status === 'graded'"
                @click="viewGrade(assignment.id)"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors duration-200"
              >
                查看成绩
              </button>
              <button
                v-else-if="assignment.status === 'overdue'"
                @click="viewAssignment(assignment.id)"
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
              >
                查看详情
              </button>
              
              <button
                @click="viewAssignmentDetails(assignment.id)"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                详情
              </button>
            </div>
          </div>
          
          <!-- 进度条（仅对进行中的作业显示） -->
          <div v-if="assignment.status === 'pending' && assignment.progress > 0" class="mt-4">
            <div class="flex justify-between text-sm text-gray-600 mb-1">
              <span>完成进度</span>
              <span>{{ assignment.progress }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: assignment.progress + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">没有找到作业</h3>
        <p class="mt-1 text-sm text-gray-500">尝试调整搜索条件或状态筛选</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../../stores/app'

const router = useRouter()
const appStore = useAppStore()

const searchQuery = ref('')
const selectedStatus = ref('')

// 模拟作业数据
const assignments = ref([
  {
    id: '1',
    title: 'Vue组件开发实践',
    description: '创建一个可复用的Vue组件，包含props、events和slots的使用',
    courseName: 'Vue.js 基础教程',
    dueDate: '2024-01-20T23:59:59',
    status: 'pending',
    priority: 'high',
    progress: 25,
    submittedAt: null,
    score: null,
    maxScore: 100
  },
  {
    id: '2',
    title: 'TypeScript类型定义',
    description: '为现有JavaScript项目添加TypeScript类型定义',
    courseName: 'TypeScript 进阶',
    dueDate: '2024-01-22T23:59:59',
    status: 'submitted',
    priority: 'medium',
    progress: 100,
    submittedAt: '2024-01-21T15:30:00',
    score: null,
    maxScore: 100
  },
  {
    id: '3',
    title: 'API接口设计',
    description: '设计RESTful API接口，包含用户认证和数据CRUD操作',
    courseName: 'Node.js 后端开发',
    dueDate: '2024-01-25T23:59:59',
    status: 'graded',
    priority: 'medium',
    progress: 100,
    submittedAt: '2024-01-24T10:15:00',
    score: 85,
    maxScore: 100
  },
  {
    id: '4',
    title: '移动端UI设计',
    description: '使用React Native设计移动端用户界面',
    courseName: 'React Native 移动开发',
    dueDate: '2024-01-15T23:59:59',
    status: 'overdue',
    priority: 'low',
    progress: 60,
    submittedAt: null,
    score: null,
    maxScore: 100
  },
  {
    id: '5',
    title: '数据分析报告',
    description: '使用机器学习算法分析数据集并生成报告',
    courseName: '机器学习入门',
    dueDate: '2024-01-28T23:59:59',
    status: 'pending',
    priority: 'medium',
    progress: 0,
    submittedAt: null,
    score: null,
    maxScore: 100
  }
])

const filteredAssignments = computed(() => {
  return assignments.value.filter(assignment => {
    const matchesSearch = assignment.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         assignment.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         assignment.courseName.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesStatus = !selectedStatus.value || assignment.status === selectedStatus.value
    return matchesSearch && matchesStatus
  })
})

const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'submitted':
      return 'bg-blue-100 text-blue-800'
    case 'graded':
      return 'bg-green-100 text-green-800'
    case 'overdue':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending':
      return '待提交'
    case 'submitted':
      return '已提交'
    case 'graded':
      return '已评分'
    case 'overdue':
      return '已逾期'
    default:
      return '未知'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const startAssignment = (assignmentId: string) => {
  router.push(`/assignments/${assignmentId}/work`)
}

const viewSubmission = (assignmentId: string) => {
  router.push(`/assignments/${assignmentId}/submission`)
}

const viewGrade = (assignmentId: string) => {
  router.push(`/assignments/${assignmentId}/grade`)
}

const viewAssignment = (assignmentId: string) => {
  router.push(`/assignments/${assignmentId}`)
}

const viewAssignmentDetails = (assignmentId: string) => {
  router.push(`/assignments/${assignmentId}/details`)
}

onMounted(() => {
  // 这里可以加载实际的作业数据
})
</script>