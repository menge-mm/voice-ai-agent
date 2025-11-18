import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-foreground">
            Welcome! 👋
          </h2>
          <p className="mt-2 text-muted-foreground">
            Start a conversation by typing a message or recording your voice.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-hide">
      <div className="flex flex-col gap-1 py-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
