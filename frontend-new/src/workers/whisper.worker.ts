/**
 * Whisper STT Web Worker
 * Runs Whisper model in background thread to avoid blocking UI
 * Model size: ~190MB, loads once and stays ready
 */

import { pipeline } from '@xenova/transformers';

// Worker state
let transcriber: any = null;
let isLoading = false;
let isReady = false;

// Message types
type WorkerMessage =
  | { type: 'INIT'; model: string }
  | { type: 'TRANSCRIBE'; audio: Float32Array; language?: string }
  | { type: 'STATUS' };

type WorkerResponse =
  | { type: 'LOADING'; progress?: number }
  | { type: 'READY' }
  | { type: 'RESULT'; text: string; chunks?: any[] }
  | { type: 'ERROR'; error: string }
  | { type: 'STATUS'; isReady: boolean; isLoading: boolean };

/**
 * Initialize Whisper model
 * This downloads and loads the model in the background
 */
async function initModel(modelName: string) {
  if (isReady) {
    self.postMessage({ type: 'READY' } as WorkerResponse);
    return;
  }

  if (isLoading) {
    return;
  }

  isLoading = true;
  self.postMessage({ type: 'LOADING', progress: 0 } as WorkerResponse);

  try {
    // Load Whisper model with progress tracking
    transcriber = await pipeline(
      'automatic-speech-recognition',
      modelName,
      {
        // Progress callback
        progress_callback: (progress: any) => {
          if (progress.status === 'downloading') {
            const percent = Math.round((progress.loaded / progress.total) * 100);
            self.postMessage({ type: 'LOADING', progress: percent } as WorkerResponse);
          }
        },
      }
    );

    isReady = true;
    isLoading = false;
    self.postMessage({ type: 'READY' } as WorkerResponse);
  } catch (error: any) {
    isLoading = false;
    self.postMessage({
      type: 'ERROR',
      error: error.message || 'Failed to load Whisper model',
    } as WorkerResponse);
  }
}

/**
 * Transcribe audio using loaded Whisper model
 */
async function transcribe(audio: Float32Array, language?: string) {
  if (!isReady || !transcriber) {
    self.postMessage({
      type: 'ERROR',
      error: 'Model not ready. Please initialize first.',
    } as WorkerResponse);
    return;
  }

  try {
    const result = await transcriber(audio, {
      language: language || null, // null = auto-detect
      task: 'transcribe',
      chunk_length_s: 30,
      stride_length_s: 5,
      return_timestamps: false,
    });

    self.postMessage({
      type: 'RESULT',
      text: result.text,
      chunks: result.chunks,
    } as WorkerResponse);
  } catch (error: any) {
    self.postMessage({
      type: 'ERROR',
      error: error.message || 'Transcription failed',
    } as WorkerResponse);
  }
}

/**
 * Handle messages from main thread
 */
self.addEventListener('message', async (event: MessageEvent<WorkerMessage>) => {
  const { type, ...data } = event.data;

  switch (type) {
    case 'INIT':
      await initModel(data.model);
      break;

    case 'TRANSCRIBE':
      await transcribe(data.audio, data.language);
      break;

    case 'STATUS':
      self.postMessage({
        type: 'STATUS',
        isReady,
        isLoading,
      } as WorkerResponse);
      break;

    default:
      self.postMessage({
        type: 'ERROR',
        error: `Unknown message type: ${type}`,
      } as WorkerResponse);
  }
});

// Export type for TypeScript
export type { WorkerMessage, WorkerResponse };
