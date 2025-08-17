<template>
  <div class="not-found-view">
    <div class="min-h-screen flex items-center justify-center bg-gray-50">
      <div class="max-w-md w-full text-center">
        <div class="mb-8">
          <h1 class="text-9xl font-bold text-blue-600">404</h1>
          <h2 class="text-2xl font-semibold text-gray-900 mt-4">页面未找到</h2>
          <p class="text-gray-600 mt-2">抱歉，您访问的页面不存在或已被移除。</p>
        </div>
        
        <div class="space-y-4">
          <button 
            @click="goBack" 
            class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回上一页
          </button>
          
          <button 
            @click="goHome" 
            class="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            回到首页
          </button>
        </div>
        
        <div class="mt-8">
          <svg class="mx-auto h-32 w-32 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.29-1.009-5.674-2.64C7.85 10.723 9.8 9 12 9s4.15 1.723 5.674 3.36A7.963 7.963 0 0112 15z" />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

const goHome = () => {
  router.push('/')
}
</script>