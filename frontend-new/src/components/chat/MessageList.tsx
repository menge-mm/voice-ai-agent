import { useMessages } from '@/queries'
import { useChatStore } from '@/stores'
import { EmptyState } from '@/components/ui/empty-state'
import { MessageSkeleton } from '@/components/ui/message-skeleton'
import { ChatMessage } from './ChatMessage'
import { StreamingMessage } from './StreamingMessage'
import { MessageSquareIcon, SparklesIcon } from 'lucide-react'
import { Activity } from 'react'
import { ChatContainerRoot, ChatContainerContent, ChatContainerScrollAnchor } from '@/components/prompt-kit/chat-container'

type MessageListProps = {
  conversationId: string
}

/**
 * MessageList - Professional message display with StickToBottom
 *
 * Design: Matches ChatGPT/Claude/prompt-kit standards
 * - Centered content with max-width
 * - Professional auto-scroll using use-stick-to-bottom library
 * - Instant initial scroll, smooth resize behavior
 * - Professional welcome screen
 * - Smooth animations
 */
export function MessageList({ conversationId }: MessageListProps) {
  const { data, isLoading, error } = useMessages(conversationId)
  const streamState = useChatStore((state) => state.streamState)

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="w-full max-w-3xl space-y-6">
          <MessageSkeleton role="user" />
          <MessageSkeleton role="assistant" />
          <MessageSkeleton role="user" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <EmptyState
          icon={MessageSquareIcon}
          title="Failed to load messages"
          description="Please try again later"
        />
      </div>
    )
  }

  // Empty state - professional welcome like ChatGPT
  if (!data || data.data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Activity mode="visible">
          <div className="w-full max-w-2xl space-y-8 text-center animate-in fade-in duration-500">
            {/* Welcome icon */}
            <div className="flex justify-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 ring-1 ring-primary/20">
                <SparklesIcon className="size-12 text-primary" />
              </div>
            </div>

            {/* Welcome message */}
            <div className="space-y-3">
              <h2 className="text-3xl font-bold tracking-tight">How can I help you today?</h2>
              <p className="text-muted-foreground">
                Start a conversation by sending a message below
              </p>
            </div>
          </div>
        </Activity>
      </div>
    )
  }

  // Check if streaming for this conversation
  const isStreamingHere =
    streamState?.isStreaming &&
    streamState.conversationId === conversationId &&
    streamState.messageId

  return (
    <ChatContainerRoot className="h-full">
      <ChatContainerContent className="mx-auto w-full max-w-3xl px-4 pt-6 pb-36 space-y-6">
        {/* Messages */}
        {data.data.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {/* Streaming message */}
        {isStreamingHere && (
          <StreamingMessage
            messageId={streamState.messageId!}
            content={streamState.content}
            thinking={streamState.thinking}
          />
        )}

        {/* Scroll anchor - automatically handled by StickToBottom */}
        <ChatContainerScrollAnchor />
      </ChatContainerContent>
    </ChatContainerRoot>
  )
}
