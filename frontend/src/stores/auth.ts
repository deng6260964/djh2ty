import { defineStore } from "pinia"
import type { User } from "../types/user"
import { authApi } from "../services/api"

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem("token"),
    isAuthenticated: false,
    isLoading: false,
    error: null
  }),

  getters: {
    userRole: (state) => state.user?.role,
    isStudent: (state) => state.user?.role === "student",
    isTeacher: (state) => state.user?.role === "teacher",
    isAdmin: (state) => state.user?.role === "admin"
  },

  actions: {
    async login(email: string, password: string) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await authApi.login({ email, password })
        this.token = response.token
        this.user = response.user
        this.isAuthenticated = true
        
        localStorage.setItem("token", response.token)
        return response
      } catch (error: any) {
        this.error = error.message || "登录失败"
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async register(userData: any) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await authApi.register(userData)
        return response
      } catch (error: any) {
        this.error = error.message || "注册失败"
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async logout() {
      try {
        await authApi.logout()
      } catch (error) {
        console.error("Logout error:", error)
      } finally {
        this.user = null
        this.token = null
        this.isAuthenticated = false
        localStorage.removeItem("token")
      }
    },

    async fetchUser() {
      if (!this.token) return
      
      this.isLoading = true
      try {
        const user = await authApi.getProfile()
        this.user = user
        this.isAuthenticated = true
      } catch (error) {
        this.logout()
      } finally {
        this.isLoading = false
      }
    },

    clearError() {
      this.error = null
    }
  }
})
