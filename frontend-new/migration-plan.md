# UI Migration + TTS Integration Plan

## Overview
Port the complete chat UI from `../chatbot-react-tanstack-query/` to `voice-ai-agent/frontend-new` with exact visual design, then add TTS functionality with a toggle button next to the file attachment icon.

---

## Phase 1: Dependencies & Infrastructure Setup

### 1.1 Install Missing Packages
```bash
npm install use-stick-to-bottom react-textarea-autosize
```

### 1.2 Create Directory Structure
```
src/
├── types/
│   └── index.ts              # Centralized type definitions
├── stores/
│   ├── useChatStore.ts       # Stream state management
│   ├── useUIStore.ts         # Sidebar/mobile state
│   └── useSettingsStore.ts   # User preferences
├── queries/
│   ├── conversations.ts      # Conversation queries
│   ├── messages.ts           # Message queries
│   └── queryClient.ts        # TanStack Query config
├── hooks/
│   ├── useAutoResizeTextarea.ts
│   └── useTTS.ts             # NEW: TTS functionality
└── components/
    ├── prompt-kit/
    │   └── chat-container.tsx  # StickToBottom wrapper
    ├── thinking/
    │   └── ThinkingBlock.tsx
    └── chat/
        ├── ChatMessage.tsx       # Port from chatbot
        ├── MessageActions.tsx    # Port from chatbot
        ├── MessageInput.tsx      # Port + add TTS toggle
        ├── MessageList.tsx       # Port from chatbot
        └── StreamingMessage.tsx  # Port from chatbot
```

---

## Phase 2: Type Definitions

**Create `src/types/index.ts`** with rich types from chatbot:
```typescript
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
  audioUrl?: string  // Keep for TTS
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
  timestamp: Date
}

export interface Conversation {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  userId: string
}
```

---

## Phase 3: State Management (Zustand Stores)

### 3.1 Create `src/stores/useChatStore.ts`
```typescript
interface StreamState {
  isStreaming: boolean
  conversationId: string
  messageId: string
  content: string
  thinking: ThinkingNode[]
}

interface ChatStore {
  streamState: StreamState | null
  setStreamState: (state: StreamState | null) => void
}
```

### 3.2 Create `src/stores/useUIStore.ts`
```typescript
interface UIStore {
  isSidebarCollapsed: boolean
  isMobile: boolean
  toggleSidebar: () => void
  setIsMobile: (isMobile: boolean) => void
}
```

### 3.3 Create `src/stores/useSettingsStore.ts`
```typescript
interface SettingsStore {
  messageTimestamps: boolean
  showThinking: boolean
  ttsEnabled: boolean  // NEW for TTS
  setMessageTimestamps: (show: boolean) => void
  setShowThinking: (show: boolean) => void
  setTtsEnabled: (enabled: boolean) => void
}
```

---

## Phase 4: TanStack Query Setup

### 4.1 Create `src/queries/queryClient.ts`
Configure TanStack Query with optimistic updates

### 4.2 Create `src/queries/conversations.ts`
```typescript
export function useConversations()
export function useCreateConversation()
export function useUpdateConversation()
export function useDeleteConversation()
```

### 4.3 Create `src/queries/messages.ts`
```typescript
export function useMessages(conversationId: string)
export function useStreamMessage()  // Adapt for our backend
export function useUpdateMessage()  // For editing
export function useRegenerateMessage()  // Regenerate AI response
```

**Adaptation Notes:**
- Our backend: `POST /api/v1/chat` with `{text, user_id, conversation_id, generate_audio, language}`
- Chatbot backend: Different schema (need to adapt)
- Keep conversation_id context flow we already implemented

---

## Phase 5: UI Primitives & Utilities

### 5.1 Port UI Components
Copy from chatbot project:
- `src/components/ui/message-bubble.tsx`
- `src/components/ui/empty-state.tsx`
- `src/components/ui/message-skeleton.tsx`

### 5.2 Create `src/components/prompt-kit/chat-container.tsx`
Wrapper around use-stick-to-bottom library:
```typescript
export function ChatContainerRoot({ children, className })
export function ChatContainerContent({ children, className })
export function ChatContainerScrollAnchor()
```

### 5.3 Create `src/hooks/useAutoResizeTextarea.ts`
Auto-resize logic for textarea (from chatbot MessageInput)

---

## Phase 6: Chat Components

### 6.1 Port `ChatMessage.tsx`
**Copy from chatbot with these adaptations:**
- Keep message editing with inline contentEditable
- Keep version navigation
- Keep thinking visualization
- Keep regeneration
- Adapt API calls to our backend
- Add audio playback UI (if message.audioUrl exists)

