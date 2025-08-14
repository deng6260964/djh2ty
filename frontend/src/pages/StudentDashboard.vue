<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import apiService from '@/services/api'

const router = useRouter()

// 用户信息
const userInfo = ref(apiService.getCurrentUser())

// 学习数据
const learningData = reactive({
  totalCourses: 0,
  completedAssignments: 0,
  pendingAssignments: 0,
  averageScore: 0,
  studyDays: 0
})

// 最近课程
const recentCourses = ref([])

// 待完成作业
const pendingAssignments = ref([])

// 最近考试
const recentExams = ref([])

// 快捷功能
const quickFeatures = [
  {
    icon: 'apps-o',
    title: '课程中心',
    color: '#1989fa',
    path: '/student/courses'
  },
  {
    icon: 'todo-list-o',
    title: '作业中心',
    color: '#07c160',
    path: '/student-homework'
  },
  {
    icon: 'certificate',
    title: '考试中心',
    color: '#ff976a',
    path: '/student-exam'
  },
  {
    icon: 'bar-chart-o',
    title: '学习报告',
    color: '#8b5cf6',
    path: '/data-statistics'
  }
]

// 获取学习数据
const fetchLearningData = async () => {
  try {
    console.log('开始获取学习数据，用户信息:', userInfo.value)
    if (userInfo.value?.id) {
      console.log('调用API获取学生进度，学生ID:', userInfo.value.id)
      const response = await apiService.getStudentProgress(userInfo.value.id)
      console.log('API响应:', response)
      if (response.success && response.data) {
        // 映射后端数据结构到前端数据结构
        const data = response.data
        learningData.totalCourses = data.course_progress?.total || 0
        learningData.completedAssignments = data.homework_progress?.graded || 0
        learningData.pendingAssignments = data.homework_progress?.pending || 0
        
        // 计算平均分（作业和考试的平均）
        const homeworkTotal = data.homework_progress?.total || 0
        const examTotal = data.exam_progress?.total || 0
        const totalTasks = homeworkTotal + examTotal
        const completedTasks = (data.homework_progress?.graded || 0) + (data.exam_progress?.graded || 0)
        learningData.averageScore = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
        
        // 计算学习天数（简化处理）
        learningData.studyDays = Math.max(learningData.totalCourses * 7, 1)
        
        console.log('学习数据更新成功:', learningData)
      } else {
        console.warn('API响应失败或无数据:', response)
      }
    } else {
      console.warn('用户信息不存在或缺少ID')
    }
  } catch (error) {
    console.error('获取学习数据失败:', error)
    showToast('获取学习数据失败')
  }
}

// 获取最近课程
const fetchRecentCourses = async () => {
  try {
    console.log('开始获取最近课程')
    const response = await apiService.getCourses({ limit: 3 })
    console.log('课程API响应:', response)
    if (response.success && response.data) {
      recentCourses.value = response.data
      console.log('课程数据更新成功:', recentCourses.value)
    } else {
      console.warn('课程API响应失败或无数据:', response)
    }
  } catch (error) {
    console.error('获取课程失败:', error)
    showToast('获取课程失败')
  }
}

// 获取待完成作业
const fetchPendingAssignments = async () => {
  try {
    console.log('开始获取待完成作业')
    const response = await apiService.getHomeworks({ status: 'pending', limit: 3 })
    console.log('作业API响应:', response)
    if (response.success && response.data) {
      pendingAssignments.value = response.data
      console.log('作业数据更新成功:', pendingAssignments.value)
    } else {
      console.warn('作业API响应失败或无数据:', response)
    }
  } catch (error) {
    console.error('获取作业失败:', error)
    showToast('获取作业失败')
  }
}

// 退出登录
const handleLogout = () => {
  apiService.logout()
}

// 快捷功能点击
const handleQuickFeature = (feature) => {
  router.push(feature.path)
}

// 底部导航栏
const activeTab = ref(0)

// 页面初始化
onMounted(() => {
  fetchLearningData()
  fetchRecentCourses()
  fetchPendingAssignments()
})
</script>

