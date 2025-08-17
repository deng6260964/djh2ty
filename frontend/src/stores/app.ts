import { defineStore } from "pinia"

export interface AppState {
  isLoading: boolean
  isMobile: boolean
  sidebarOpen: boolean
  theme: "light" | "dark"
  language: "zh" | "en"
  notifications: Notification[]
}

export interface Notification {
  id: string
  type: "success" | "error" | "warning" | "info"
  title: string
  message: string
  duration?: number
  timestamp: Date
  read?: boolean
}

export const useAppStore = defineStore("app", {
  state: (): AppState => ({
    isLoading: false,
    isMobile: false,
    sidebarOpen: false,
    theme: (localStorage.getItem("theme") as "light" | "dark") || "light",
    language: (localStorage.getItem("language") as "zh" | "en") || "zh",
    notifications: []
  }),

  getters: {
    unreadNotifications: (state) => state.notifications.filter(n => !n.read),
    notificationCount: (state) => state.notifications.filter(n => !n.read).length
  },

  actions: {
    setLoading(loading: boolean) {
      this.isLoading = loading
    },

    setMobile(mobile: boolean) {
      this.isMobile = mobile
    },

    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen
    },

    setSidebarOpen(open: boolean) {
      this.sidebarOpen = open
    },

    setTheme(theme: "light" | "dark") {
      this.theme = theme
      localStorage.setItem("theme", theme)
      document.documentElement.classList.toggle("dark", theme === "dark")
    },

    setLanguage(language: "zh" | "en") {
      this.language = language
      localStorage.setItem("language", language)
    },

    addNotification(notification: Omit<Notification, "id" | "timestamp" | "read">) {
      const newNotification: Notification = {
        ...notification,
        id: Date.now().toString(),
        timestamp: new Date(),
        read: false
      }
      this.notifications.unshift(newNotification)
      
      // 自动移除通知
      if (notification.duration !== 0) {
        setTimeout(() => {
          this.removeNotification(newNotification.id)
        }, notification.duration || 5000)
      }
    },

    removeNotification(id: string) {
      const index = this.notifications.findIndex(n => n.id === id)
      if (index > -1) {
        this.notifications.splice(index, 1)
      }
    },

    clearNotifications() {
      this.notifications = []
    },

    initializeApp() {
      // 检测移动设备
      this.setMobile(window.innerWidth < 768)
      
      // 应用主题
      document.documentElement.classList.toggle("dark", this.theme === "dark")
      
      // 监听窗口大小变化
      window.addEventListener("resize", () => {
        this.setMobile(window.innerWidth < 768)
        if (window.innerWidth >= 768) {
          this.setSidebarOpen(false)
        }
      })
    }
  }
})
