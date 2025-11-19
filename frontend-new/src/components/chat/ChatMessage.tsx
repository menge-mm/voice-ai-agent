import { useState, useRef, useEffect } from 'react'
import type { Message } from '@/types'
import { MessageBubble } from '@/components/ui/message-bubble'
import { MessageActions } from './MessageActions'
import { ThinkingBlock } from '@/components/thinking/ThinkingBlock'
import { UserCircleIcon, BotIcon, Volume2, VolumeX } from 'lucide-react'
import { useSettingsStore } from '@/stores'
import { cn } from '@/lib/utils'
import { useRegenerateMessage, useUpdateMessage } from '@/queries'
import { useQueryClient } from '@tanstack/react-query'
import { useTTS } from '@/hooks/useTTS'

type ChatMessageProps = {
  message: Message
}

/**
 * ChatMessage - Professional message display component
 *
 * Design principles:
 * - Clean visual hierarchy
 * - Smooth hover effects
 * - Actions appear contextually
 * - Thinking process shown BEFORE content (for AI messages)
 * - Accessible and semantic
 * - Inline editing for user messages
 */
export function ChatMessage({ message }: ChatMessageProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(message.content)
  const [currentVersionIndex, setCurrentVersionIndex] = useState(message.currentVersionIndex ?? 0)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const editableRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const updateMessage = useUpdateMessage()
  const regenerateMessage = useRegenerateMessage()
  const { playAudio, stopAudio, isPlaying, currentAudioUrl } = useTTS()

  const showTimestamps = useSettingsStore((state) => state.messageTimestamps)
  const showThinking = useSettingsStore((state) => state.showThinking)
  const isUser = message.role === 'user'
  const isStreaming = message.status === 'streaming'
  const isPending = message.status === 'pending'

  // Get current version content
  const versions = message.versions ?? []
  const totalVersions = versions.length

  const currentVersion = versions[currentVersionIndex]
  const displayContent = currentVersion?.content ?? message.content
  const displayThinking = currentVersion?.thinkingNodes ?? message.thinkingNodes

  const hasThinking = !isUser && displayThinking && displayThinking.length > 0

  const handleVersionChange = (index: number) => {
    if (index >= 0 && index < totalVersions) {
      setCurrentVersionIndex(index)

      // Persist the version selection in the cache
      queryClient.setQueryData(
        ['messages', 'list', message.conversationId, undefined],
        (oldData: any) => {
          if (!oldData) return oldData

          return {
            ...oldData,
            data: oldData.data.map((msg: Message) =>
              msg.id === message.id
                ? { ...msg, currentVersionIndex: index }
                : msg
            ),
          }
        }
      )
    }
  }

  // Sync currentVersionIndex when message.currentVersionIndex changes (e.g., after regeneration)
  useEffect(() => {
    if (message.currentVersionIndex !== undefined && message.currentVersionIndex !== currentVersionIndex) {
      setCurrentVersionIndex(message.currentVersionIndex)
    }
  }, [message.currentVersionIndex])

  // Focus contentEditable and set content when entering edit mode
  useEffect(() => {
    if (isEditing && editableRef.current) {
      // Set text content
      editableRef.current.textContent = editedContent
      editableRef.current.focus()

      // Move cursor to end
      const range = document.createRange()
      const selection = window.getSelection()
      range.selectNodeContents(editableRef.current)
      range.collapse(false)
      selection?.removeAllRanges()
      selection?.addRange(range)
    }
  }, [isEditing, editedContent])

  const handleEditStart = () => {
    setEditedContent(message.content)
    setIsEditing(true)
  }

  const handleEditCancel = () => {
    setIsEditing(false)
    setEditedContent(message.content)
  }

  const handleEditSave = async () => {
    if (!editedContent.trim() || editedContent === message.content) {
      setIsEditing(false)
      return
    }

    setIsRegenerating(true)

    try {
      // Find the next AI message BEFORE updating (to avoid cache issues)
      const messagesData: any = queryClient.getQueryData([
        'messages',
        'list',
        message.conversationId,
        undefined,
      ])

      let nextAIMessage: Message | undefined

      if (messagesData?.data) {
        const currentIndex = messagesData.data.findIndex(
          (msg: Message) => msg.id === message.id
        )

        // Find the AI message after this user message
        nextAIMessage = messagesData.data
          .slice(currentIndex + 1)
          .find((msg: Message) => msg.role === 'assistant')
      }

      // Update the user message via API
      await updateMessage.mutateAsync({
        conversationId: message.conversationId,
        messageId: message.id,
        content: editedContent.trim(),
      })

      // Regenerate the AI message if it exists
      if (nextAIMessage) {
        await regenerateMessage.mutateAsync({
          conversationId: message.conversationId,
          messageId: nextAIMessage.id,
        })
      }

      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save edited message:', error)
      // Error is logged - UI shows loading states and user can retry if needed
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      e.stopPropagation()

      if (!e.shiftKey) {
        // Enter without Shift: save and regenerate
        handleEditSave()
      }
      // Shift+Enter: allow new line (but we're preventing default, so we need to manually add it)
      // For now, just save on Enter - user can use Shift+Enter if needed in future
    } else if (e.key === 'Escape') {
      e.preventDefault()
      e.stopPropagation()
      handleEditCancel()
    }
  }

  const handleInput = (e: React.FormEvent<HTMLDivElement>) => {
    setEditedContent(e.currentTarget.textContent || '')
  }

  return (
    <div
      className={cn(
        'flex gap-3 group relative',
        'animate-in fade-in slide-in-from-bottom-2 duration-300',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {/* Avatar - assistant only */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center ring-1 ring-primary/10">
          <BotIcon className="size-4 text-primary" />
        </div>
      )}

      {/* Message content */}
      <div className={cn('flex flex-col gap-2.5 flex-1 min-w-0', isUser && 'items-end')}>
        {/* CRITICAL: Thinking appears BEFORE message content for completed messages */}
        {showThinking && hasThinking && !isStreaming && (
          <div className="w-full animate-in fade-in slide-in-from-top-1 duration-200">
            <ThinkingBlock nodes={displayThinking!} defaultExpanded={false} />
          </div>
        )}

        {/* Message bubble or edit mode */}
        <div className={cn('relative w-full')}>
          {isEditing && isUser ? (
            // Inline edit mode for user messages - contentEditable with nice styling
            <div className={cn(
              'rounded-2xl px-4 py-3 max-w-xl ml-auto',
              'bg-gray-100 dark:bg-blue-500/15 shadow-sm',
              'ring-2 ring-primary/50',
              'transition-all duration-200'
            )}>
              <div
                ref={editableRef}
                contentEditable
                suppressContentEditableWarning
                onInput={handleInput}
                onKeyDown={handleKeyDown}
                role="textbox"
                aria-label="Edit your message"
                aria-multiline="true"
                className={cn(
                  "w-full outline-none",
                  "text-sm leading-relaxed whitespace-pre-wrap break-words",
                  "min-h-[60px]",
                  "empty:before:content-[attr(data-placeholder)] empty:before:text-muted-foreground/50"
                )}
                data-placeholder="Edit your message..."
              />
              <div className="text-[10px] text-muted-foreground/70 mt-2 pt-2 border-t border-border/30" aria-live="polite">
                <kbd className="px-1 py-0.5 rounded bg-muted/50 font-mono text-[9px]">Enter</kbd> to save and regenerate • <kbd className="px-1 py-0.5 rounded bg-muted/50 font-mono text-[9px]">Esc</kbd> to cancel
              </div>
            </div>
          ) : (
            // Normal message display
            <MessageBubble
              role={message.role === 'system' ? 'assistant' : message.role}
              content={displayContent}
              timestamp={showTimestamps ? message.timestamp : undefined}
              attachments={message.attachments}
              currentVersion={currentVersionIndex}
              totalVersions={totalVersions}
              onVersionChange={handleVersionChange}
            />
          )}

          {/* Status indicators - integrated and polished */}
          {isPending && (
            <div className="flex items-center gap-2 mt-2 px-1 animate-in fade-in slide-in-from-left-1 duration-200">
              <div className="flex gap-1">
                <span className="size-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:0ms]" />
                <span className="size-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:150ms]" />
                <span className="size-1.5 rounded-full bg-primary/60 animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-xs text-muted-foreground/70 font-medium">Sending...</span>
            </div>
          )}
          {isStreaming && (
            <div className="flex items-center gap-2 mt-2 px-1 animate-in fade-in slide-in-from-left-1 duration-200">
              <div className="flex gap-1">
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-xs text-primary/90 font-medium">Generating...</span>
            </div>
          )}
          {isRegenerating && !isUser && (
            <div className="flex items-center gap-2 mt-2 px-1 animate-in fade-in slide-in-from-left-1 duration-200">
              <div className="flex gap-1">
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:0ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:150ms]" />
                <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:300ms]" />
              </div>
              <span className="text-xs text-primary/90 font-medium">Regenerating...</span>
            </div>
          )}
        </div>

        {/* TTS Audio Player - for assistant messages with audio */}
        {!isUser && message.audioUrl && !isPending && !isStreaming && (
          <div className="flex items-center gap-1.5 mt-2">
            <button
              onClick={() => {
                if (isPlaying && currentAudioUrl === message.audioUrl) {
                  stopAudio()
                } else {
                  playAudio(message.audioUrl!)
                }
              }}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors text-xs"
              aria-label={isPlaying && currentAudioUrl === message.audioUrl ? "Stop audio" : "Play audio"}
            >
              {isPlaying && currentAudioUrl === message.audioUrl ? (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-primary" />
                  <span>Playing...</span>
                </>
              ) : (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Play audio</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Message actions - smooth reveal on hover */}
        {!isPending && !isStreaming && !isEditing && (
          <div
            className={cn(
              "opacity-0 group-hover:opacity-100",
              "transition-all duration-200 ease-out",
              "transform translate-y-2 group-hover:translate-y-0"
            )}
          >
            <MessageActions
              message={message}
              onEditStart={handleEditStart}
              isRegenerating={isRegenerating}
            />
          </div>
        )}
      </div>

      {/* Avatar - user only */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-sm">
          <UserCircleIcon className="size-5 text-primary-foreground" />
        </div>
      )}
    </div>
  )
}