<template>
  <div class="student-dashboard min-h-screen bg-gray-50">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      title="学习中心"
      left-text="退出"
      left-arrow
      @click-left="handleLogout"
      class="bg-gradient-to-r from-purple-500 to-pink-500 text-white"
    >
      <template #right>
        <van-icon name="bell-o" size="18" @click="router.push('/student/notifications')" />
      </template>
    </van-nav-bar>

    <!-- 用户信息卡片 -->
    <div class="p-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex items-center space-x-3">
          <van-image
            :src="userInfo?.avatar_url || 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=student%20avatar%20young%20friendly&image_size=square'"
            width="60"
            height="60"
            round
            class="border-2 border-purple-200"
          />
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-800">{{ userInfo?.name }}</h3>
            <p class="text-gray-500 text-sm">{{ userInfo?.phone }}</p>
            <div class="flex items-center mt-1">
              <van-tag type="success">学生</van-tag>
              <span class="ml-2 text-xs text-gray-400">已学习 {{ learningData.studyDays }} 天</span>
            </div>
          </div>
          <van-icon name="arrow" size="16" color="#c8c9cc" />
        </div>
      </div>
    </div>

    <!-- 学习数据 -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <h4 class="text-lg font-semibold mb-4 text-gray-800">学习概览</h4>
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-purple-500">{{ learningData.totalCourses }}</div>
            <div class="text-sm text-gray-500 mt-1">学习课程</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-green-500">{{ learningData.completedAssignments }}</div>
            <div class="text-sm text-gray-500 mt-1">完成作业</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-500">{{ learningData.pendingAssignments }}</div>
            <div class="text-sm text-gray-500 mt-1">待完成</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-500">{{ learningData.averageScore }}%</div>
            <div class="text-sm text-gray-500 mt-1">平均分</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷功能 -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <h4 class="text-lg font-semibold mb-4 text-gray-800">快捷功能</h4>
        <div class="grid grid-cols-2 gap-4">
          <div
            v-for="feature in quickFeatures"
            :key="feature.title"
            @click="handleQuickFeature(feature)"
            class="flex items-center p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div 
              class="w-10 h-10 rounded-full flex items-center justify-center mr-3"
              :style="{ backgroundColor: feature.color + '20' }"
            >
              <van-icon :name="feature.icon" size="20" :color="feature.color" />
            </div>
            <span class="text-sm text-gray-700 font-medium">{{ feature.title }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 待完成作业 -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-lg font-semibold text-gray-800">待完成作业</h4>
          <van-button type="primary" size="mini" plain @click="router.push('/student/assignments')">
            查看全部
          </van-button>
        </div>
        
        <div v-if="pendingAssignments.length === 0" class="text-center py-6">
          <van-empty description="暂无待完成作业" />
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="assignment in pendingAssignments"
            :key="assignment.id"
            @click="router.push(`/student/assignments/${assignment.id}`)"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
          >
            <div class="flex-1">
              <h5 class="font-medium text-gray-800">{{ assignment.title }}</h5>
              <p class="text-sm text-gray-500 mt-1">截止时间：{{ assignment.due_date }}</p>
            </div>
            <van-tag type="warning">待完成</van-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近课程 -->
    <div class="px-4 pb-20">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-lg font-semibold text-gray-800">我的课程</h4>
          <van-button type="primary" size="mini" plain @click="router.push('/student/courses')">
            查看全部
          </van-button>
        </div>
        
        <div v-if="recentCourses.length === 0" class="text-center py-6">
          <van-empty description="暂无课程" />
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="course in recentCourses"
            :key="course.id"
            @click="router.push(`/student/courses/${course.id}`)"
            class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
          >
            <van-image
              :src="course.cover_image || 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=english%20course%20book%20education&image_size=square'"
              width="50"
              height="50"
              round
            />
            <div class="flex-1">
              <h5 class="font-medium text-gray-800">{{ course.name }}</h5>
              <p class="text-sm text-gray-500 mt-1">{{ course.description }}</p>
            </div>
            <van-icon name="arrow" size="16" color="#c8c9cc" />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航栏 -->
    <van-tabbar v-model="activeTab" fixed>
      <van-tabbar-item icon="wap-home-o" to="/student/dashboard">首页</van-tabbar-item>
      <van-tabbar-item icon="apps-o" to="/student/courses">课程</van-tabbar-item>
      <van-tabbar-item icon="todo-list-o" to="/student/assignments">作业</van-tabbar-item>
      <van-tabbar-item icon="certificate" to="/student/exams">考试</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/student/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>



<style scoped>
.student-dashboard {
  padding-bottom: 50px;
}

.van-nav-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.van-nav-bar :deep(.van-nav-bar__title) {
  color: white;
}

.van-nav-bar :deep(.van-nav-bar__left) {
  color: white;
}
</style>