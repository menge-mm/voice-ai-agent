import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { User, Bot } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  audioUrl?: string;
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'flex gap-3 px-4 py-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted text-muted-foreground'
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div className={cn('flex max-w-[70%] flex-col gap-2')}>
        {/* Message Bubble */}
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm',
            isUser
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-foreground'
          )}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Audio Player (if TTS was generated) */}
        {message.audioUrl && (
          <div className="rounded-lg border bg-background p-2">
            <audio
              src={message.audioUrl}
              controls
              className="w-full"
              preload="metadata"
            />
          </div>
        )}

        {/* Timestamp */}
        <span className="px-2 text-xs text-muted-foreground">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </motion.div>
  );
}
