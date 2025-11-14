# Speech-to-Text (STT) Implementation Guide

## Overview
This document details the implementation of Speech-to-Text functionality using OpenAI's Whisper model via Transformers.js, following the approach used in popular HuggingFace Spaces.

## Why Whisper?

Based on research of popular HuggingFace Spaces and industry trends (2025):

1. **Most Popular Choice**: Whisper is the #1 STT model in open-source community
2. **High Accuracy**: Trained on 5M+ hours of labeled data
3. **Multilingual**: Supports 99+ languages
4. **Zero-shot Performance**: Generalizes well without fine-tuning
5. **Strong Community**: Massive ecosystem of projects and tools
6. **Browser Support**: Can run client-side via Transformers.js

## Popular HuggingFace Spaces Using Whisper

### 1. Xenova/whisper-web
- **Approach**: Client-side inference using Transformers.js
- **Benefits**:
  - Privacy-preserving (audio never leaves browser)
  - No server costs for STT
  - Fast processing with WebGPU
- **Implementation**: Uses WebGPU with WASM fallback

### 2. Xenova/realtime-whisper-webgpu
- **Approach**: Real-time transcription with WebGPU acceleration
- **Benefits**:
  - Ultra-low latency
  - Streaming transcription
  - Hardware acceleration

### 3. openai/whisper (Official)
- **Approach**: Server-side processing with GPU
- **Benefits**:
  - Can use larger models
  - Centralized processing
- **Drawbacks**:
  - Privacy concerns
  - Server costs
  - Network latency

## Our Implementation: Client-Side with Transformers.js

We follow the **Xenova/whisper-web** approach for optimal user experience.

### Technology Stack

```javascript
// Core Libraries
import { pipeline } from '@xenova/transformers';

// Audio Processing
MediaRecorder API (native browser)
Web Audio API (native browser)
```

### Model Selection

Available Whisper models (ordered by size/performance):

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| whisper-tiny | 39M | ★★★★★ | ★★☆☆☆ | Real-time, low-end devices |
| whisper-base | 74M | ★★★★☆ | ★★★☆☆ | Balanced for most use cases |
| whisper-small | 244M | ★★★☆☆ | ★★★★☆ | Good accuracy, reasonable speed |
| whisper-medium | 769M | ★★☆☆☆ | ★★★★★ | High accuracy |
| whisper-large-v3 | 1550M | ★☆☆☆☆ | ★★★★★ | Best accuracy, high-end only |

**Recommended**: `whisper-base` for real-time, `whisper-small` for quality

### Implementation Steps

#### 1. Initialize Whisper Pipeline

```javascript
// whisper-stt.js

class WhisperSTT {
    constructor() {
        this.transcriber = null;
        this.modelName = 'Xenova/whisper-base';
        this.isLoading = false;
        this.isReady = false;
    }

    async initialize() {
        if (this.isReady) return;

        this.isLoading = true;
        console.log('Loading Whisper model...');

        try {
            // Create transcription pipeline
            this.transcriber = await pipeline(
                'automatic-speech-recognition',
                this.modelName,
                {
                    // Use WebGPU if available, fallback to WASM
                    device: 'webgpu',
                    dtype: 'fp32'
                }
            );

            this.isReady = true;
            console.log('Whisper model loaded successfully');
        } catch (error) {
            console.error('Failed to load Whisper model:', error);
            throw error;
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
            const result = await this.transcriber(audioData, {
                language,
                task,
                chunk_length_s,
                stride_length_s,
                return_timestamps
            });

            return result;
        } catch (error) {
            console.error('Transcription error:', error);
            throw error;
        }
    }
}

export default WhisperSTT;
```

#### 2. Audio Recording and Processing

```javascript
// audio-recorder.js

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
    }

    async startRecording() {
        try {
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

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus'
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
            console.log('Recording started');

        } catch (error) {
            console.error('Failed to start recording:', error);
            throw error;
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
                    // Create audio blob
                    const audioBlob = new Blob(this.audioChunks, {
                        type: 'audio/webm;codecs=opus'
                    });

                    // Convert to format suitable for Whisper
                    const audioData = await this.convertToWhisperFormat(audioBlob);

                    // Stop all tracks
                    this.stream.getTracks().forEach(track => track.stop());

                    this.isRecording = false;
                    resolve(audioData);
                } catch (error) {
                    reject(error);
                }
            };

            this.mediaRecorder.stop();
        });
    }

    async convertToWhisperFormat(blob) {
        // Convert blob to ArrayBuffer
        const arrayBuffer = await blob.arrayBuffer();

        // Create audio context
        const audioContext = new AudioContext({ sampleRate: 16000 });

        // Decode audio data
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // Get mono channel data
        const channelData = audioBuffer.getChannelData(0);

        // Convert to Float32Array (Whisper format)
        return channelData;
    }

    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.stream.getTracks().forEach(track => track.stop());
            this.audioChunks = [];
            this.isRecording = false;
        }
    }
}

export default AudioRecorder;
```

#### 3. Real-time Visualization (Optional)

```javascript
// audio-visualizer.js

class AudioVisualizer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.analyser = null;
        this.dataArray = null;
        this.animationId = null;
    }

    start(stream) {
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);

        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = 2048;

        source.connect(this.analyser);

        const bufferLength = this.analyser.frequencyBinCount;
        this.dataArray = new Uint8Array(bufferLength);

        this.draw();
    }

    draw() {
        this.animationId = requestAnimationFrame(() => this.draw());

        this.analyser.getByteTimeDomainData(this.dataArray);

        this.ctx.fillStyle = 'rgb(240, 240, 240)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = 'rgb(59, 130, 246)'; // Blue color

        this.ctx.beginPath();

        const sliceWidth = this.canvas.width / this.dataArray.length;
        let x = 0;

        for (let i = 0; i < this.dataArray.length; i++) {
            const v = this.dataArray[i] / 128.0;
            const y = (v * this.canvas.height) / 2;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        this.ctx.lineTo(this.canvas.width, this.canvas.height / 2);
        this.ctx.stroke();
    }

    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

export default AudioVisualizer;
```

