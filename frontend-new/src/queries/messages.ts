import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef } from 'react'
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

async function sendMessage(params: SendMessageParams & {
  onStream?: (chunk: string, accumulated: string) => void
}): Promise<{
  userMessage: Message
  assistantMessage: Message
}> {
  const { conversationId, content, generateAudio = false, onStream } = params

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

  // Call backend SSE streaming API
  const request: ChatRequest = {
    text: content,
    user_id: 1,
    conversation_id: conversationId,
    generate_audio: generateAudio,
    language: 'en',
  }

  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`)
  }

  // Read SSE stream
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('Response body is not readable')
  }

  let accumulatedText = ''
  let finalConversationId = conversationId || 'new'
  let audioUrl: string | undefined

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        if (line.startsWith('event:')) {
          const eventType = line.substring(6).trim()
          const nextLineIdx = i + 1

          if (nextLineIdx < lines.length && lines[nextLineIdx].startsWith('data:')) {
            const dataLine = lines[nextLineIdx].substring(5).trim()

            try {
              const data = JSON.parse(dataLine)

              switch (eventType) {
                case 'content':
                  accumulatedText += data.chunk
                  onStream?.(data.chunk, accumulatedText)
                  break

                case 'metadata':
                  finalConversationId = data.conversation_id
                  break

                case 'audio':
                  audioUrl = `data:audio/wav;base64,${data.audio}`
                  break

                case 'error':
                  console.error('Stream error:', data.message)
                  break

                case 'done':
                  // Stream complete
                  break
              }
            } catch (e) {
              // Ignore JSON parse errors for partial chunks
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }

  // Create assistant message
  const assistantMessage: Message = {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: accumulatedText,
    timestamp: new Date(),
    conversationId: finalConversationId,
    status: 'completed',
    audioUrl,
  }

  // Update user message with correct conversation ID
  const updatedUserMessage: Message = {
    ...userMessage,
    conversationId: finalConversationId,
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

  // Use ref to store current stream info for callbacks
  const streamInfoRef = useRef({ messageId: '', conversationId: '' })

  return useMutation({
    mutationFn: (params: SendMessageParams) => {
      // Call sendMessage with streaming callback using stored IDs
      return sendMessage({
        ...params,
        onStream: (_chunk: string, accumulated: string) => {
          // Update stream state with accumulated content
          setStreamState({
            isStreaming: true,
            conversationId: streamInfoRef.current.conversationId,
            messageId: streamInfoRef.current.messageId,
            content: accumulated,
            thinking: [],
          })
        },
      })
    },
    onMutate: async (params) => {
      const messageId = crypto.randomUUID()
      const conversationId = params.conversationId || 'new'

      // Store for use in mutationFn callback
      streamInfoRef.current = { messageId, conversationId }

      // Set initial stream state IMMEDIATELY
      setStreamState({
        isStreaming: true,
        conversationId,
        messageId,
        content: '',
        thinking: [],
      })

      // Optimistic update: add user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: params.content,
        timestamp: new Date(),
        conversationId,
        status: 'completed', // Mark as completed immediately since it's just the user message
        attachments: params.attachments,
      }

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

          // Add assistant message (user message was already added in onMutate)
          return {
            ...old,
            data: [...old.data, data.assistantMessage],
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
