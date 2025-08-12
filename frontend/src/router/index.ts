import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'
import TeacherDashboard from '@/pages/TeacherDashboard.vue'
import StudentDashboard from '@/pages/StudentDashboard.vue'
import CourseManagement from '@/pages/CourseManagement.vue'
import QuestionManagement from '@/pages/QuestionManagement.vue'
import HomeworkManagement from '@/pages/HomeworkManagement.vue'
import StudentHomework from '@/pages/StudentHomework.vue'
import ExamManagement from '@/pages/ExamManagement.vue'
import StudentExam from '@/pages/StudentExam.vue'
import StudentManagement from '@/pages/StudentManagement.vue'
import DataStatistics from '@/pages/DataStatistics.vue'
import apiService from '@/services/api'

// 定义路由配置
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterPage,
  },
  {
    path: '/teacher/dashboard',
    name: 'teacher-dashboard',
    component: TeacherDashboard,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/course-management',
    name: 'CourseManagement',
    component: CourseManagement,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/question-management',
    name: 'QuestionManagement',
    component: QuestionManagement,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/homework-management',
    name: 'HomeworkManagement',
    component: HomeworkManagement,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student-homework',
    name: 'StudentHomework',
    component: StudentHomework,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/exam-management',
    name: 'ExamManagement',
    component: ExamManagement,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student-exam',
    name: 'StudentExam',
    component: StudentExam,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student-management',
    name: 'StudentManagement',
    component: StudentManagement,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/data-statistics',
    name: 'DataStatistics',
    component: DataStatistics,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/about',
    name: 'about',
    component: {
      template: '<div class="text-center text-xl p-8">About Page - Coming Soon</div>',
    },
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = apiService.isAuthenticated()
  const userInfo = apiService.getCurrentUser()
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // 未登录，跳转到登录页
      next('/login')
      return
    }
    
    // 检查角色权限
    if (to.meta.role && userInfo?.role !== to.meta.role) {
      // 角色不匹配，跳转到对应的仪表板
      if (userInfo?.role === 'teacher') {
        next('/teacher/dashboard')
      } else if (userInfo?.role === 'student') {
        next('/student/dashboard')
      } else {
        next('/login')
      }
      return
    }
  }
  
  // 如果已登录用户访问登录或注册页面，重定向到仪表板
  if (isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    if (userInfo?.role === 'teacher') {
      next('/teacher/dashboard')
    } else if (userInfo?.role === 'student') {
      next('/student/dashboard')
    } else {
      next()
    }
    return
  }
  
  next()
})

export default router
