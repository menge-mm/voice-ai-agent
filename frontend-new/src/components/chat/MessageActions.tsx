import { EditIcon, RefreshCwIcon, CopyIcon, CheckIcon } from 'lucide-react'
import { useState } from 'react'
import { useRegenerateMessage } from '@/queries'
import type { Message } from '@/types'
import { cn } from '@/lib/utils'

type MessageActionsProps = {
  message: Message
  onEditStart?: () => void
  isRegenerating?: boolean
}

/**
 * MessageActions - Action buttons for messages
 *
 * Features:
 * - Copy message content
 * - Edit user messages
 * - Regenerate AI responses
 * - Smooth hover transitions
 */
export function MessageActions({
  message,
  onEditStart,
  isRegenerating = false,
}: MessageActionsProps) {
  const [copied, setCopied] = useState(false)
  const regenerateMessage = useRegenerateMessage()
  const isUser = message.role === 'user'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const handleRegenerate = async () => {
    try {
      await regenerateMessage.mutateAsync({
        conversationId: message.conversationId,
        messageId: message.id,
      })
    } catch (error) {
      console.error('Failed to regenerate:', error)
    }
  }

  return (
    <div className={cn('flex items-center gap-1', isUser && 'justify-end')}>
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="p-1.5 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Copy message"
        title="Copy message"
      >
        {copied ? (
          <CheckIcon className="size-3.5 text-green-500" />
        ) : (
          <CopyIcon className="size-3.5" />
        )}
      </button>

      {/* Edit button (user messages only) */}
      {isUser && onEditStart && (
        <button
          onClick={onEditStart}
          className="p-1.5 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Edit message"
          title="Edit message"
        >
          <EditIcon className="size-3.5" />
        </button>
      )}

      {/* Regenerate button (assistant messages only) */}
      {!isUser && (
        <button
          onClick={handleRegenerate}
          disabled={isRegenerating || regenerateMessage.isPending}
          className={cn(
            "p-1.5 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors",
            (isRegenerating || regenerateMessage.isPending) && "opacity-50 cursor-not-allowed"
          )}
          aria-label="Regenerate response"
          title="Regenerate response"
        >
          <RefreshCwIcon
            className={cn(
              "size-3.5",
              (isRegenerating || regenerateMessage.isPending) && "animate-spin"
            )}
          />
        </button>
      )}
    </div>
  )
}
