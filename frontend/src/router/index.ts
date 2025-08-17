import { createRouter, createWebHistory } from "vue-router"
import type { RouteRecordRaw } from "vue-router"
import { useAuthStore } from "../stores/auth"

// 导入页面组件
import HomeView from "../views/HomeView.vue"

// 定义路由
const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "home",
    component: HomeView,
    meta: { requiresAuth: false }
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../views/auth/LoginView.vue"),
    meta: { requiresAuth: false }
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/auth/RegisterView.vue"),
    meta: { requiresAuth: false }
  },
  {
    path: "/dashboard",
    name: "dashboard",
    component: () => import("../views/DashboardView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/courses",
    name: "courses",
    component: () => import("../views/course/CourseListView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/assignments",
    name: "assignments",
    component: () => import("../views/assignment/AssignmentListView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/exercises",
    name: "exercises",
    component: () => import("../views/exercise/ExerciseListView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/profile",
    name: "profile",
    component: () => import("../views/user/ProfileView.vue"),
    meta: { requiresAuth: true }
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/AboutView.vue"),
    meta: { requiresAuth: false }
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../views/NotFoundView.vue"),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫 - 认证检查
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    // 如果用户未认证，重定向到登录页
    if (!authStore.isAuthenticated) {
      next({
        name: 'login',
        query: { redirect: to.fullPath } // 保存原始路径用于登录后重定向
      })
      return
    }
    
    // 如果有token但用户信息为空，尝试获取用户信息
    if (authStore.token && !authStore.user) {
      try {
        await authStore.fetchUser()
      } catch (error) {
        console.error('Failed to fetch user info:', error)
        // 如果获取用户信息失败，清除认证状态并重定向到登录页
        authStore.logout()
        next({
          name: 'login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
  }
  
  // 如果用户已认证且访问登录或注册页，重定向到仪表板
  if (authStore.isAuthenticated && (to.name === 'login' || to.name === 'register')) {
    const redirectPath = (to.query.redirect as string) || '/dashboard'
    next(redirectPath)
    return
  }
  
  next()
})

export default router
