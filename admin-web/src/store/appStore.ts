import { create } from 'zustand'

interface AppState {
  sidebarCollapsed: boolean
  unreadNotifications: number
  setSidebarCollapsed: (collapsed: boolean) => void
  setUnreadNotifications: (count: number) => void
  toggleSidebar: () => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  unreadNotifications: 0,

  setSidebarCollapsed: (collapsed: boolean) => {
    set({ sidebarCollapsed: collapsed })
  },

  setUnreadNotifications: (count: number) => {
    set({ unreadNotifications: count })
  },

  toggleSidebar: () => {
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }))
  },
}))
