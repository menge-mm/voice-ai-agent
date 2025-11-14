/**
 * Voice AI Agent - Main Application
 * Integrates STT, OpenAI, and TTS
 */

import { WhisperSTT } from './whisper-stt.js';
import { AudioRecorder } from './audio-recorder.js';
import { AudioVisualizer } from './audio-visualizer.js';

class VoiceAIAgent {
    constructor() {
        // Backend API URL
        this.apiUrl = this.getApiUrl();

        // Components
        this.whisper = new WhisperSTT();
        this.recorder = new AudioRecorder();
        this.visualizer = null;

        // State
        this.conversationId = null;
        this.isProcessing = false;

        // UI Elements
        this.elements = {
            chatContainer: document.getElementById('chatContainer'),
            recordBtn: document.getElementById('recordBtn'),
            stopBtn: document.getElementById('stopBtn'),
            sendBtn: document.getElementById('sendBtn'),
            clearBtn: document.getElementById('clearBtn'),
            textInput: document.getElementById('textInput'),
            status: document.getElementById('status'),
            ttsToggle: document.getElementById('ttsToggle'),
            languageSelect: document.getElementById('languageSelect'),
            audioVisualizer: document.getElementById('audioVisualizer'),
            loadingOverlay: document.getElementById('loadingOverlay')
        };

        this.init();
    }

