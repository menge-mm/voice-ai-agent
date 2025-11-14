# Voice AI Agent

A full-featured voice-enabled AI agent that accepts voice and text input, converts speech to text using Whisper, processes queries with OpenAI GPT, and provides responses via text and text-to-speech using Coqui XTTS-v2.

## Features

- 🎤 **Voice Input**: Record and transcribe speech using OpenAI Whisper (browser-based)
- ⌨️ **Text Input**: Type messages directly
- 🤖 **AI Responses**: Powered by OpenAI GPT-4/GPT-3.5
- 🔊 **Text-to-Speech**: Natural voice output with Coqui XTTS-v2
- 🌍 **Multilingual**: Support for 17+ languages
- 🎭 **Voice Cloning**: Clone any voice from 6 seconds of audio
- 💬 **Conversation History**: Maintains context across exchanges
- 🎨 **Modern UI**: Clean, responsive interface
- 🔒 **Privacy-Focused**: Speech-to-text runs in browser (no server upload)

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│    FastAPI   │────────▶│   OpenAI    │
│  (Whisper   │◀────────│   Backend    │◀────────│     API     │
│   STT)      │         │  (XTTS TTS)  │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
```

**Frontend**: HTML5, JavaScript, Transformers.js (Whisper)
**Backend**: Python, FastAPI, Coqui TTS, OpenAI API
**Models**: Whisper (STT), XTTS-v2 (TTS), GPT-4 (AI)

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- 8GB RAM (16GB recommended)
- GPU (optional, for faster TTS)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/voice-ai-agent.git
cd voice-ai-agent
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Start the backend**
```bash
cd backend
python main.py
```

5. **Open the frontend**
```bash
# In a new terminal
python -m http.server 3000
```

6. **Access the application**

Open your browser to `http://localhost:3000`

## Usage

### Voice Interaction
1. Click the "🎤 Record" button
2. Speak your message
3. Click "⏹️ Stop"
4. Transcription appears automatically
5. AI response is displayed and (optionally) spoken aloud

### Text Interaction
1. Type your message in the text input
2. Press Enter or click "Send"
3. AI response appears
4. Toggle TTS to enable/disable voice output

### Voice Cloning
1. Navigate to Settings
2. Upload a 6+ second audio clip of the target voice
3. Select the voice for future TTS output
4. All responses will use the cloned voice

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo

# Application Settings
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO

# TTS Settings
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
DEFAULT_VOICE_PATH=voices/default_en.wav

# Server Settings
HOST=0.0.0.0
PORT=8000
```

### Supported Languages

STT and TTS support multiple languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)
- Turkish (tr)
- Russian (ru)
- Dutch (nl)
- Czech (cs)
- Arabic (ar)
- Chinese (zh-cn)
- Japanese (ja)
- Hungarian (hu)
- Korean (ko)
- Hindi (hi)

## API Documentation

Once the backend is running, access the interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**POST /api/chat**
```json
{
  "text": "What is the weather today?",
  "enable_tts": true,
  "language": "en",
  "conversation_id": "optional-conv-id"
}
```

**POST /api/tts**
```json
{
  "text": "Hello, how are you?",
  "language": "en"
}
```

**POST /api/tts/clone-voice**
```
Form data:
- text: "Text to speak"
- language: "en"
- voice_file: <audio file>
```

## Development

### Project Structure

```
voice-ai-agent/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── tts_engine.py          # Coqui XTTS integration
│   ├── openai_integration.py  # OpenAI API client
│   └── tests/                 # Backend tests
├── frontend/
│   ├── index.html             # Main UI
│   ├── js/
│   │   ├── whisper-stt.js     # Whisper STT client
│   │   ├── audio-recorder.js  # Audio recording
│   │   └── main.js            # Application logic
│   └── css/
│       └── styles.css         # Styling
├── docs/
│   └── dev/
│       ├── ARCHITECTURE.md
│       ├── STT_IMPLEMENTATION.md
│       ├── TTS_IMPLEMENTATION.md
│       ├── OPENAI_INTEGRATION.md
│       └── SETUP_GUIDE.md
├── requirements.txt
├── .env.example
└── README.md
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# With coverage
pytest --cov=backend backend/tests/
```

### Code Style

```bash
# Format code
black backend/

# Lint
flake8 backend/
pylint backend/
```

## Deployment

### Docker

```bash
# Build image
docker build -t voice-ai-agent .

# Run container
docker run -p 8000:8000 --env-file .env voice-ai-agent
```

### Production Considerations

1. **Use HTTPS**: Required for microphone access
2. **Set CORS**: Configure allowed origins
3. **Rate Limiting**: Implement request limits
4. **Caching**: Cache TTS outputs
5. **Monitoring**: Set up health checks and logging
6. **Database**: Use Redis for conversation storage
7. **Load Balancing**: Use multiple backend instances

See [SETUP_GUIDE.md](docs/dev/SETUP_GUIDE.md) for detailed deployment instructions.

## Technologies Used

### Speech-to-Text (STT)
- **OpenAI Whisper**: State-of-the-art STT model
- **Transformers.js**: Browser-based ML inference
- **WebGPU/WASM**: Hardware acceleration

### Text-to-Speech (TTS)
- **Coqui XTTS-v2**: High-quality multilingual TTS
- **Voice Cloning**: 6-second voice replication
- **17 Languages**: Broad language support

### AI Backend
- **OpenAI GPT-4**: Advanced language understanding
- **FastAPI**: Modern Python web framework
- **Async Processing**: Efficient request handling

## Performance

### Metrics (with GPU)
- **STT Latency**: < 1s for 10s audio (browser-based)
- **AI Response**: 1-3s (OpenAI API)
- **TTS Generation**: 1-2s for short responses
- **Total Round Trip**: 3-6s typical

### Optimization Tips
1. Use GPU for TTS (10x faster)
2. Cache Whisper model in browser
3. Use smaller Whisper model for real-time
4. Enable response streaming
5. Implement audio chunking

## Troubleshooting

### Common Issues

**Microphone not working**
- Ensure HTTPS or localhost
- Grant browser permissions
- Check system microphone settings

**TTS too slow**
- Install CUDA for GPU support
- Use smaller text chunks
- Check GPU memory availability

**OpenAI API errors**
- Verify API key in .env
- Check account credits
- Review rate limits

See [SETUP_GUIDE.md](docs/dev/SETUP_GUIDE.md) for detailed troubleshooting.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **OpenAI**: Whisper and GPT models
- **Coqui AI**: XTTS-v2 TTS model
- **Xenova**: Transformers.js library
- **HuggingFace**: Model hosting and community

## Resources

- [Architecture Documentation](docs/dev/ARCHITECTURE.md)
- [STT Implementation Guide](docs/dev/STT_IMPLEMENTATION.md)
- [TTS Implementation Guide](docs/dev/TTS_IMPLEMENTATION.md)
- [OpenAI Integration Guide](docs/dev/OPENAI_INTEGRATION.md)
- [Setup Guide](docs/dev/SETUP_GUIDE.md)

## Support

- 📖 Documentation: `docs/dev/`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: support@example.com

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Multi-user support
- [ ] Custom voice profiles
- [ ] Emotion detection
- [ ] WebSocket support
- [ ] Offline mode
- [ ] Browser extension
- [ ] Desktop app (Electron)

---

Made with ❤️ using OpenAI Whisper, Coqui XTTS, and GPT-4
