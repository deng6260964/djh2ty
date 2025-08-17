import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useAppStore } from './stores/app'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 应用初始化逻辑
async function initializeApp() {
  const authStore = useAuthStore()
  const appStore = useAppStore()
  
  // 初始化应用状态
  await appStore.initializeApp()
  
  // 恢复用户认证状态
  const token = localStorage.getItem('auth_token')
  if (token) {
    authStore.token = token
    try {
      await authStore.fetchUser()
    } catch (error) {
      console.warn('Failed to restore user session:', error)
      // 清除无效的token
      localStorage.removeItem('auth_token')
      authStore.logout()
    }
  }
}

// 初始化应用并挂载
initializeApp().then(() => {
  app.mount('#app')
}).catch((error) => {
  console.error('Failed to initialize app:', error)
  // 即使初始化失败也要挂载应用
  app.mount('#app')
})
