import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useChatStore } from '@/stores'
import type {
  Message,
  MessageAttachment,
  PaginatedResponse,
  ChatRequest,
  ChatResponse,
} from '@/types'

/**
 * Message Query Hooks
 *
 * Adapted for our backend API schema:
 * POST /api/v1/chat with {text, user_id, conversation_id, generate_audio, language}
 */

// ============================================================================
// API Functions
// ============================================================================

async function fetchMessages(
  _conversationId: string
): Promise<PaginatedResponse<Message>> {
  // For now, return empty messages
  // Messages will be populated as user chats
  return {
    data: [],
    total: 0,
    page: 1,
    limit: 50,
  }
}

interface SendMessageParams {
  conversationId?: string
  content: string
  enableThinking?: boolean
  attachments?: MessageAttachment[]
  generateAudio?: boolean
}

async function sendMessage(params: SendMessageParams): Promise<{
  userMessage: Message
  assistantMessage: Message
}> {
  const { conversationId, content, generateAudio = false } = params

  // Create user message
  const userMessage: Message = {
    id: crypto.randomUUID(),
    role: 'user',
    content,
    timestamp: new Date(),
    conversationId: conversationId || 'new',
    status: 'pending',
    attachments: params.attachments,
  }

  // Call backend API
  const request: ChatRequest = {
    text: content,
    user_id: 1,
    conversation_id: conversationId,
    generate_audio: generateAudio,
    language: 'en',
  }

  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`)
  }

  const data: ChatResponse = await response.json()

  // Create assistant message
  const assistantMessage: Message = {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: data.text,
    timestamp: new Date(),
    conversationId: data.conversation_id,
    status: 'completed',
    audioUrl: data.audio ? `data:audio/wav;base64,${data.audio}` : undefined,
  }

  // Update user message with correct conversation ID (create new object to trigger React re-render)
  const updatedUserMessage: Message = {
    ...userMessage,
    conversationId: data.conversation_id,
    status: 'completed',
  }

  return { userMessage: updatedUserMessage, assistantMessage }
}

async function updateMessage(_params: {
  conversationId: string
  messageId: string
  content: string
}): Promise<Message> {
  // TODO: Implement backend update endpoint
  // For now, just return a updated message
  throw new Error('Message update not implemented in backend yet')
}

async function regenerateMessage(_params: {
  conversationId: string
  messageId: string
}): Promise<Message> {
  // TODO: Implement backend regenerate endpoint
  // For now, just throw error
  throw new Error('Message regeneration not implemented in backend yet')
}

// ============================================================================
// Query Hooks
// ============================================================================

export function useMessages(conversationId: string) {
  return useQuery({
    queryKey: ['messages', 'list', conversationId, undefined],
    queryFn: () => fetchMessages(conversationId),
    enabled: !!conversationId,
  })
}

export function useStreamMessage() {
  const queryClient = useQueryClient()
  const setStreamState = useChatStore((state) => state.setStreamState)

  return useMutation({
    mutationFn: sendMessage,
    onMutate: async (params) => {
      // Optimistic update: add user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: params.content,
        timestamp: new Date(),
        conversationId: params.conversationId || 'new',
        status: 'pending',
        attachments: params.attachments,
      }

      const conversationId = params.conversationId || 'new'

      await queryClient.cancelQueries({
        queryKey: ['messages', 'list', conversationId],
      })

      const previousMessages = queryClient.getQueryData<
        PaginatedResponse<Message>
      >(['messages', 'list', conversationId, undefined])

      queryClient.setQueryData<PaginatedResponse<Message>>(
        ['messages', 'list', conversationId, undefined],
        (old) => ({
          data: [...(old?.data || []), userMessage],
          total: (old?.total || 0) + 1,
          page: old?.page || 1,
          limit: old?.limit || 50,
        })
      )

      return { previousMessages, userMessage }
    },
    onSuccess: (data) => {
      const conversationId = data.assistantMessage.conversationId

      // Add assistant message to cache
      queryClient.setQueryData<PaginatedResponse<Message>>(
        ['messages', 'list', conversationId, undefined],
        (old) => {
          if (!old) return old

          // Update user message status and add assistant message
          return {
            ...old,
            data: [
              ...old.data.map((msg) =>
                msg.id === data.userMessage.id
                  ? { ...data.userMessage, status: 'completed' as const }
                  : msg
              ),
              data.assistantMessage,
            ],
          }
        }
      )

      // Clear stream state
      setStreamState(null)
    },
    onError: (_error, params, context) => {
      // Rollback optimistic update on error
      if (context?.previousMessages) {
        const conversationId = params.conversationId || 'new'
        queryClient.setQueryData(
          ['messages', 'list', conversationId, undefined],
          context.previousMessages
        )
      }
      setStreamState(null)
    },
  })
}

export function useUpdateMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateMessage,
    onSuccess: (updated) => {
      // Update message in cache
      queryClient.setQueryData<PaginatedResponse<Message>>(
        ['messages', 'list', updated.conversationId, undefined],
        (old) => {
          if (!old) return old
          return {
            ...old,
            data: old.data.map((msg) =>
              msg.id === updated.id ? updated : msg
            ),
          }
        }
      )
    },
  })
}

export function useRegenerateMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: regenerateMessage,
    onSuccess: (regenerated) => {
      // Update message in cache
      queryClient.setQueryData<PaginatedResponse<Message>>(
        ['messages', 'list', regenerated.conversationId, undefined],
        (old) => {
          if (!old) return old
          return {
            ...old,
            data: old.data.map((msg) =>
              msg.id === regenerated.id ? regenerated : msg
            ),
          }
        }
      )
    },
  })
}
