import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * UI Store - Manages UI state (sidebar, mobile)
 *
 * Tracks UI-related state like sidebar collapse and mobile detection
 * Persists sidebar preference to localStorage
 */
interface UIStore {
  isSidebarCollapsed: boolean
  isMobile: boolean
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setIsMobile: (isMobile: boolean) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      isSidebarCollapsed: false,
      isMobile: false,

      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

      setSidebarCollapsed: (collapsed) =>
        set({ isSidebarCollapsed: collapsed }),

      setIsMobile: (isMobile) => set({ isMobile }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({ isSidebarCollapsed: state.isSidebarCollapsed }),
    }
  )
)
