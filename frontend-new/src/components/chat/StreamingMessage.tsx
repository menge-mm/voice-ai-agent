import { BotIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ThinkingBlock } from '@/components/thinking/ThinkingBlock'
import { MarkdownRenderer } from '@/components/markdown/MarkdownRenderer'
import { useSettingsStore } from '@/stores'
import type { ThinkingNode } from '@/types'

type StreamingMessageProps = {
  messageId: string
  content: string
  thinking?: ThinkingNode[]
}

/**
 * StreamingMessage - Real-time streaming message display
 *
 * Shows AI message as it's being generated with thinking process
 */
export function StreamingMessage({
  messageId: _messageId,
  content,
  thinking = [],
}: StreamingMessageProps) {
  const showThinking = useSettingsStore((state) => state.showThinking)
  const hasThinking = thinking && thinking.length > 0

  return (
    <div
      className={cn(
        'flex gap-3 group relative',
        'animate-in fade-in slide-in-from-bottom-2 duration-300'
      )}
    >
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center ring-1 ring-primary/10">
        <BotIcon className="size-4 text-primary" />
      </div>

      {/* Message content */}
      <div className="flex flex-col gap-2.5 flex-1 min-w-0">
        {/* Thinking process - shown during streaming */}
        {showThinking && hasThinking && (
          <div className="w-full animate-in fade-in slide-in-from-top-1 duration-200">
            <ThinkingBlock nodes={thinking} defaultExpanded={true} />
          </div>
        )}

        {/* Streaming content */}
        <div className="rounded-2xl px-4 py-3 w-full bg-muted/50 text-foreground shadow-sm">
          {content ? (
            <div className="text-sm leading-relaxed">
              <MarkdownRenderer content={content} />
            </div>
          ) : (
            // Empty state - waiting for content
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-xs text-primary/90 font-medium">Generating...</span>
            </div>
          )}

          {/* Cursor indicator at end of content */}
          {content && (
            <span className="inline-block w-1 h-4 bg-primary/60 animate-pulse ml-0.5 align-text-bottom" />
          )}
        </div>
      </div>
    </div>
  )
}
