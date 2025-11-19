import { useState, useEffect, useRef, useCallback } from 'react';

type WhisperStatus = 'idle' | 'loading' | 'ready' | 'transcribing' | 'error';

interface UseWhisperReturn {
  status: WhisperStatus;
  progress: number;
  error: string | null;
  transcribe: (audio: Float32Array, language?: string) => Promise<string>;
  isReady: boolean;
}

/**
 * Hook to use Whisper STT in Web Worker (following official example)
 * Handles model loading, transcription, and state management
 */
export function useWhisper(): UseWhisperReturn {
  const [status, setStatus] = useState<WhisperStatus>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const workerRef = useRef<Worker | null>(null);
  const resolveRef = useRef<((text: string) => void) | null>(null);
  const rejectRef = useRef<((error: Error) => void) | null>(null);

  // Initialize Web Worker
  useEffect(() => {
    // Create worker using Vite's worker import pattern
    const worker = new Worker(
      new URL('../../../workers/whisper.worker.ts', import.meta.url),
      { type: 'module' }
    );

    workerRef.current = worker;

    // Handle messages from worker
    const handleMessage = (event: MessageEvent) => {
      const { type, ...data } = event.data;

      switch (type) {
        case 'LOADING':
          setStatus('loading');
          if (data.progress?.status === 'progress') {
            const percent = Math.round((data.progress.loaded / data.progress.total) * 100);
            setProgress(percent);
            console.log(`Loading: ${percent}%`);
          }
          break;

        case 'READY':
          setStatus('ready');
          setProgress(100);
          console.log('✓ Whisper model loaded successfully');
          break;

        case 'RESULT':
          setStatus('ready');
          if (resolveRef.current) {
            resolveRef.current(data.text);
            resolveRef.current = null;
          }
          break;

        case 'ERROR':
          setStatus('error');
          setError(data.error);
          console.error('✗ Whisper error:', data.error);
          if (rejectRef.current) {
            rejectRef.current(new Error(data.error));
            rejectRef.current = null;
          }
          break;
      }
    };

    worker.addEventListener('message', handleMessage);

    // Initialize model
    worker.postMessage({ type: 'INIT' });

    // Cleanup
    return () => {
      worker.removeEventListener('message', handleMessage);
      worker.terminate();
      workerRef.current = null;
    };
  }, []);

  // Transcribe function
  const transcribe = useCallback(
    async (audio: Float32Array, language?: string): Promise<string> => {
      if (!workerRef.current) {
        throw new Error('Worker not initialized');
      }

      if (status !== 'ready') {
        throw new Error('Model not ready');
      }

      setStatus('transcribing');

      return new Promise((resolve, reject) => {
        resolveRef.current = resolve;
        rejectRef.current = reject;

        workerRef.current!.postMessage({
          type: 'TRANSCRIBE',
          audio,
          language,
        });
      });
    },
    [status]
  );

  return {
    status,
    progress,
    error,
    transcribe,
    isReady: status === 'ready',
  };
}
