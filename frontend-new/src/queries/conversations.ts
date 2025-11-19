import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Conversation } from '@/types'

/**
 * Conversation Query Hooks
 *
 * Manages conversations with TanStack Query
 * TODO: Implement backend API endpoints when ready
 */

// ============================================================================
// API Functions
// ============================================================================

async function fetchConversations(): Promise<Conversation[]> {
  // TODO: Implement when backend has conversation list endpoint
  // const response = await fetch('/api/v1/conversations')
  // return response.json()
  return []
}

async function createConversation(title: string): Promise<Conversation> {
  // For now, create a local conversation
  // TODO: Implement when backend has create conversation endpoint
  return {
    id: crypto.randomUUID(),
    title,
    createdAt: new Date(),
    updatedAt: new Date(),
    userId: '1',
  }
}

async function updateConversation(
  _id: string,
  _title: string
): Promise<Conversation> {
  // TODO: Implement when backend has update endpoint
  throw new Error('Not implemented')
}

async function deleteConversation(_id: string): Promise<void> {
  // TODO: Implement when backend has delete endpoint
  throw new Error('Not implemented')
}

// ============================================================================
// Query Hooks
// ============================================================================

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: fetchConversations,
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { title: string }) => createConversation(data.title),
    onSuccess: (newConversation) => {
      queryClient.setQueryData<Conversation[]>(
        ['conversations'],
        (old = []) => [newConversation, ...old]
      )
    },
  })
}

export function useUpdateConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { id: string; title: string }) =>
      updateConversation(data.id, data.title),
    onSuccess: (updated) => {
      queryClient.setQueryData<Conversation[]>(
        ['conversations'],
        (old = []) =>
          old.map((conv) => (conv.id === updated.id ? updated : conv))
      )
    },
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.setQueryData<Conversation[]>(
        ['conversations'],
        (old = []) => old.filter((conv) => conv.id !== deletedId)
      )
    },
  })
}
