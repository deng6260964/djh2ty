<template>
  <div class="course-list-view">
    <div class="max-w-7xl mx-auto p-6">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">课程列表</h1>
        <p class="text-gray-600 mt-2">浏览和管理您的课程</p>
      </div>
      
      <!-- 搜索和筛选 -->
      <div class="mb-6 flex flex-col sm:flex-row gap-4">
        <div class="flex-1">
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索课程..."
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
            v-model="selectedCategory"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有分类</option>
            <option value="frontend">前端开发</option>
            <option value="backend">后端开发</option>
            <option value="mobile">移动开发</option>
            <option value="ai">人工智能</option>
          </select>
        </div>
      </div>
      
      <!-- 课程网格 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" v-if="filteredCourses.length > 0">
        <div
          v-for="course in filteredCourses"
          :key="course.id"
          class="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
        >
          <!-- 课程图片 -->
          <div class="h-48 bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
            <svg class="w-16 h-16 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
            </svg>
          </div>
          
          <!-- 课程信息 -->
          <div class="p-6">
            <div class="flex items-center justify-between mb-2">
              <span class="px-2 py-1 text-xs font-medium rounded-full" :class="getCategoryClass(course.category)">
                {{ getCategoryName(course.category) }}
              </span>
              <span class="text-sm text-gray-500">{{ course.duration }}</span>
            </div>
            
            <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ course.title }}</h3>
            <p class="text-gray-600 mb-4 line-clamp-2">{{ course.description }}</p>
            
            <!-- 进度条 -->
            <div class="mb-4">
              <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>进度</span>
                <span>{{ course.progress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  :style="{ width: course.progress + '%' }"
                ></div>
              </div>
            </div>
            
            <!-- 课程统计 -->
            <div class="flex items-center justify-between text-sm text-gray-500 mb-4">
              <div class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                </svg>
                {{ course.students }} 学生
              </div>
              <div class="flex items-center">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                {{ course.lessons }} 课时
              </div>
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex gap-2">
              <button
                @click="enterCourse(course.id)"
                class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200"
              >
                {{ course.progress > 0 ? '继续学习' : '开始学习' }}
              </button>
              <button
                @click="viewCourseDetails(course.id)"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                详情
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">没有找到课程</h3>
        <p class="mt-1 text-sm text-gray-500">尝试调整搜索条件或分类筛选</p>
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
const selectedCategory = ref('')

// 模拟课程数据
const courses = ref([
  {
    id: '1',
    title: 'Vue.js 基础教程',
    description: '从零开始学习Vue.js框架，掌握现代前端开发技能',
    category: 'frontend',
    duration: '8小时',
    progress: 75,
    students: 1234,
    lessons: 24
  },
  {
    id: '2',
    title: 'TypeScript 进阶',
    description: '深入学习TypeScript高级特性，提升代码质量',
    category: 'frontend',
    duration: '12小时',
    progress: 45,
    students: 856,
    lessons: 32
  },
  {
    id: '3',
    title: 'Node.js 后端开发',
    description: '使用Node.js构建高性能的后端应用程序',
    category: 'backend',
    duration: '16小时',
    progress: 0,
    students: 2341,
    lessons: 48
  },
  {
    id: '4',
    title: 'React Native 移动开发',
    description: '使用React Native开发跨平台移动应用',
    category: 'mobile',
    duration: '20小时',
    progress: 30,
    students: 567,
    lessons: 56
  },
  {
    id: '5',
    title: '机器学习入门',
    description: '学习机器学习基础概念和常用算法',
    category: 'ai',
    duration: '24小时',
    progress: 15,
    students: 789,
    lessons: 64
  }
])

const filteredCourses = computed(() => {
  return courses.value.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         course.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesCategory = !selectedCategory.value || course.category === selectedCategory.value
    return matchesSearch && matchesCategory
  })
})

const getCategoryClass = (category: string) => {
  switch (category) {
    case 'frontend':
      return 'bg-blue-100 text-blue-800'
    case 'backend':
      return 'bg-green-100 text-green-800'
    case 'mobile':
      return 'bg-purple-100 text-purple-800'
    case 'ai':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const getCategoryName = (category: string) => {
  switch (category) {
    case 'frontend':
      return '前端开发'
    case 'backend':
      return '后端开发'
    case 'mobile':
      return '移动开发'
    case 'ai':
      return '人工智能'
    default:
      return '其他'
  }
}

const enterCourse = (courseId: string) => {
  router.push(`/courses/${courseId}`)
}

const viewCourseDetails = (courseId: string) => {
  router.push(`/courses/${courseId}/details`)
}

onMounted(() => {
  // 这里可以加载实际的课程数据
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