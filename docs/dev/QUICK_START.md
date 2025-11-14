# Quick Start Guide

Get up and running with Voice AI Agent in 5 minutes!

## Prerequisites

- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/voice-ai-agent.git
cd voice-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
nano .env  # or use your preferred editor
```

### 3. Add a Default Voice (Important!)

The TTS system needs a reference voice file. You have two options:

**Option A: Record your own (Recommended)**
```bash
# Record 10 seconds of your voice and save as voices/default.wav
# You can use any audio recording software
```

**Option B: Use a sample voice**
```bash
# Download a sample voice from Mozilla Common Voice or similar
# Save it as voices/default.wav
```

Then update your `.env`:
```env
DEFAULT_VOICE_PATH=voices/default.wav
```

### 4. Run

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd ..
python -m http.server 3000
```

### 5. Open Browser

Navigate to: `http://localhost:3000`

## First Steps

### Test Voice Input
1. Click the "🎤 Record" button
2. Say something (e.g., "Hello, how are you?")
3. Click "⏹️ Stop"
4. Watch the transcription appear
5. Get AI response (text and audio)

### Test Text Input
1. Type a message in the text box
2. Press Enter or click "Send"
3. Get AI response

## Common Issues

### "TTS engine not available"
- **Problem**: No default voice file configured
- **Solution**: Add a voice file and set `DEFAULT_VOICE_PATH` in `.env`

### "OpenAI authentication failed"
- **Problem**: Invalid or missing API key
- **Solution**: Check your `.env` file has correct `OPENAI_API_KEY`

### "Microphone access denied"
- **Problem**: Browser blocked microphone
- **Solution**: Grant permission when prompted, or check browser settings

### Slow TTS generation
- **Problem**: Running on CPU instead of GPU
- **Solution**: Install CUDA-enabled PyTorch:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
- Check [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed configuration
- Explore [STT_IMPLEMENTATION.md](./STT_IMPLEMENTATION.md) for STT details
- Review [TTS_IMPLEMENTATION.md](./TTS_IMPLEMENTATION.md) for TTS details

## Need Help?

- Check the full documentation in `docs/dev/`
- Open an issue on GitHub
- Review the troubleshooting section in [SETUP_GUIDE.md](./SETUP_GUIDE.md)

## What's Next?

Try these features:
- Voice cloning: Upload your own voice sample
- Multiple languages: Change the language dropdown
- Conversation history: Have a multi-turn conversation
- Custom system prompts: Modify the AI's personality

Enjoy using Voice AI Agent! 🎉
