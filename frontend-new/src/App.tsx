import { useState, useEffect } from 'react'
import { MessageList } from '@/components/chat/MessageList'
import { MessageInput } from '@/components/chat/MessageInput'
import { useCreateConversation } from '@/queries'
import './index.css'

function App() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const createConversation = useCreateConversation()

  // Create a conversation on mount
  useEffect(() => {
    const initConversation = async () => {
      try {
        const conversation = await createConversation.mutateAsync({
          title: 'New Conversation',
        })
        setConversationId(conversation.id)
      } catch (error) {
        console.error('Failed to create conversation:', error)
      }
    }

    if (!conversationId) {
      initConversation()
    }
  }, [conversationId])

  if (!conversationId) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground">Initializing...</div>
      </div>
    )
  }

  return (
    <div className="relative h-screen bg-background">
      {/* Messages */}
      <MessageList conversationId={conversationId} />

      {/* Input */}
      <MessageInput conversationId={conversationId} />
    </div>
  )
}

export default App
