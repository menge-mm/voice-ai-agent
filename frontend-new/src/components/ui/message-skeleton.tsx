import { cn } from '@/lib/utils'

type MessageSkeletonProps = {
  role?: 'user' | 'assistant'
  className?: string
}

/**
 * MessageSkeleton - Loading skeleton for chat messages
 * Matches the MessageBubble component layout
 */
export function MessageSkeleton({
  role = 'assistant',
  className,
}: MessageSkeletonProps) {
  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start',
        className
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-3 space-y-2',
          isUser ? 'bg-primary/10' : 'bg-muted'
        )}
      >
        {/* Message content skeleton */}
        <div className="space-y-2">
          <div className="h-4 bg-foreground/10 rounded animate-pulse w-3/4" />
          <div className="h-4 bg-foreground/10 rounded animate-pulse w-full" />
          <div className="h-4 bg-foreground/10 rounded animate-pulse w-5/6" />
        </div>
        {/* Timestamp skeleton */}
        <div className="h-3 bg-foreground/10 rounded animate-pulse w-16" />
      </div>
    </div>
  )
}
