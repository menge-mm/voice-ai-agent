import { useRef, useCallback } from 'react'

interface UseAutoResizeTextareaOptions {
  minHeight?: number
  maxHeight?: number
}

interface UseAutoResizeTextareaReturn {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
  adjustHeight: (reset?: boolean) => void
}

/**
 * useAutoResizeTextarea - Auto-resize textarea hook
 *
 * Automatically adjusts textarea height based on content
 * Supports min/max height constraints
 */
export function useAutoResizeTextarea({
  minHeight = 72,
  maxHeight = 300,
}: UseAutoResizeTextareaOptions = {}): UseAutoResizeTextareaReturn {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const adjustHeight = useCallback(
    (reset = false) => {
      const textarea = textareaRef.current
      if (!textarea) return

      if (reset) {
        // Reset to min height
        textarea.style.height = `${minHeight}px`
        return
      }

      // Reset height to auto to get correct scrollHeight
      textarea.style.height = 'auto'

      // Calculate new height
      const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)

      // Set new height
      textarea.style.height = `${newHeight}px`

      // Set overflow based on whether content exceeds maxHeight
      textarea.style.overflowY = newHeight >= maxHeight ? 'auto' : 'hidden'
    },
    [minHeight, maxHeight]
  )

  return {
    textareaRef,
    adjustHeight,
  }
}