    getApiUrl() {
        // Try to get from environment or use default
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }
        // For production, use same origin
        return window.location.origin;
    }

    async init() {
        console.log('Initializing Voice AI Agent...');

        // Initialize visualizer
        this.visualizer = new AudioVisualizer(this.elements.audioVisualizer);

        // Set up event listeners
        this.setupEventListeners();

        // Test backend connection
        await this.testBackendConnection();

        // Initialize Whisper model
        this.showLoading('Loading Whisper model...');
        try {
            await this.whisper.initialize();
            this.hideLoading();
            this.showStatus('Ready', 'ready');
            console.log('✓ Voice AI Agent initialized successfully');
        } catch (error) {
            this.hideLoading();
            this.showError('Failed to load Whisper model. Voice input will not work.');
            console.error('Initialization error:', error);
        }
    }

    setupEventListeners() {
        // Record button
        this.elements.recordBtn.addEventListener('click', () => this.startRecording());

        // Stop button
        this.elements.stopBtn.addEventListener('click', () => this.stopRecording());

        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.sendTextMessage());

        // Text input - send on Enter (Shift+Enter for new line)
        this.elements.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });

        // Clear button
        this.elements.clearBtn.addEventListener('click', () => this.clearChat());
    }

    async testBackendConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/api/health`);
            if (response.ok) {
                const data = await response.json();
                console.log('✓ Backend connection successful:', data);
                return true;
            } else {
                console.warn('Backend health check failed:', response.status);
                this.showError('Backend server is not responding. Please start the server.');
                return false;
            }
        } catch (error) {
            console.error('✗ Backend connection failed:', error);
            this.showError('Cannot connect to backend server. Please ensure it is running on ' + this.apiUrl);
            return false;
        }
    }

    async startRecording() {
        try {
            this.showStatus('Recording...', 'recording');
            this.elements.recordBtn.disabled = true;
            this.elements.stopBtn.disabled = false;

            await this.recorder.startRecording();
            this.visualizer.start(this.recorder.getStream());

        } catch (error) {
            console.error('Recording error:', error);
            this.showError(error.message);
            this.resetRecordingUI();
        }
    }

    async stopRecording() {
        try {
            this.showStatus('Processing...', 'processing');
            this.visualizer.stop();

            // Stop recording and get audio data
            const audioData = await this.recorder.stopRecording();

            // Transcribe audio
            this.showStatus('Transcribing...', 'processing');
            const result = await this.whisper.transcribe(audioData, {
                language: this.elements.languageSelect.value === 'en' ? null : this.elements.languageSelect.value,
                return_timestamps: false
            });

            const transcription = result.text;

            if (!transcription || transcription.trim() === '') {
                throw new Error('No speech detected. Please try again.');
            }

            // Display transcription
            this.addMessage(transcription, 'transcription', 'Transcribed');

            // Send to backend
            await this.sendToBackend(transcription);

            this.resetRecordingUI();
            this.showStatus('Ready', 'ready');

        } catch (error) {
            console.error('Processing error:', error);
            this.showError(error.message);
            this.resetRecordingUI();
        }
    }

    async sendTextMessage() {
        const text = this.elements.textInput.value.trim();

        if (!text) {
            return;
        }

        // Clear input
        this.elements.textInput.value = '';

        // Add user message
        this.addMessage(text, 'user', 'You');

        // Send to backend
        await this.sendToBackend(text);
    }

    async sendToBackend(text) {
        if (this.isProcessing) {
            console.warn('Already processing a request');
            return;
        }

        this.isProcessing = true;
        this.showStatus('Thinking...', 'processing');

        try {
            const requestBody = {
                text: text,
                enable_tts: this.elements.ttsToggle.checked,
                language: this.elements.languageSelect.value,
                conversation_id: this.conversationId,
                temperature: 0.7
            };

            console.log('Sending to backend:', requestBody);

            const response = await fetch(`${this.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Backend request failed');
            }

            const data = await response.json();

            console.log('✓ Received response:', data);

            // Store conversation ID
            this.conversationId = data.conversation_id;

            // Add assistant message
            this.addMessage(data.response_text, 'assistant', 'AI');

            // Play TTS if available
            if (data.audio_url) {
                await this.playTTS(data.audio_url);
            }

            this.showStatus('Ready', 'ready');

        } catch (error) {
            console.error('✗ Backend request failed:', error);
            this.showError('Failed to get AI response: ' + error.message);
            this.showStatus('Ready', 'ready');
        } finally {
            this.isProcessing = false;
        }
    }

    async playTTS(audioUrl) {
        try {
            // Create audio element
            const audio = new Audio(this.apiUrl + audioUrl);

            // Add to last message
            const lastMessage = this.elements.chatContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('assistant')) {
                const audioPlayer = document.createElement('div');
                audioPlayer.className = 'audio-player';
                audioPlayer.innerHTML = `<audio controls src="${this.apiUrl + audioUrl}"></audio>`;
                lastMessage.appendChild(audioPlayer);
            }

            // Auto-play if TTS is enabled
            if (this.elements.ttsToggle.checked) {
                await audio.play();
            }

        } catch (error) {
            console.error('✗ TTS playback failed:', error);
            // Don't show error to user, just log it
        }
    }

    addMessage(text, type, label) {
        // Remove welcome message if present
        const welcomeMessage = this.elements.chatContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        const labelDiv = document.createElement('div');
        labelDiv.className = 'message-label';
        labelDiv.textContent = label;

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;

        messageDiv.appendChild(labelDiv);
        messageDiv.appendChild(textDiv);

        this.elements.chatContainer.appendChild(messageDiv);

        // Scroll to bottom
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    clearChat() {
        // Clear conversation history
        if (this.conversationId) {
            fetch(`${this.apiUrl}/api/conversation/${this.conversationId}`, {
                method: 'DELETE'
            }).catch(err => console.error('Failed to clear conversation:', err));

            this.conversationId = null;
        }

        // Clear UI
        this.elements.chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome! 👋</h2>
                <p>Start a conversation by recording your voice or typing a message.</p>
            </div>
        `;

        this.showStatus('Ready', 'ready');
        console.log('✓ Chat cleared');
    }

    showStatus(text, type = '') {
        this.elements.status.textContent = text;
        this.elements.status.className = `status ${type}`;
    }

    showError(message) {
        // Add error message to chat
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = '⚠️ ' + message;

        this.elements.chatContainer.appendChild(errorDiv);
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    showLoading(message = 'Loading...') {
        this.elements.loadingOverlay.classList.remove('hidden');
        const loadingText = this.elements.loadingOverlay.querySelector('p');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    hideLoading() {
        this.elements.loadingOverlay.classList.add('hidden');
    }

    resetRecordingUI() {
        this.elements.recordBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.visualizer.stop();
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.voiceAIAgent = new VoiceAIAgent();
    });
} else {
    window.voiceAIAgent = new VoiceAIAgent();
}

export default VoiceAIAgent;
