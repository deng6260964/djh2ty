import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { getToken, setToken, removeToken } from '../api/client'

export interface AuthUser {
  id: number
  username?: string
  role: string
  display_name: string
  student_id?: number
}

interface AuthState {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (token: string, user: AuthUser) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: !!getToken(),

      login: (token: string, user: AuthUser) => {
        setToken(token)
        set({ user, isAuthenticated: true })
      },

      logout: () => {
        removeToken()
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'student-auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ user: state.user }),
    }
  )
)
