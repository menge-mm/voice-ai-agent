/**
 * Whisper Speech-to-Text Client
 * Uses Transformers.js for browser-based STT
 * Following implementation from Xenova/whisper-web
 */

export class WhisperSTT {
    constructor(modelName = 'Xenova/whisper-base') {
        this.modelName = modelName;
        this.transcriber = null;
        this.isLoading = false;
        this.isReady = false;
    }

    async initialize() {
        if (this.isReady) {
            console.log('Whisper model already loaded');
            return;
        }

        if (this.isLoading) {
            console.log('Whisper model is currently loading...');
            return;
        }

        this.isLoading = true;
        console.log(`Loading Whisper model: ${this.modelName}...`);

        try {
            // Dynamically import Transformers.js
            const { pipeline } = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.9.0');

            // Create transcription pipeline
            this.transcriber = await pipeline(
                'automatic-speech-recognition',
                this.modelName
            );

            this.isReady = true;
            console.log('✓ Whisper model loaded successfully');

        } catch (error) {
            console.error('✗ Failed to load Whisper model:', error);
            throw new Error(`Failed to load Whisper model: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    async transcribe(audioData, options = {}) {
        if (!this.isReady) {
            await this.initialize();
        }

        const {
            language = null, // Auto-detect if null
            task = 'transcribe', // or 'translate' for translation to English
            chunk_length_s = 30, // Process in 30-second chunks
            stride_length_s = 5, // 5-second stride between chunks
            return_timestamps = false
        } = options;

        try {
            console.log('Transcribing audio...');

            const result = await this.transcriber(audioData, {
                language,
                task,
                chunk_length_s,
                stride_length_s,
                return_timestamps
            });

            console.log('✓ Transcription complete:', result.text);
            return result;

        } catch (error) {
            console.error('✗ Transcription error:', error);
            throw new Error(`Transcription failed: ${error.message}`);
        }
    }

    getStatus() {
        return {
            isReady: this.isReady,
            isLoading: this.isLoading,
            modelName: this.modelName
        };
    }
}

export default WhisperSTT;
