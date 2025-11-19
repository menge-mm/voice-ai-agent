import { useActionState, useState, useRef } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { useStreamMessage } from '@/queries';
import { useChatStore, useUIStore, useSettingsStore } from '@/stores';
import {
  ArrowRight,
  StopCircle,
  Paperclip,
  FileText,
  X,
  Globe,
  Volume2,
  Mic,
  MicOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAutoResizeTextarea } from '@/hooks/useAutoResizeTextarea';
import { useWhisper } from '@/features/voice/hooks/useWhisper';
import type { MessageAttachment } from '@/types';

type MessageInputProps = {
  conversationId: string;
};

interface SendMessageState {
  error: string | null;
}

/**
 * MessageInput - Modern AI chat input with auto-resize and TTS toggle
 *
 * Design inspired by kokonutui with adaptations for Voice AI Agent:
 * - Auto-resizing textarea
 * - Clean, modern design with subtle gradients
 * - Smooth animations and transitions
 * - File upload support
 * - Web search toggle
 * - TTS (Text-to-Speech) toggle - NEW!
 */
export function MessageInput({ conversationId }: MessageInputProps) {
  const [value, setValue] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 72,
    maxHeight: 300,
  });

  const streamMessage = useStreamMessage();
  const streamState = useChatStore((state) => state.streamState);
  const { isMobile, isSidebarCollapsed } = useUIStore();
  const { ttsEnabled, setTtsEnabled } = useSettingsStore();
  const { transcribe, isReady: whisperReady } = useWhisper();

  const isStreaming =
    streamState?.isStreaming && streamState.conversationId === conversationId;

  // Calculate left offset based on sidebar state (desktop only)
  const leftOffset = isMobile ? '0' : isSidebarCollapsed ? '80px' : '260px';

  // React 19 action state
  const [, submitAction, isPending] = useActionState(
    async (
      _prevState: SendMessageState,
      formData: FormData
    ): Promise<SendMessageState> => {
      const content = formData.get('message') as string;

      if (!content?.trim()) {
        return { error: 'Message cannot be empty' };
      }

      try {
        // Convert File[] to MessageAttachment[] with object URLs for immediate display
        const messageAttachments: MessageAttachment[] = attachments.map(
          (file) => ({
            id: `${file.name}-${Date.now()}-${Math.random()
              .toString(36)
              .slice(2, 9)}`,
            name: file.name,
            size: file.size,
            type: file.type,
            url: URL.createObjectURL(file), // Create object URL for immediate display
          })
        );

        await streamMessage.mutateAsync({
          conversationId,
          content: content.trim(),
          enableThinking: true,
          attachments:
            messageAttachments.length > 0 ? messageAttachments : undefined,
          generateAudio: ttsEnabled, // NEW: Pass TTS preference to backend
        });

        // Clear on success
        setValue('');
        setAttachments([]);
        adjustHeight(true);

        return { error: null };
      } catch (error) {
        return {
          error:
            error instanceof Error ? error.message : 'Failed to send message',
        };
      }
    },
    { error: null }
  );

  // TODO: Handle stream cancellation when SSE streaming is implemented
  const handleCancelStream = () => {
    // Stream cancellation not implemented yet
    console.log('Stream cancellation not yet implemented');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isStreaming && !isPending) {
        const form = e.currentTarget.form;
        if (form) {
          form.requestSubmit();
        }
      }
    }
  };

  const handleSubmit = () => {
    if (value.trim() && !isStreaming && !isPending) {
      const form = textareaRef.current?.form;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setAttachments([...attachments, ...files]);
    }
    e.target.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };

  // Voice recording handlers
  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());

        try {
          // Convert audio blob to Float32Array for Whisper
          const arrayBuffer = await audioBlob.arrayBuffer();
          const audioContext = new AudioContext({ sampleRate: 16000 });
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          const audioData = audioBuffer.getChannelData(0);

          // Transcribe with Whisper
          const text = await transcribe(audioData);

          if (text) {
            setValue(text);
            adjustHeight();
          }
        } catch (error) {
          console.error('Transcription failed:', error);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      setMediaRecorder(null);
      setIsRecording(false);
    }
  };

  const isDisabled = isStreaming || isPending;

  return (
    <div
      className="fixed bottom-0 min-w-xl z-10 p-2 transition-all duration-300 pointer-events-none"
      style={{ left: leftOffset }}
    >
      <div className="w-full max-w-3xl mx-auto pointer-events-auto">
        <form action={submitAction}>
          <div className="bg-muted/80 backdrop-blur-sm rounded-2xl p-0 border border-border/50 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
            <div className="relative">
              <div className="relative flex flex-col">
                {/* Textarea */}
                <div className="overflow-y-auto" style={{ maxHeight: '400px' }}>
                  <Textarea
                    ref={textareaRef}
                    name="message"
                    value={value}
                    placeholder={
                      isStreaming
                        ? 'Waiting for response...'
                        : isPending
                        ? 'Sending...'
                        : 'Ask anything...'
                    }
                    className={cn(
                      'w-full rounded-none placeholder:font-mono px-5 pt-4 bg-muted/80 border-none text-foreground placeholder:text-muted-foreground/70 resize-none focus-visible:ring-0 focus-visible:ring-offset-0 transition-colors duration-200',
                      'min-h-1'
                    )}
                    onKeyDown={handleKeyDown}
                    onChange={(e) => {
                      setValue(e.target.value);
                      adjustHeight();
                    }}
                    disabled={isDisabled}
                  />
                </div>

                {/* Bottom bar with actions */}
                <div className="h-12 bg-muted/80 flex items-center">
                  <div className="absolute left-3 right-3 bottom-3 flex items-center justify-between w-[calc(100%-24px)]">
                    {/* Left side - Tools and File Preview */}
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {/* Web Search Toggle */}
                      <button
                        type="button"
                        onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                        className={cn(
                          'rounded-lg p-1.5 bg-muted transition-all duration-200 shrink-0',
                          'hover:bg-accent',
                          'focus-visible:ring-[3px] focus-visible:ring-ring/50',
                          'text-muted-foreground hover:text-foreground',
                          webSearchEnabled && 'bg-primary/20 text-primary',
                          isDisabled && 'opacity-50 cursor-not-allowed'
                        )}
                        disabled={isDisabled}
                        aria-label="Toggle web search"
                        title={
                          webSearchEnabled
                            ? 'Web search enabled'
                            : 'Enable web search'
                        }
                      >
                        <Globe className="w-4 h-4 transition-colors" />
                      </button>

                      {/* <div className="h-4 w-px bg-border mx-0.5 shrink-0" /> */}

                      {/* TTS Toggle - NEW! */}
                      <button
                        type="button"
                        onClick={() => setTtsEnabled(!ttsEnabled)}
                        className={cn(
                          'rounded-lg p-1.5 bg-muted transition-all duration-200 shrink-0',
                          'hover:bg-accent',
                          'focus-visible:ring-[3px] focus-visible:ring-ring/50',
                          'text-muted-foreground hover:text-foreground',
                          ttsEnabled && 'bg-primary/20 text-primary',
                          isDisabled && 'opacity-50 cursor-not-allowed'
                        )}
                        disabled={isDisabled}
                        aria-label="Toggle text-to-speech"
                        title={
                          ttsEnabled
                            ? 'TTS enabled - AI will speak responses'
                            : 'Enable TTS'
                        }
                      >
                        <Volume2 className="w-4 h-4 transition-colors" />
                      </button>

                      {/* <div className="h-4 w-px bg-border mx-0.5 shrink-0" /> */}

                      {/* Voice Recording (Whisper) - NEW! */}
                      <button
                        type="button"
                        onClick={
                          isRecording
                            ? handleStopRecording
                            : handleStartRecording
                        }
                        className={cn(
                          'rounded-lg p-1.5 bg-muted transition-all duration-200 shrink-0',
                          'hover:bg-accent',
                          'focus-visible:ring-[3px] focus-visible:ring-ring/50',
                          'text-muted-foreground hover:text-foreground',
                          isRecording &&
                            'bg-red-500/20 text-red-500 animate-pulse',
                          (!whisperReady || isDisabled) &&
                            'opacity-50 cursor-not-allowed'
                        )}
                        disabled={!whisperReady || isDisabled}
                        aria-label={
                          isRecording
                            ? 'Stop recording'
                            : 'Start voice recording'
                        }
                        title={
                          !whisperReady
                            ? 'Whisper model loading...'
                            : isRecording
                            ? 'Stop recording'
                            : 'Voice input (Whisper STT)'
                        }
                      >
                        {isRecording ? (
                          <MicOff className="w-4 h-4 transition-colors" />
                        ) : (
                          <Mic className="w-4 h-4 transition-colors" />
                        )}
                      </button>

                      {/* <div className="h-4 w-px bg-border mx-0.5 shrink-0" /> */}

                      {/* File Attach */}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className={cn(
                          'rounded-lg p-1.5 bg-muted cursor-pointer shrink-0',
                          'hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50',
                          'text-muted-foreground hover:text-foreground',
                          isDisabled && 'opacity-50 cursor-not-allowed'
                        )}
                        disabled={isDisabled}
                        aria-label="Attach file"
                      >
                        <Paperclip className="w-4 h-4 transition-colors" />
                      </button>

                      {/* File attachments preview - inline */}
                      {attachments.length > 0 && (
                        <div className="flex items-center gap-1 ml-1 max-w-[120px] overflow-hidden">
                          {attachments.slice(0, 2).map((file, i) => {
                            const isImage = file.type.startsWith('image/');
                            if (isImage) {
                              const url = URL.createObjectURL(file);
                              return (
                                <div
                                  key={`${file.name}-${i}`}
                                  className="group relative h-5 w-5 overflow-hidden rounded border border-black/20 dark:border-white/20 shadow-sm shrink-0"
                                >
                                  <img
                                    src={url}
                                    alt={file.name}
                                    onLoad={() => URL.revokeObjectURL(url)}
                                    className="h-full w-full object-cover"
                                  />
                                  <button
                                    type="button"
                                    aria-label="Remove attachment"
                                    onClick={() => removeAttachment(i)}
                                    className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-white dark:bg-black border border-black/20 dark:border-white/20 text-black dark:text-white hover:bg-red-500 hover:text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200"
                                  >
                                    <X className="h-1.5 w-1.5" />
                                  </button>
                                </div>
                              );
                            }
                            return (
                              <div
                                key={`${file.name}-${i}`}
                                className="group relative h-5 w-5 rounded border border-black/20 dark:border-white/20 bg-black/5 dark:bg-white/5 flex items-center justify-center shadow-sm shrink-0"
                              >
                                <FileText className="h-3 w-3 text-black/60 dark:text-white/60" />
                                <button
                                  type="button"
                                  aria-label="Remove attachment"
                                  onClick={() => removeAttachment(i)}
                                  className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-white dark:bg-black border border-black/20 dark:border-white/20 text-black dark:text-white hover:bg-red-500 hover:text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-200"
                                >
                                  <X className="h-1.5 w-1.5" />
                                </button>
                              </div>
                            );
                          })}
                          {attachments.length > 2 && (
                            <span className="text-[10px] text-black/60 dark:text-white/60 bg-black/5 dark:bg-white/5 px-1 py-0.5 rounded border border-black/10 dark:border-white/10 shrink-0">
                              +{attachments.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Right side - Submit */}
                    {isStreaming ? (
                      <button
                        type="button"
                        onClick={handleCancelStream}
                        className="rounded-lg p-2 bg-destructive/10 hover:bg-destructive/20 text-destructive transition-all duration-200 focus-visible:ring-1 focus-visible:ring-offset-0 focus-visible:ring-destructive"
                        aria-label="Stop generating"
                      >
                        <StopCircle className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="button"
                        className={cn(
                          'rounded-lg p-2 bg-muted transition-all duration-200',
                          'hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50',
                          'disabled:opacity-50 disabled:cursor-not-allowed',
                          value.trim() && !isDisabled
                            ? 'bg-primary hover:bg-primary/90 text-primary-foreground'
                            : ''
                        )}
                        aria-label="Send message"
                        disabled={!value.trim() || isDisabled}
                        onClick={handleSubmit}
                      >
                        <ArrowRight
                          className={cn(
                            'w-4 h-4 transition-opacity duration-200',
                            value.trim() && !isDisabled
                              ? 'opacity-100 text-primary-foreground'
                              : 'opacity-30 text-muted-foreground'
                          )}
                        />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </form>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          disabled={isDisabled}
          multiple
          accept="image/*,.pdf,.doc,.docx,.txt"
        />
      </div>
    </div>
  );
}
