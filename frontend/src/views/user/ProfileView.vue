<template>
  <div class="profile-view">
    <div class="max-w-4xl mx-auto p-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-8">个人资料</h1>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center space-x-6 mb-6">
          <div class="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {{ userInitial }}
          </div>
          <div>
            <h2 class="text-2xl font-semibold text-gray-900">{{ user?.name || '用户' }}</h2>
            <p class="text-gray-600">{{ user?.email }}</p>
            <span class="inline-block px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full mt-2">
              {{ roleText }}
            </span>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">姓名</label>
            <input 
              v-model="profileForm.name" 
              type="text" 
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
            <input 
              v-model="profileForm.email" 
              type="email" 
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">电话</label>
            <input 
              v-model="profileForm.phone" 
              type="tel" 
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">角色</label>
            <input 
              :value="roleText" 
              type="text" 
              disabled 
              class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
            >
          </div>
        </div>
        
        <div class="mt-6 flex justify-end space-x-4">
          <button 
            @click="resetForm" 
            class="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            重置
          </button>
          <button 
            @click="updateProfile" 
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            保存更改
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useAppStore } from '../../stores/app'

const authStore = useAuthStore()
const appStore = useAppStore()

const user = computed(() => authStore.user)

const profileForm = ref({
  name: '',
  email: '',
  phone: ''
})

const userInitial = computed(() => {
  return user.value?.name?.charAt(0).toUpperCase() || 'U'
})

const roleText = computed(() => {
  const roleMap = {
    student: '学生',
    teacher: '教师',
    admin: '管理员'
  }
  return roleMap[user.value?.role || 'student']
})

const resetForm = () => {
  if (user.value) {
    profileForm.value = {
      name: user.value.name,
      email: user.value.email,
      phone: user.value.phone || ''
    }
  }
}

const updateProfile = async () => {
  try {
    // TODO: 实现更新用户资料的API调用
    appStore.addNotification({
      type: 'success',
      title: '成功',
      message: '个人资料更新成功'
    })
  } catch (error) {
    appStore.addNotification({
      type: 'error',
      title: '错误',
      message: '更新个人资料失败'
    })
  }
}

onMounted(() => {
  resetForm()
})
</script>