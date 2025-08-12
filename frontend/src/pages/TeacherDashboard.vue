<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import apiService from '@/services/api'

const router = useRouter()

// 用户信息
const userInfo = ref(apiService.getCurrentUser())

// 统计数据
const statistics = reactive({
  totalStudents: 0,
  totalCourses: 0,
  totalQuestions: 0,
  totalAssignments: 0,
  pendingGrading: 0
})

// 最近活动
const recentActivities = ref([])

// 快捷操作菜单
const quickActions = [
  {
    icon: 'plus',
    title: '创建课程',
    color: '#1989fa',
    path: '/course-management'
  },
  {
    icon: 'edit',
    title: '题目管理',
    color: '#07c160',
    path: '/question-management'
  },
  {
    icon: 'todo-list-o',
    title: '布置作业',
    color: '#ff976a',
    path: '/homework-management'
  },
  {
    icon: 'medal-o',
    title: '创建考试',
    color: '#ed4014',
    path: '/exam-management'
  },
  {
    icon: 'friends-o',
    title: '学生管理',
    color: '#8b5cf6',
    path: '/student-management'
  },
  {
    icon: 'bar-chart-o',
    title: '数据统计',
    color: '#06b6d4',
    path: '/data-statistics'
  }
]

// 获取统计数据
const fetchStatistics = async () => {
  try {
    const response = await apiService.getTeachingStatistics()
    if (response.success && response.data) {
      Object.assign(statistics, response.data)
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 退出登录
const handleLogout = () => {
  apiService.logout()
}

// 快捷操作点击
const handleQuickAction = (action) => {
  router.push(action.path)
}

// 底部导航栏
const activeTab = ref(0)

// 页面初始化
onMounted(() => {
  fetchStatistics()
})
</script>

<template>
  <div class="teacher-dashboard min-h-screen bg-gray-50">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      title="教师工作台"
      left-text="退出"
      left-arrow
      @click-left="handleLogout"
      class="bg-blue-500 text-white"
    >
      <template #right>
        <van-icon name="setting-o" size="18" @click="router.push('/teacher/settings')" />
      </template>
    </van-nav-bar>

    <!-- 用户信息卡片 -->
    <div class="p-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex items-center space-x-3">
          <van-image
            :src="userInfo?.avatar_url || 'https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=teacher%20avatar%20professional%20friendly&image_size=square'"
            width="60"
            height="60"
            round
            class="border-2 border-blue-200"
          />
          <div class="flex-1">
            <h3 class="text-lg font-semibold text-gray-800">{{ userInfo?.name }}</h3>
            <p class="text-gray-500 text-sm">{{ userInfo?.phone }}</p>
            <div class="flex items-center mt-1">
              <van-tag type="primary">教师</van-tag>
            </div>
          </div>
          <van-icon name="arrow" size="16" color="#c8c9cc" />
        </div>
      </div>
    </div>

    <!-- 统计数据 -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <h4 class="text-lg font-semibold mb-4 text-gray-800">数据概览</h4>
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-500">{{ statistics.totalStudents }}</div>
            <div class="text-sm text-gray-500 mt-1">学生总数</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-green-500">{{ statistics.totalCourses }}</div>
            <div class="text-sm text-gray-500 mt-1">课程数量</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-500">{{ statistics.totalQuestions }}</div>
            <div class="text-sm text-gray-500 mt-1">题目总数</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-red-500">{{ statistics.pendingGrading }}</div>
            <div class="text-sm text-gray-500 mt-1">待批改</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="px-4 pb-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <h4 class="text-lg font-semibold mb-4 text-gray-800">快捷操作</h4>
        <div class="grid grid-cols-3 gap-4">
          <div
            v-for="action in quickActions"
            :key="action.title"
            @click="handleQuickAction(action)"
            class="flex flex-col items-center p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div 
              class="w-12 h-12 rounded-full flex items-center justify-center mb-2"
              :style="{ backgroundColor: action.color + '20' }"
            >
              <van-icon :name="action.icon" size="24" :color="action.color" />
            </div>
            <span class="text-sm text-gray-700 text-center">{{ action.title }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="px-4 pb-20">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-lg font-semibold text-gray-800">最近活动</h4>
          <van-button type="primary" size="mini" plain @click="router.push('/teacher/activities')">
            查看全部
          </van-button>
        </div>
        
        <div v-if="recentActivities.length === 0" class="text-center py-8">
          <van-empty description="暂无最近活动" />
        </div>
        
        <div v-else class="space-y-3">
          <div
            v-for="activity in recentActivities.slice(0, 5)"
            :key="activity.id"
            class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg"
          >
            <van-icon name="clock-o" size="16" color="#969799" />
            <div class="flex-1">
              <p class="text-sm text-gray-800">{{ activity.description }}</p>
              <p class="text-xs text-gray-500 mt-1">{{ activity.time }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航栏 -->
    <van-tabbar v-model="activeTab" fixed>
      <van-tabbar-item icon="wap-home-o" to="/teacher/dashboard">首页</van-tabbar-item>
      <van-tabbar-item icon="apps-o" to="/teacher/courses">课程</van-tabbar-item>
      <van-tabbar-item icon="edit" to="/teacher/questions">题目</van-tabbar-item>
      <van-tabbar-item icon="friends-o" to="/teacher/students">学生</van-tabbar-item>
      <van-tabbar-item icon="user-o" to="/teacher/profile">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>



<style scoped>
.teacher-dashboard {
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