## Integration Example

```javascript
// main.js

import WhisperSTT from './whisper-stt.js';
import AudioRecorder from './audio-recorder.js';
import AudioVisualizer from './audio-visualizer.js';

class VoiceAIAgent {
    constructor() {
        this.whisper = new WhisperSTT();
        this.recorder = new AudioRecorder();
        this.visualizer = null;

        this.setupUI();
    }

    async initialize() {
        // Preload Whisper model
        await this.whisper.initialize();
        console.log('Voice AI Agent ready');
    }

    setupUI() {
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const canvas = document.getElementById('audioVisualizer');

        this.visualizer = new AudioVisualizer(canvas);

        recordBtn.addEventListener('click', async () => {
            await this.startRecording();
        });

        stopBtn.addEventListener('click', async () => {
            await this.stopRecording();
        });
    }

    async startRecording() {
        try {
            await this.recorder.startRecording();
            this.visualizer.start(this.recorder.stream);

            // Update UI
            document.getElementById('recordBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('status').textContent = 'Recording...';
        } catch (error) {
            console.error('Recording failed:', error);
            alert('Failed to start recording: ' + error.message);
        }
    }

    async stopRecording() {
        try {
            // Update UI
            document.getElementById('status').textContent = 'Transcribing...';

            // Stop recording and get audio data
            const audioData = await this.recorder.stopRecording();
            this.visualizer.stop();

            // Transcribe
            const result = await this.whisper.transcribe(audioData, {
                language: null, // Auto-detect
                return_timestamps: false
            });

            // Display transcription
            const transcription = result.text;
            document.getElementById('transcription').textContent = transcription;

            // Send to backend for processing
            await this.sendToBackend(transcription);

            // Update UI
            document.getElementById('recordBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('status').textContent = 'Ready';

        } catch (error) {
            console.error('Transcription failed:', error);
            alert('Failed to transcribe audio: ' + error.message);
        }
    }

    async sendToBackend(text) {
        // Will be implemented in backend integration
        console.log('Sending to backend:', text);
    }
}

// Initialize app
const app = new VoiceAIAgent();
app.initialize();
```

## Browser Compatibility

### Required Features
- **MediaRecorder API**: Chrome 47+, Firefox 25+, Safari 14.1+
- **Web Audio API**: All modern browsers
- **WebGPU** (optional): Chrome 113+, Edge 113+
- **WebAssembly**: All modern browsers

### Fallback Strategy
1. Try WebGPU acceleration
2. Fall back to WASM if WebGPU unavailable
3. Show error if neither is supported

## Performance Optimization

### 1. Model Caching
```javascript
// Cache model in IndexedDB for faster subsequent loads
import { env } from '@xenova/transformers';

// Set cache location
env.cacheDir = './.cache';
env.allowLocalModels = false;
env.allowRemoteModels = true;
```

### 2. Lazy Loading
```javascript
// Only load model when first needed
async ensureModelLoaded() {
    if (!this.isReady && !this.isLoading) {
        await this.initialize();
    }
}
```

### 3. Progressive Enhancement
```javascript
// Start with smaller model, offer upgrade
async upgradeModel(newModel) {
    this.modelName = newModel;
    this.isReady = false;
    await this.initialize();
}
```

## Error Handling

```javascript
async transcribe(audioData, options = {}) {
    try {
        // Check if model is ready
        if (!this.isReady) {
            await this.initialize();
        }

        // Validate audio data
        if (!audioData || audioData.length === 0) {
            throw new Error('Invalid audio data');
        }

        // Perform transcription
        const result = await this.transcriber(audioData, options);

        return result;

    } catch (error) {
        // Handle specific error types
        if (error.name === 'NotAllowedError') {
            throw new Error('Microphone access denied');
        } else if (error.name === 'NotFoundError') {
            throw new Error('No microphone found');
        } else if (error.message.includes('WebGPU')) {
            console.warn('WebGPU not available, falling back to WASM');
            // Retry with WASM
        } else {
            throw new Error(`Transcription failed: ${error.message}`);
        }
    }
}
```

## Testing

### Unit Tests
```javascript
// test-whisper-stt.js
import { describe, it, expect } from 'vitest';
import WhisperSTT from './whisper-stt.js';

describe('WhisperSTT', () => {
    it('should initialize successfully', async () => {
        const whisper = new WhisperSTT();
        await whisper.initialize();
        expect(whisper.isReady).toBe(true);
    });

    it('should transcribe audio', async () => {
        const whisper = new WhisperSTT();
        // Use sample audio data
        const audioData = new Float32Array(16000); // 1 second of silence
        const result = await whisper.transcribe(audioData);
        expect(result).toHaveProperty('text');
    });
});
```

## Deployment Considerations

1. **CDN for Models**: Models are loaded from HuggingFace CDN
2. **Service Worker**: Cache models for offline use
3. **Compression**: Models are already compressed in ONNX format
4. **Progressive Loading**: Show loading progress to users

## References

- Xenova/whisper-web Space: https://huggingface.co/spaces/Xenova/whisper-web
- Transformers.js Documentation: https://huggingface.co/docs/transformers.js
- Whisper Model Card: https://huggingface.co/openai/whisper-base
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