### 6.2 Port `MessageActions.tsx`
Copy/edit/delete/regenerate actions with smooth hover effects

### 6.3 Port `StreamingMessage.tsx`
Real-time streaming display (adapt for our SSE format later)

### 6.4 Port `MessageList.tsx`
**Copy from chatbot with these adaptations:**
- Use our useMessages hook
- Keep StickToBottom integration
- Keep welcome screen
- Keep loading/error states
- Add streaming message support

### 6.5 Port `ThinkingBlock.tsx`
Collapsible thinking visualization (if backend supports it)

---

## Phase 7: Enhanced MessageInput with TTS Toggle

### 7.1 Port MessageInput.tsx Base
**Copy from chatbot project:**
- Auto-resize textarea
- React 19 useActionState
- File upload with preview
- Web search toggle
- Smooth animations
- Send/cancel buttons

### 7.2 Add TTS Toggle Button
**NEW: Add Speaker icon button next to Paperclip (file upload)**

```tsx
{/* TTS Toggle - NEW */}
<button
  type="button"
  onClick={() => setTtsEnabled(!ttsEnabled)}
  className={cn(
    "rounded-lg p-1.5 bg-muted transition-all duration-200 shrink-0",
    "hover:bg-accent",
    "focus-visible:ring-[3px] focus-visible:ring-ring/50",
    "text-muted-foreground hover:text-foreground",
    ttsEnabled && "bg-primary/20 text-primary",
    isDisabled && "opacity-50 cursor-not-allowed"
  )}
  disabled={isDisabled}
  aria-label="Toggle text-to-speech"
  title={ttsEnabled ? "TTS enabled" : "Enable TTS"}
>
  <Volume2 className="w-4 h-4 transition-colors" />
</button>

<div className="h-4 w-px bg-border mx-0.5 shrink-0" />

{/* File Attach - existing */}
<button type="button" onClick={...}>
  <Paperclip className="w-4 h-4" />
</button>
```

### 7.3 Update Send Logic
```typescript
await streamMessage.mutateAsync({
  conversationId,
  content: content.trim(),
  enableThinking: true,
  attachments: messageAttachments.length > 0 ? messageAttachments : undefined,
  generateAudio: ttsEnabled,  // NEW: Pass TTS preference
})
```

---

## Phase 8: TTS Implementation

### 8.1 Create `src/hooks/useTTS.ts`
```typescript
export function useTTS() {
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement>(null)

  const playAudio = async (audioUrl: string) => {
    if (!audioRef.current) {
      audioRef.current = new Audio()
    }

    audioRef.current.src = audioUrl
    audioRef.current.play()
    setIsPlaying(true)

    audioRef.current.onended = () => setIsPlaying(false)
  }

  const stopAudio = () => {
    audioRef.current?.pause()
    setIsPlaying(false)
  }

  return { playAudio, stopAudio, isPlaying }
}
```

### 8.2 Integrate TTS in ChatMessage
**Add audio player for assistant messages:**
```tsx
{message.audioUrl && (
  <button
    onClick={() => playAudio(message.audioUrl!)}
    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
  >
    {isPlaying ? <Volume2 className="w-3 h-3" /> : <VolumeX className="w-3 h-3" />}
    {isPlaying ? 'Playing...' : 'Play audio'}
  </button>
)}
```

### 8.3 Streaming Audio Support
**Future enhancement:** Play audio chunks as they arrive during streaming
- Backend needs to support audio streaming
- Frontend buffers and plays audio progressively

---

## Phase 9: Routing Migration

### 9.1 Update Routes
**Transform from:**
```tsx
// src/routes/index.tsx (single page)
export function ChatPage() { ... }
```

**To:**
```tsx
// src/routes/index.tsx (welcome screen)
export const Route = createFileRoute('/')(...)

// src/routes/chat.$conversationId.tsx (chat page)
export const Route = createFileRoute('/chat/$conversationId')(...)
```

### 9.2 Add Sidebar Navigation
**Optional:** Port sidebar from chatbot for conversation list
- Or keep simple single-conversation flow for now

---

## Phase 10: Backend API Adaptation

### 10.1 Adapt Query Hooks
**Our backend schema:**
```typescript
// Request
POST /api/v1/chat
{
  text: string
  user_id: number
  conversation_id?: string
  generate_audio: boolean  // TTS toggle state
  language: string
}

// Response
{
  text: string
  conversation_id: string
  audio?: string  // base64 WAV
  tokens_used: number
}
```

