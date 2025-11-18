import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Mic, MicOff, Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  onVoiceRecord?: (audioBlob: Blob) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSendMessage,
  onVoiceRecord,
  disabled = false,
  placeholder = 'Type a message...',
}: ChatInputProps) {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!text.trim() || disabled) return;

    onSendMessage(text);
    setText('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        onVoiceRecord?.(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Auto-resize textarea
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);

    // Auto-resize
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  return (
    <div className="border-t bg-background p-4">
      <div className="flex items-end gap-2">
        {/* Text Input */}
        <Textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="max-h-32 min-h-[80px] resize-none"
          rows={1}
        />

        {/* Voice Recording Button */}
        {onVoiceRecord && (
          <Button
            type="button"
            variant={isRecording ? 'destructive' : 'outline'}
            size="icon"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={disabled}
            className={cn(
              'h-10 w-10 shrink-0',
              isRecording && 'animate-pulse'
            )}
          >
            {isRecording ? (
              <MicOff className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>
        )}

        {/* Send Button */}
        <Button
          type="button"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          size="icon"
          className="h-10 w-10 shrink-0"
        >
          {disabled ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
