<template>
  <div class="exercise-list-view">
    <div class="max-w-7xl mx-auto p-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">练习列表</h1>
        <p class="text-gray-600 mt-2">通过练习巩固您的学习成果</p>
      </div>
      
      <!-- 筛选和搜索 -->
      <div class="mb-6 flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索练习..."
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
            v-model="selectedDifficulty"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有难度</option>
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </div>
        <div class="sm:w-48">
          <select
            v-model="selectedType"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有类型</option>
            <option value="multiple_choice">选择题</option>
            <option value="coding">编程题</option>
            <option value="essay">问答题</option>
          </select>
        </div>
      </div>
      
      <!-- 练习网格 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" v-if="filteredExercises.length > 0">
        <div
          v-for="exercise in filteredExercises"
          :key="exercise.id"
          class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
        >
          <!-- 练习头部 -->
          <div class="p-6">
            <div class="flex items-center justify-between mb-3">
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getDifficultyClass(exercise.difficulty)">
                {{ getDifficultyText(exercise.difficulty) }}
              </span>
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getTypeClass(exercise.type)">
                {{ getTypeText(exercise.type) }}
              </span>
            </div>
            
            <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ exercise.title }}</h3>
            <p class="text-gray-600 mb-4 line-clamp-2">{{ exercise.description }}</p>
            
            <!-- 练习统计 -->
            <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
              <div class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {{ exercise.timeLimit }} 分钟
              </div>
              <div class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {{ exercise.questions }} 题
              </div>
              <div class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                </svg>
                {{ exercise.points }} 分
              </div>
            </div>
            
            <!-- 完成状态 -->
            <div v-if="exercise.completed" class="mb-4">
              <div class="flex items-center justify-between text-sm mb-2">
                <span class="text-gray-600">最佳成绩</span>
                <span class="font-medium" :class="getScoreClass(exercise.bestScore || 0, exercise.points)">
                  {{ exercise.bestScore }}/{{ exercise.points }}
                </span>
              </div>
              <div class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                完成时间：{{ formatDate(exercise.completedAt || '') }}
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex gap-2">
              <button
                @click="startExercise(exercise.id)"
                class="flex-1 px-4 py-2 rounded-lg transition-colors duration-200"
                :class="exercise.completed ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-blue-600 text-white hover:bg-blue-700'"
              >
                {{ exercise.completed ? '重新练习' : '开始练习' }}
              </button>
              <button
                @click="viewExerciseDetails(exercise.id)"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                详情
              </button>
            </div>
            
            <!-- 查看历史记录按钮 -->
            <button
              v-if="exercise.completed"
              @click="viewHistory(exercise.id)"
              class="w-full mt-2 px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
            >
              查看历史记录
            </button>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">没有找到练习</h3>
        <p class="mt-1 text-sm text-gray-500">尝试调整搜索条件或筛选选项</p>
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
const selectedDifficulty = ref('')
const selectedType = ref('')

// 模拟练习数据
const exercises = ref([
  {
    id: '1',
    title: 'Vue组件基础',
    description: '测试Vue组件的基本概念和使用方法',
    difficulty: 'easy',
    type: 'multiple_choice',
    timeLimit: 30,
    questions: 10,
    points: 100,
    completed: true,
    bestScore: 85,
    completedAt: '2024-01-15T14:30:00'
  },
  {
    id: '2',
    title: 'TypeScript类型系统',
    description: '深入理解TypeScript的类型系统和高级特性',
    difficulty: 'medium',
    type: 'coding',
    timeLimit: 60,
    questions: 5,
    points: 150,
    completed: true,
    bestScore: 120,
    completedAt: '2024-01-18T16:45:00'
  },
  {
    id: '3',
    title: 'React Hooks实践',
    description: '通过编程练习掌握React Hooks的使用',
    difficulty: 'medium',
    type: 'coding',
    timeLimit: 45,
    questions: 8,
    points: 120,
    completed: false,
    bestScore: null,
    completedAt: null
  },
  {
    id: '4',
    title: '算法设计与分析',
    description: '分析和设计常见算法，解决复杂问题',
    difficulty: 'hard',
    type: 'essay',
    timeLimit: 90,
    questions: 3,
    points: 200,
    completed: false,
    bestScore: null,
    completedAt: null
  },
  {
    id: '5',
    title: 'JavaScript基础语法',
    description: '测试JavaScript基础语法和概念理解',
    difficulty: 'easy',
    type: 'multiple_choice',
    timeLimit: 20,
    questions: 15,
    points: 75,
    completed: true,
    bestScore: 70,
    completedAt: '2024-01-12T10:20:00'
  },
  {
    id: '6',
    title: 'Node.js API开发',
    description: '使用Node.js开发RESTful API接口',
    difficulty: 'hard',
    type: 'coding',
    timeLimit: 120,
    questions: 4,
    points: 180,
    completed: false,
    bestScore: null,
    completedAt: null
  }
])

const filteredExercises = computed(() => {
  return exercises.value.filter(exercise => {
    const matchesSearch = exercise.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         exercise.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesDifficulty = !selectedDifficulty.value || exercise.difficulty === selectedDifficulty.value
    const matchesType = !selectedType.value || exercise.type === selectedType.value
    return matchesSearch && matchesDifficulty && matchesType
  })
})

const getDifficultyClass = (difficulty: string) => {
  switch (difficulty) {
    case 'easy':
      return 'bg-green-100 text-green-800'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800'
    case 'hard':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getDifficultyText = (difficulty: string) => {
  switch (difficulty) {
    case 'easy':
      return '简单'
    case 'medium':
      return '中等'
    case 'hard':
      return '困难'
    default:
      return '未知'
  }
}

const getTypeClass = (type: string) => {
  switch (type) {
    case 'multiple_choice':
      return 'bg-blue-100 text-blue-800'
    case 'coding':
      return 'bg-purple-100 text-purple-800'
    case 'essay':
      return 'bg-indigo-100 text-indigo-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getTypeText = (type: string) => {
  switch (type) {
    case 'multiple_choice':
      return '选择题'
    case 'coding':
      return '编程题'
    case 'essay':
      return '问答题'
    default:
      return '未知'
  }
}

const getScoreClass = (score: number, total: number) => {
  const percentage = (score / total) * 100
  if (percentage >= 90) return 'text-green-600'
  if (percentage >= 70) return 'text-yellow-600'
  return 'text-red-600'
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

const startExercise = (exerciseId: string) => {
  router.push(`/exercises/${exerciseId}/start`)
}

const viewExerciseDetails = (exerciseId: string) => {
  router.push(`/exercises/${exerciseId}/details`)
}

const viewHistory = (exerciseId: string) => {
  router.push(`/exercises/${exerciseId}/history`)
}

onMounted(() => {
  // 这里可以加载实际的练习数据
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>