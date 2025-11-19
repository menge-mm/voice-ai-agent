import { create } from 'zustand'
import type { StreamState } from '@/types'

/**
 * Chat Store - Manages streaming state
 *
 * Handles real-time streaming of messages from the backend,
 * tracking the current streaming conversation and message
 */
interface ChatStore {
  streamState: StreamState | null
  setStreamState: (state: StreamState | null) => void
  resetStreamState: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  streamState: null,

  setStreamState: (state) => set({ streamState: state }),

  resetStreamState: () => set({ streamState: null }),
}))
