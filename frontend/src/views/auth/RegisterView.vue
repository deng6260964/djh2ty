<template>
  <div class="register-view">
    <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div class="max-w-md w-full space-y-8">
        <div>
          <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
            创建新账户
          </h2>
          <p class="mt-2 text-center text-sm text-gray-600">
            或者
            <router-link to="/login" class="font-medium text-blue-600 hover:text-blue-500">
              登录已有账户
            </router-link>
          </p>
        </div>
        
        <form class="mt-8 space-y-6" @submit.prevent="handleRegister">
          <div class="space-y-4">
            <div>
              <label for="name" class="block text-sm font-medium text-gray-700">姓名</label>
              <input
                id="name"
                v-model="form.name"
                name="name"
                type="text"
                autocomplete="name"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="请输入您的姓名"
              >
            </div>
            
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700">邮箱地址</label>
              <input
                id="email"
                v-model="form.email"
                name="email"
                type="email"
                autocomplete="email"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="请输入邮箱地址"
              >
            </div>
            
            <div>
              <label for="password" class="block text-sm font-medium text-gray-700">密码</label>
              <input
                id="password"
                v-model="form.password"
                name="password"
                type="password"
                autocomplete="new-password"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="请输入密码（至少6位）"
              >
            </div>
            
            <div>
              <label for="confirmPassword" class="block text-sm font-medium text-gray-700">确认密码</label>
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                name="confirmPassword"
                type="password"
                autocomplete="new-password"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="请再次输入密码"
              >
            </div>
            
            <div>
              <label for="role" class="block text-sm font-medium text-gray-700">角色</label>
              <select
                id="role"
                v-model="form.role"
                name="role"
                required
                class="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="student">学生</option>
                <option value="teacher">教师</option>
              </select>
            </div>
          </div>

          <div class="flex items-center">
            <input
              id="agree-terms"
              v-model="form.agreeTerms"
              name="agree-terms"
              type="checkbox"
              required
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            >
            <label for="agree-terms" class="ml-2 block text-sm text-gray-900">
              我同意
              <a href="#" class="text-blue-600 hover:text-blue-500">服务条款</a>
              和
              <a href="#" class="text-blue-600 hover:text-blue-500">隐私政策</a>
            </label>
          </div>

          <div>
            <button
              type="submit"
              :disabled="isLoading || !isFormValid"
              class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
                <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </span>
              {{ isLoading ? '注册中...' : '注册' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import type { RegisterRequest } from '../../types/user'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const isLoading = ref(false)

const form = ref<RegisterRequest & { confirmPassword: string; agreeTerms: boolean }>({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'student',
  agreeTerms: false
})

const isFormValid = computed(() => {
  return (
    form.value.name.trim() &&
    form.value.email.trim() &&
    form.value.password.length >= 6 &&
    form.value.password === form.value.confirmPassword &&
    form.value.agreeTerms
  )
})

const handleRegister = async () => {
  if (isLoading.value || !isFormValid.value) return
  
  isLoading.value = true
  
  try {
    await authStore.register({
      name: form.value.name,
      email: form.value.email,
      password: form.value.password,
      role: form.value.role
    })
    
    appStore.addNotification({
      type: 'success',
      title: '注册成功',
      message: '欢迎加入智能学习平台！'
    })
    
    // 注册成功后跳转到仪表板
    router.push('/dashboard')
    
  } catch (error: any) {
    appStore.addNotification({
      type: 'error',
      title: '注册失败',
      message: error.message || '注册过程中发生错误'
    })
  } finally {
    isLoading.value = false
  }
}
</script>