**Adapt useStreamMessage to:**
- Use our endpoint structure
- Handle generate_audio parameter
- Parse audio response
- Maintain conversation_id state

### 10.2 Future: Add SSE Streaming
**Later enhancement:**
- Backend: Create streaming endpoint `/api/v1/chat/stream`
- Frontend: EventSource for real-time updates
- Stream both text and audio chunks

---

## Phase 11: Testing & Polish

### 11.1 Visual Polish
- Verify exact UI match with chatbot project
- Test animations and transitions
- Test dark mode
- Test responsive design

### 11.2 Feature Testing
- ✅ Message sending with text input
- ✅ Voice recording with Whisper STT
- ✅ TTS toggle (on/off state persists)
- ✅ Audio playback for AI responses
- ✅ File attachments with preview
- ✅ Message editing and regeneration
- ✅ Conversation context maintained
- ✅ Auto-scroll behavior
- ✅ Loading states and error handling

### 11.3 Performance Testing
- Whisper model loading (already working)
- Audio playback latency
- Message list scroll performance
- Large conversation handling

---

## Success Criteria

1. **UI is flawless** - Exact visual match with chatbot project
2. **TTS works perfectly** - Toggle controls audio generation, audio plays smoothly
3. **All features work** - Editing, regeneration, attachments, thinking (if backend supports)
4. **Whisper STT continues working** - Voice input unchanged
5. **Conversation context maintained** - Multi-turn conversations work
6. **Performance is excellent** - Smooth animations, fast responses
7. **Code is clean** - TypeScript strict mode, proper error handling

---

## Rollback Plan

If migration encounters issues:
- Branch: `ui-copy-from-chatbot` (already created)
- Main branch: `claude/accept-voice-text-input-01LfvCiYZwoB33mNdJGXJuPc` (stable)
- Can revert individual phases independently
- Whisper integration isolated in hooks/workers (won't be affected)

---

## Estimated Effort

- **Phase 1-3:** Setup (30 min)
- **Phase 4-5:** Queries & UI primitives (45 min)
- **Phase 6-7:** Chat components + MessageInput (1.5 hr)
- **Phase 8:** TTS implementation (45 min)
- **Phase 9-10:** Routing & API adaptation (45 min)
- **Phase 11:** Testing & polish (1 hr)

**Total:** ~5 hours of focused work

---

## Key Technical Decisions

1. **Keep Whisper integration as-is** - Already working perfectly
2. **Port UI exactly** - No design changes, maintain visual consistency
3. **Adapt API calls** - Keep our backend schema, don't change backend
4. **TTS toggle in MessageInput** - Clear, accessible, next to file upload
5. **Audio in Message type** - Extend existing audioUrl field
6. **Progressive enhancement** - Start with basic TTS, add streaming later

---

## Implementation Checklist

### Phase 1: ✅ Dependencies
- [x] Install use-stick-to-bottom
- [x] Install react-textarea-autosize
- [ ] Create directory structure

### Phase 2: Type Definitions
- [ ] Create src/types/index.ts
- [ ] Define Message interface
- [ ] Define MessageAttachment interface
- [ ] Define MessageVersion interface
- [ ] Define ThinkingNode interface
- [ ] Define Conversation interface

### Phase 3: Stores
- [ ] Create useChatStore
- [ ] Create useUIStore
- [ ] Create useSettingsStore

### Phase 4: Queries
- [ ] Setup QueryClient
- [ ] Create conversation queries
- [ ] Create message queries
- [ ] Adapt to backend schema

### Phase 5: UI Primitives
- [ ] Port message-bubble
- [ ] Port empty-state
- [ ] Port message-skeleton
- [ ] Create ChatContainer components
- [ ] Create useAutoResizeTextarea

### Phase 6: Chat Components
- [ ] Port ChatMessage
- [ ] Port MessageActions
- [ ] Port StreamingMessage
- [ ] Port MessageList
- [ ] Port ThinkingBlock

### Phase 7: MessageInput
- [ ] Port MessageInput base
- [ ] Add TTS toggle button
- [ ] Integrate with stores

### Phase 8: TTS
- [ ] Create useTTS hook
- [ ] Integrate in ChatMessage
- [ ] Test audio playback

### Phase 9: Routing
- [ ] Update index route
- [ ] Create chat.$conversationId route
- [ ] Setup navigation

### Phase 10: Backend Integration
- [ ] Adapt query hooks
- [ ] Test API calls
- [ ] Verify conversation context

### Phase 11: Testing
- [ ] Visual testing
- [ ] Feature testing
- [ ] Performance testing
- [ ] Bug fixes
