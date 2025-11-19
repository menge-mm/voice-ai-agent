import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Settings Store - User preferences
 *
 * Manages user preferences like message timestamps, thinking display, and TTS
 * Persists all settings to localStorage
 */
interface SettingsStore {
  messageTimestamps: boolean
  showThinking: boolean
  ttsEnabled: boolean  // NEW: TTS toggle state
  setMessageTimestamps: (show: boolean) => void
  setShowThinking: (show: boolean) => void
  setTtsEnabled: (enabled: boolean) => void
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      messageTimestamps: false,
      showThinking: true,
      ttsEnabled: false,  // TTS off by default

      setMessageTimestamps: (show) => set({ messageTimestamps: show }),

      setShowThinking: (show) => set({ showThinking: show }),

      setTtsEnabled: (enabled) => set({ ttsEnabled: enabled }),
    }),
    {
      name: 'settings-storage',
    }
  )
)
