import { useAuthStore } from '../store/authStore'
import { getToken } from '../api/client'

export const useAuth = () => {
  const { user, isAuthenticated, login, logout } = useAuthStore()

  const checkAuth = (): boolean => {
    const token = getToken()
    return !!token && isAuthenticated
  }

  return {
    user,
    isAuthenticated: checkAuth(),
    login,
    logout,
  }
}
