/**
 * Centralized type definitions for Voice AI Agent
 * Ported from chatbot-react-tanstack-query with adaptations
 */

// ============================================================================
// Message Types
// ============================================================================

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  conversationId: string
  status?: 'pending' | 'streaming' | 'completed' | 'error'
  thinkingNodes?: ThinkingNode[]
  versions?: MessageVersion[]
  currentVersionIndex?: number
  attachments?: MessageAttachment[]
  audioUrl?: string  // For TTS audio playback
}

export interface MessageAttachment {
  id: string
  name: string
  size: number
  type: string
  url: string
}

export interface MessageVersion {
  content: string
  thinkingNodes?: ThinkingNode[]
  timestamp: Date
}

export interface ThinkingNode {
  id: string
  type: 'thinking' | 'reasoning'
  content: string
  timestamp: number | Date
  parentId?: string | null
}

// ============================================================================
// Conversation Types
// ============================================================================

export interface Conversation {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  userId: string
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface ChatRequest {
  text: string
  user_id: number
  conversation_id?: string
  generate_audio: boolean
  language: string
}

export interface ChatResponse {
  text: string
  conversation_id: string
  audio?: string  // base64 encoded WAV
  tokens_used: number
}

// ============================================================================
// Stream State Types
// ============================================================================

export interface StreamState {
  isStreaming: boolean
  conversationId: string
  messageId: string
  content: string
  thinking: ThinkingNode[]
}

// ============================================================================
// Query Response Types
// ============================================================================

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

// ============================================================================
// Utility Types
// ============================================================================

export type MessageRole = Message['role']
export type MessageStatus = NonNullable<Message['status']>
