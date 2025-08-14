<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import apiService from '@/services/api'

const router = useRouter()

// 表单数据
const formData = reactive({
  phone: '',
  password: ''
})

// 表单验证规则
const phoneRules = [
  { required: true, message: '请输入手机号' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
]

const passwordRules = [
  { required: true, message: '请输入密码' },
  { min: 6, message: '密码至少6位' }
]

// 登录处理
const handleLogin = async () => {
  if (!formData.phone || !formData.password) {
    showToast('请填写完整信息')
    return
  }

  const loadingToast = showLoadingToast({
    message: '登录中...',
    forbidClick: true
  })

  try {
    const response = await apiService.login({
      phone: formData.phone,
      password: formData.password
    })

    closeToast()

    if (response.success) {
      showToast('登录成功')
      // 根据用户角色跳转到不同页面
      const userInfo: any = response.data?.user
      if (userInfo?.role === 'teacher') {
        router.push('/teacher/dashboard')
      } else {
        router.push('/student/dashboard')
      }
    } else {
      showToast(response.message || '登录失败')
    }
  } catch (error: any) {
    closeToast()
    showToast(error.response?.data?.message || '登录失败，请重试')
  }
}

// 跳转到注册页面
const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="login-page min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- 顶部装饰 -->
    <div class="pt-20 pb-8 text-center">
      <div class="w-20 h-20 mx-auto mb-4 bg-blue-500 rounded-full flex items-center justify-center">
        <van-icon name="study-o" size="40" color="white" />
      </div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">英语家教教学系统</h1>
      <p class="text-gray-600">专业的英语学习管理平台</p>
    </div>

    <!-- 登录表单 -->
    <div class="px-6">
      <div class="bg-white rounded-2xl shadow-lg p-6">
        <h2 class="text-xl font-semibold text-center mb-6 text-gray-800">用户登录</h2>
        
        <van-form @submit="handleLogin">
          <van-cell-group inset>
            <van-field
              v-model="formData.phone"
              name="phone"
              label="手机号"
              placeholder="请输入手机号"
              :rules="phoneRules"
              left-icon="phone-o"
              maxlength="11"
              type="tel"
            />
            
            <van-field
              v-model="formData.password"
              name="password"
              type="password"
              label="密码"
              placeholder="请输入密码"
              :rules="passwordRules"
              left-icon="lock"
            />
          </van-cell-group>

          <div class="mt-6 space-y-4">
            <van-button
              type="primary"
              size="large"
              block
              round
              native-type="submit"
              class="bg-blue-500 border-blue-500"
            >
              登录
            </van-button>
            
            <van-button
              type="default"
              size="large"
              block
              round
              @click="goToRegister"
              class="text-blue-500 border-blue-500"
            >
              注册新账号
            </van-button>
          </div>
        </van-form>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="mt-8 text-center text-gray-500 text-sm px-6">
      <p>测试账号：</p>
      <p>教师：13800138001 / 123456</p>
      <p>学生：13800138002 / 123456</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
}
</style>