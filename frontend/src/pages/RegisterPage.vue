<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import apiService from '@/services/api'

const router = useRouter()

// 表单数据
const formData = reactive({
  phone: '',
  password: '',
  confirmPassword: '',
  name: '',
  role: 'student' as 'teacher' | 'student',
  inviteCode: ''
})

const showRolePicker = ref(false)

// 角色选项
const roleOptions = [
  { text: '学生', value: 'student' },
  { text: '教师', value: 'teacher' }
]

// 表单验证规则
const phoneRules = [
  { required: true, message: '请输入手机号' },
  { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
]

const passwordRules = [
  { required: true, message: '请输入密码' },
  { min: 6, message: '密码至少6位' }
]

const nameRules = [
  { required: true, message: '请输入姓名' },
  { min: 2, message: '姓名至少2位' }
]

// 注册处理
const handleRegister = async () => {
  // 表单验证
  if (!formData.phone || !formData.password || !formData.name) {
    showToast('请填写完整信息')
    return
  }

  if (formData.password !== formData.confirmPassword) {
    showToast('两次输入的密码不一致')
    return
  }

  if (formData.role === 'teacher' && !formData.inviteCode) {
    showToast('教师注册需要邀请码')
    return
  }

  const loadingToast = showLoadingToast({
    message: '注册中...',
    forbidClick: true
  })

  try {
    const response = await apiService.register({
      phone: formData.phone,
      password: formData.password,
      name: formData.name,
      role: formData.role,
      invite_code: formData.inviteCode || undefined
    })

    closeToast()

    if (response.success) {
      showToast('注册成功，请登录')
      router.push('/login')
    } else {
      showToast(response.message || '注册失败')
    }
  } catch (error: any) {
    closeToast()
    showToast(error.response?.data?.message || '注册失败，请重试')
  }
}

// 返回登录页面
const goToLogin = () => {
  router.push('/login')
}

// 角色选择确认
const onRoleConfirm = ({ selectedOptions }: { selectedOptions: any }) => {
  formData.role = selectedOptions[0].value
  showRolePicker.value = false
}
</script>

<template>
  <div class="register-page min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
    <!-- 顶部装饰 -->
    <div class="pt-16 pb-6 text-center">
      <div class="w-20 h-20 mx-auto mb-4 bg-green-500 rounded-full flex items-center justify-center">
        <van-icon name="add-square" size="40" color="white" />
      </div>
      <h1 class="text-2xl font-bold text-gray-800 mb-2">注册新账号</h1>
      <p class="text-gray-600">加入英语学习大家庭</p>
    </div>

    <!-- 注册表单 -->
    <div class="px-6">
      <div class="bg-white rounded-2xl shadow-lg p-6">
        <van-form @submit="handleRegister">
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
              v-model="formData.name"
              name="name"
              label="姓名"
              placeholder="请输入真实姓名"
              :rules="nameRules"
              left-icon="contact"
            />
            
            <van-field
              v-model="formData.password"
              name="password"
              type="password"
              label="密码"
              placeholder="请输入密码（至少6位）"
              :rules="passwordRules"
              left-icon="lock"
            />
            
            <van-field
              v-model="formData.confirmPassword"
              name="confirmPassword"
              type="password"
              label="确认密码"
              placeholder="请再次输入密码"
              left-icon="lock"
            />
            
            <van-field
              v-model="formData.role"
              is-link
              readonly
              name="role"
              label="身份"
              placeholder="请选择身份"
              left-icon="manager-o"
              @click="showRolePicker = true"
            />
            
            <van-field
              v-if="formData.role === 'teacher'"
              v-model="formData.inviteCode"
              name="inviteCode"
              label="邀请码"
              placeholder="请输入教师邀请码"
              left-icon="coupon-o"
            />
          </van-cell-group>

          <div class="mt-6 space-y-4">
            <van-button
              type="primary"
              size="large"
              block
              round
              native-type="submit"
              class="bg-green-500 border-green-500"
            >
              注册
            </van-button>
            
            <van-button
              type="default"
              size="large"
              block
              round
              @click="goToLogin"
              class="text-green-500 border-green-500"
            >
              已有账号，去登录
            </van-button>
          </div>
        </van-form>
      </div>
    </div>

    <!-- 角色选择器 -->
    <van-popup v-model:show="showRolePicker" position="bottom">
      <van-picker
        :columns="roleOptions"
        @confirm="onRoleConfirm"
        @cancel="showRolePicker = false"
      />
    </van-popup>

    <!-- 底部提示 -->
    <div class="mt-6 text-center text-gray-500 text-sm px-6">
      <p>教师邀请码请联系管理员获取</p>
      <p>学生可直接注册</p>
    </div>
  </div>
</template>



<style scoped>
.register-page {
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(34, 197, 94, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(16, 185, 129, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 40%, rgba(5, 150, 105, 0.3) 0%, transparent 50%);
}
</style>