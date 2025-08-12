<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import { showToast } from 'vant'

const router = useRouter()
const isAuthenticated = ref(false)
const userInfo = ref<any>(null)

onMounted(() => {
  checkAuthStatus()
})

const checkAuthStatus = () => {
  isAuthenticated.value = apiService.isAuthenticated()
  if (isAuthenticated.value) {
    userInfo.value = apiService.getCurrentUser()
  }
}

const goToLogin = () => {
  router.push('/login')
}

const goToRegister = () => {
  router.push('/register')
}

const goToDashboard = () => {
  if (userInfo.value?.role === 'teacher') {
    router.push('/teacher/dashboard')
  } else if (userInfo.value?.role === 'student') {
    router.push('/student/dashboard')
  }
}

const logout = async () => {
  try {
    await apiService.logout()
    showToast('退出登录成功')
    isAuthenticated.value = false
    userInfo.value = null
  } catch (error) {
    showToast('退出登录失败')
  }
}
</script>

<template>
  <div class="home-page">
    <!-- 头部 -->
    <van-nav-bar title="英语家教教学管理系统" />
    
    <!-- 主要内容 -->
    <div class="content">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="logo">
          <van-icon name="study-o" size="60" color="#1989fa" />
        </div>
        <h1 class="title">英语家教教学管理系统</h1>
        <p class="subtitle">专业的英语教学管理平台</p>
      </div>
      
      <!-- 功能介绍 -->
      <div class="features">
        <van-grid :column-num="2" :gutter="16">
          <van-grid-item>
            <van-icon name="friends-o" size="24" />
            <span class="feature-text">师生管理</span>
          </van-grid-item>
          <van-grid-item>
            <van-icon name="bookmark-o" size="24" />
            <span class="feature-text">课程管理</span>
          </van-grid-item>
          <van-grid-item>
            <van-icon name="edit" size="24" />
            <span class="feature-text">题目管理</span>
          </van-grid-item>
          <van-grid-item>
            <van-icon name="todo-list-o" size="24" />
            <span class="feature-text">作业考试</span>
          </van-grid-item>
        </van-grid>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <template v-if="!isAuthenticated">
          <van-button type="primary" size="large" block @click="goToLogin">
            立即登录
          </van-button>
          <van-button type="default" size="large" block @click="goToRegister" class="mt-3">
            注册账号
          </van-button>
        </template>
        <template v-else>
          <div class="user-info">
            <van-cell-group>
              <van-cell :title="userInfo?.name" :label="userInfo?.role === 'teacher' ? '教师' : '学生'">
                <template #icon>
                  <van-icon name="user-o" />
                </template>
              </van-cell>
            </van-cell-group>
          </div>
          <van-button type="primary" size="large" block @click="goToDashboard" class="mt-4">
            进入{{ userInfo?.role === 'teacher' ? '教师' : '学生' }}工作台
          </van-button>
          <van-button type="default" size="large" block @click="logout" class="mt-3">
            退出登录
          </van-button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: calc(100vh - 46px);
}

.welcome-section {
  text-align: center;
  margin-top: 60px;
  margin-bottom: 40px;
}

.logo {
  margin-bottom: 20px;
}

.title {
  font-size: 24px;
  font-weight: bold;
  color: white;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0;
}

.features {
  width: 100%;
  max-width: 300px;
  margin-bottom: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.feature-text {
  display: block;
  margin-top: 8px;
  font-size: 14px;
  color: white;
}

.actions {
  width: 100%;
  max-width: 300px;
  margin-top: auto;
  margin-bottom: 40px;
}

.user-info {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.mt-3 {
  margin-top: 12px;
}

.mt-4 {
  margin-top: 16px;
}

:deep(.van-nav-bar) {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

:deep(.van-nav-bar__title) {
  color: white;
}

:deep(.van-grid-item__content) {
  background: transparent;
  color: white;
  flex-direction: column;
  padding: 16px 8px;
}

:deep(.van-cell) {
  background: transparent;
  color: white;
}

:deep(.van-cell__title) {
  color: white;
}

:deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.7);
}
</style>
