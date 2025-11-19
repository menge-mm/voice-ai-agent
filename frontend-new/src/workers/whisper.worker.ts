import { pipeline, env } from '@xenova/transformers';

// Configure environment
env.allowLocalModels = false;
env.allowRemoteModels = true;

console.log('✓ Whisper worker loaded');

class WhisperPipeline {
  static task = 'automatic-speech-recognition' as const;
  static model = 'Xenova/whisper-tiny.en';
  static instance: any = null;

  static async getInstance(progress_callback?: ((progress: any) => void)) {
    if (this.instance === null) {
      console.log(`Loading Whisper model: ${this.model}...`);
      this.instance = await pipeline(this.task, this.model, { progress_callback });
    }
    return this.instance;
  }
}

// Listen for messages from the main thread
self.addEventListener('message', async (event) => {
  console.log('Worker received message:', event.data.type);
  const { type, audio, language } = event.data;

  if (type === 'INIT') {
    try {
      // Load model
      await WhisperPipeline.getInstance((progress) => {
        console.log('Progress:', progress);
        self.postMessage({ type: 'LOADING', progress: progress });
      });

      console.log('Model ready, sending READY message');
      self.postMessage({ type: 'READY' });
    } catch (error: any) {
      console.error('Failed to initialize:', error);
      self.postMessage({ type: 'ERROR', error: error.message });
    }
  } else if (type === 'TRANSCRIBE') {
    // Get the transcriber
    const transcriber = await WhisperPipeline.getInstance();

    // Perform transcription
    try {
      const result = await transcriber(audio, {
        language: language || null,
        task: 'transcribe',
        chunk_length_s: 30,
        stride_length_s: 5,
        return_timestamps: false,
      });

      self.postMessage({
        type: 'RESULT',
        text: result.text,
      });
    } catch (error: any) {
      self.postMessage({
        type: 'ERROR',
        error: error.message || 'Transcription failed',
      });
    }
  }
});
