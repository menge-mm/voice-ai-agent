import { useRef, useState, useCallback } from 'react'

interface UseTTSReturn {
  playAudio: (audioUrl: string) => Promise<void>
  stopAudio: () => void
  isPlaying: boolean
  currentAudioUrl: string | null
}

/**
 * useTTS - Text-to-Speech audio playback hook
 *
 * Manages audio playback for TTS-generated responses
 * Handles play/pause/stop and tracks playing state
 */
export function useTTS(): UseTTSReturn {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const playAudio = useCallback(async (audioUrl: string) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
      }

      // Create new audio element if needed
      if (!audioRef.current) {
        audioRef.current = new Audio()
      }

      // Set up event listeners
      audioRef.current.onended = () => {
        setIsPlaying(false)
        setCurrentAudioUrl(null)
      }

      audioRef.current.onerror = () => {
        setIsPlaying(false)
        setCurrentAudioUrl(null)
        console.error('Failed to play audio')
      }

      // Start playback
      audioRef.current.src = audioUrl
      await audioRef.current.play()

      setIsPlaying(true)
      setCurrentAudioUrl(audioUrl)
    } catch (error) {
      console.error('Failed to play audio:', error)
      setIsPlaying(false)
      setCurrentAudioUrl(null)
    }
  }, [])

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
    }
    setIsPlaying(false)
    setCurrentAudioUrl(null)
  }, [])

  return {
    playAudio,
    stopAudio,
    isPlaying,
    currentAudioUrl,
  }
}
