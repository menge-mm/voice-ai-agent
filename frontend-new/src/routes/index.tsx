import { useState } from 'react';
import { MessageList } from '@/features/chat/components/MessageList';
import { ChatInput } from '@/features/chat/components/ChatInput';
import { Card } from '@/components/ui/card';
import { useWhisper } from '@/features/voice/hooks/useWhisper';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const { transcribe, isReady, status, progress } = useWhisper();

  const handleSendMessage = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call backend API
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          user_id: 1,
          conversation_id: conversationId,
          generate_audio: false,
          language: 'en',
        }),
      });

      const data = await response.json();

      // Save conversation ID for context
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.text,
        timestamp: new Date(),
        audioUrl: data.audio ? `data:audio/wav;base64,${data.audio}` : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);

      // Add error message
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'system',
        content: '❌ Failed to get response. Please try again.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceRecord = async (audioBlob: Blob) => {
    try {
      // Convert audio blob to Float32Array for Whisper
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioContext = new AudioContext({ sampleRate: 16000 });
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const audioData = audioBuffer.getChannelData(0);

      // Transcribe with Whisper
      const text = await transcribe(audioData);

      if (text) {
        handleSendMessage(text);
      }
    } catch (error) {
      console.error('Transcription failed:', error);
      alert('Failed to transcribe audio. Please try again.');
    }
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div>
            <h1 className="text-xl font-bold">Voice AI Agent</h1>
            <p className="text-xs text-muted-foreground">
              {status === 'loading' && `Loading Whisper model... ${progress}%`}
              {status === 'ready' && '✓ Ready'}
              {status === 'idle' && 'Initializing...'}
            </p>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="container mx-auto flex h-[calc(100vh-4rem)] max-w-4xl flex-col overflow-hidden">
        <Card className="my-4 flex flex-1 flex-col overflow-hidden">
          {/* Messages */}
          <MessageList messages={messages} />

          {/* Input */}
          <ChatInput
            onSendMessage={handleSendMessage}
            onVoiceRecord={handleVoiceRecord}
            disabled={isLoading}
            voiceReady={isReady}
            placeholder="Or type your message here..."
          />
        </Card>
      </div>
    </div>
  );
}

export default ChatPage;
