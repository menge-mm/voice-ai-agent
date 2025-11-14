/**
 * Audio Recorder
 * Handles microphone recording and audio processing
 */

export class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.audioContext = null;
    }

    async startRecording() {
        try {
            console.log('Requesting microphone access...');

            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1, // Mono
                    sampleRate: 16000, // Whisper expects 16kHz
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            console.log('✓ Microphone access granted');

            // Create MediaRecorder
            const mimeType = this.getSupportedMimeType();
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType
            });

            this.audioChunks = [];

            // Collect audio data
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            console.log('✓ Recording started');

        } catch (error) {
            console.error('✗ Failed to start recording:', error);

            if (error.name === 'NotAllowedError') {
                throw new Error('Microphone access denied. Please grant permission and try again.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No microphone found. Please connect a microphone and try again.');
            } else {
                throw new Error(`Failed to start recording: ${error.message}`);
            }
        }
    }

    async stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder || !this.isRecording) {
                reject(new Error('Not recording'));
                return;
            }

            this.mediaRecorder.onstop = async () => {
                try {
                    console.log('Processing recorded audio...');

                    // Create audio blob
                    const mimeType = this.getSupportedMimeType();
                    const audioBlob = new Blob(this.audioChunks, {
                        type: mimeType
                    });

                    // Convert to format suitable for Whisper
                    const audioData = await this.convertToWhisperFormat(audioBlob);

                    // Stop all tracks
                    this.stream.getTracks().forEach(track => track.stop());

                    this.isRecording = false;
                    console.log('✓ Recording stopped and processed');

                    resolve(audioData);
                } catch (error) {
                    console.error('✗ Error processing audio:', error);
                    reject(error);
                }
            };

            this.mediaRecorder.stop();
        });
    }

    async convertToWhisperFormat(blob) {
        try {
            // Convert blob to ArrayBuffer
            const arrayBuffer = await blob.arrayBuffer();

            // Create audio context with 16kHz sample rate (Whisper requirement)
            if (!this.audioContext) {
                this.audioContext = new AudioContext({ sampleRate: 16000 });
            }

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            // Get mono channel data
            const channelData = audioBuffer.getChannelData(0);

            // Convert to Float32Array (Whisper format)
            return new Float32Array(channelData);

        } catch (error) {
            console.error('✗ Error converting audio format:', error);
            throw new Error(`Failed to convert audio format: ${error.message}`);
        }
    }

    getSupportedMimeType() {
        // Try different mime types in order of preference
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/mpeg'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                console.log(`Using mime type: ${type}`);
                return type;
            }
        }

        // Fallback to default
        console.warn('No preferred mime type supported, using default');
        return '';
    }

    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.stream.getTracks().forEach(track => track.stop());
            this.audioChunks = [];
            this.isRecording = false;
            console.log('✓ Recording cancelled');
        }
    }

    getStream() {
        return this.stream;
    }

    static async checkMicrophonePermission() {
        try {
            const result = await navigator.permissions.query({ name: 'microphone' });
            return result.state; // 'granted', 'denied', or 'prompt'
        } catch (error) {
            // Permissions API not supported in all browsers
            console.warn('Permissions API not supported');
            return 'prompt';
        }
    }
}

export default AudioRecorder;
