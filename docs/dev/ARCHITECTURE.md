# Voice AI Agent Architecture

## Overview
This voice-AI agent accepts both voice and text input from users, converts speech to text using Whisper, processes the input with OpenAI API, and provides text and optional speech output.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Voice Input  │  │  Text Input  │  │  TTS Toggle     │   │
│  │ (Microphone) │  │  (Text Box)  │  │  (Preference)   │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────────────┘   │
│         │                 │                                  │
│         ▼                 │                                  │
│  ┌──────────────┐         │                                  │
│  │  Whisper STT │         │                                  │
│  │(Transformers.js)       │                                  │
│  └──────┬───────┘         │                                  │
│         │                 │                                  │
│         └────────┬────────┘                                  │
│                  ▼                                           │
│         ┌────────────────┐                                   │
│         │  Text Display  │                                   │
│         └────────┬───────┘                                   │
└──────────────────┼─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              API Endpoints                          │    │
│  │  • POST /api/chat - Process text/audio input        │    │
│  │  • POST /api/tts - Convert text to speech           │    │
│  │  • GET /api/health - Health check                   │    │
│  └─────────────────┬───────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐    │
│  │            OpenAI Integration                       │    │
│  │  • Call OpenAI Chat Completions API                 │    │
│  │  • Handle conversation history                      │    │
│  └─────────────────┬───────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐    │
│  │          TTS Engine (Coqui XTTS-v2)                 │    │
│  │  • Generate speech from text                        │    │
│  │  • Support multiple languages                       │    │
│  │  • Optional voice cloning                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Frontend
- **Technology**: HTML5, JavaScript, CSS
- **STT Library**: Transformers.js with Whisper model
- **Features**:
  - Microphone access for voice input
  - Text area for text input
  - Real-time audio visualization
  - Toggle for TTS preference
  - Display chat history

### Backend
- **Framework**: FastAPI (Python)
- **Key Libraries**:
  - `openai` - OpenAI API client
  - `TTS` - Coqui TTS library for text-to-speech
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `python-multipart` - File upload handling

### Speech-to-Text (STT)
- **Primary Model**: OpenAI Whisper
- **Implementation**: Transformers.js (browser-based)
- **Models Available**:
  - `whisper-tiny` - Fastest, lowest accuracy
  - `whisper-base` - Good balance
  - `whisper-small` - Better accuracy
  - `whisper-medium` - High accuracy
  - `whisper-large-v3` - Best accuracy (requires more resources)
- **Approach**: Following Xenova/whisper-web implementation
  - Client-side inference using WebGPU/WASM
  - No server-side processing needed for STT
  - Privacy-focused (audio stays in browser)

### Text-to-Speech (TTS)
- **Primary Model**: Coqui XTTS-v2
- **Features**:
  - 17 language support
  - Voice cloning from 6-second clips
  - Emotion and style transfer
  - Cross-language voice cloning
- **Supported Languages**: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi
- **Approach**: Following coqui/xtts Space implementation
  - Server-side generation
  - Streaming audio response
  - Configurable voice presets

### OpenAI Integration
- **API**: Chat Completions API
- **Model**: Configurable (default: gpt-4, gpt-3.5-turbo)
- **Features**:
  - Conversation history management
  - Streaming responses (optional)
  - System prompts customization
  - Token usage tracking

## Data Flow

1. **Voice Input Flow**:
   ```
   User speaks → Microphone captures audio → Whisper (Transformers.js)
   → Transcribed text → Display to user → Send to backend
   ```

2. **Text Input Flow**:
   ```
   User types → Text captured → Display to user → Send to backend
   ```

3. **Backend Processing**:
   ```
   Receive text → Call OpenAI API → Get response → Return to frontend
   → (Optional) Generate TTS audio → Stream to frontend
   ```

4. **TTS Flow** (if enabled):
   ```
   OpenAI response text → Coqui XTTS-v2 → Audio file
   → Stream to browser → Audio playback
   ```

## Configuration Options

### User Preferences
- **TTS Enabled**: Toggle text-to-speech output
- **Voice Selection**: Choose from preset voices or custom voice
- **Language**: Select input/output language
- **Model Size**: Choose Whisper model size (speed vs accuracy)
- **OpenAI Model**: Select GPT model variant

### System Configuration
- **OpenAI API Key**: Required for backend
- **TTS Voice Path**: Optional custom voice file
- **Max Conversation History**: Limit context tokens
- **Audio Quality**: Bitrate and sample rate for TTS
- **CORS Settings**: Frontend origin whitelist

## Scalability Considerations

### Client-Side (Browser)
- **WebGPU Support**: Fallback to WASM if unavailable
- **Model Caching**: Cache Whisper models locally
- **Audio Chunking**: Process long audio in segments

### Server-Side
- **Async Processing**: FastAPI async endpoints
- **Model Loading**: Load TTS model once at startup
- **Caching**: Cache OpenAI responses for common queries
- **Rate Limiting**: Prevent API abuse
- **Queue System**: Handle concurrent TTS requests

## Security Considerations

1. **API Key Protection**: Store OpenAI key in environment variables
2. **CORS Configuration**: Restrict origins
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Prevent DoS attacks
5. **Audio File Validation**: Check file types and sizes
6. **Session Management**: Implement user sessions for conversation history

## Performance Optimization

### Frontend
- Lazy load Whisper models
- Use smaller models for real-time processing
- Implement audio buffering
- Debounce text input

### Backend
- Keep TTS model in memory
- Use connection pooling for OpenAI API
- Implement response caching
- Stream responses instead of buffering

## Future Enhancements

1. **Multi-user Support**: Add user authentication and isolated sessions
2. **Voice Profiles**: Save custom voice clones per user
3. **Language Detection**: Auto-detect input language
4. **Emotion Detection**: Analyze and mirror user emotions
5. **WebSocket Support**: Real-time bidirectional communication
6. **Mobile Support**: Progressive Web App (PWA)
7. **Offline Mode**: Cache models and enable offline functionality
8. **Analytics**: Track usage patterns and performance metrics
