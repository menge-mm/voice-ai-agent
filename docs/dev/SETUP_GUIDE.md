# Voice AI Agent - Setup Guide

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **Node.js**: 16+ (for frontend development)
- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: Optional but recommended for TTS (CUDA-capable NVIDIA GPU)
- **Disk Space**: 5GB free space for models and dependencies

### Required Accounts
1. **OpenAI Account**
   - Sign up at https://platform.openai.com/
   - Create an API key
   - Add credits to your account

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-username/voice-ai-agent.git
cd voice-ai-agent
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Python Dependencies

```bash
# Install all backend dependencies
pip install -r requirements.txt
```

**Note**: Installing TTS with CUDA support requires PyTorch with CUDA. If you have a GPU:

```bash
# Install PyTorch with CUDA 11.8 (adjust version as needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo
DEFAULT_LANGUAGE=en
```

### 5. Download Default Voice Files (Optional)

For better TTS quality, you can add default voice samples:

```bash
# Create voices directory
mkdir -p voices

# Add your default voice files (6+ seconds of clear speech)
# voices/en_default.wav
# voices/es_default.wav
# etc.
```

You can record your own or use sample voices from:
- https://commonvoice.mozilla.org/
- https://librivox.org/

### 6. Start the Backend Server

```bash
# Navigate to backend directory
cd backend

# Start the server
python main.py
```

The server will start on `http://localhost:8000`

You should see:
```
INFO:     Starting Voice AI Agent API...
INFO:     Loading XTTS model on cuda...
INFO:     XTTS model loaded successfully
INFO:     OpenAI client connected successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Open Frontend

```bash
# In a new terminal, navigate to project root
cd /path/to/voice-ai-agent

# Serve frontend files
# Option 1: Using Python's built-in server
python -m http.server 3000

# Option 2: Using Node.js http-server
npx http-server -p 3000
```

Open your browser to `http://localhost:3000`

## Verification

### Test Backend Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "tts_loaded": true,
  "openai_connected": true
}
```

### Test STT in Browser

1. Open `http://localhost:3000`
2. Click "Record" button
3. Speak a short sentence
4. Click "Stop"
5. Verify transcription appears

### Test Complete Flow

1. Record voice input or type text
2. Verify transcription (if voice)
3. See AI response appear
4. If TTS enabled, hear audio response

## Troubleshooting

### GPU Not Detected

**Issue**: TTS using CPU instead of GPU

**Solution**:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### OpenAI API Key Error

**Issue**: "OpenAI authentication failed"

**Solution**:
1. Verify API key is correct in `.env`
2. Check API key has not expired
3. Verify you have credits in your OpenAI account
4. Test key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### TTS Model Loading Failed

**Issue**: "Failed to load XTTS model"

**Solution**:
```bash
# Clear TTS cache
rm -rf ~/.cache/tts

# Reinstall TTS
pip uninstall TTS
pip install TTS==0.20.0

# Try loading model manually
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')"
```

### CORS Errors in Browser

**Issue**: CORS policy blocking requests

**Solution**: Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Microphone Not Working

**Issue**: Browser cannot access microphone

**Solution**:
1. Use HTTPS or localhost (required for microphone access)
2. Grant microphone permissions in browser
3. Check system microphone settings
4. Try different browser (Chrome/Edge recommended)

### Slow TTS Generation

**Issue**: TTS takes too long to generate

**Solutions**:
1. **Use GPU**: Ensure CUDA is properly installed
2. **Reduce text length**: Break long responses into smaller chunks
3. **Preload model**: Model loads on startup, not per request
4. **Check GPU memory**: Close other GPU-intensive applications

### Out of Memory Error

**Issue**: CUDA out of memory or system RAM exhausted

**Solutions**:
```python
# Reduce batch size in tts_engine.py
# Use smaller Whisper model in frontend
# Close other applications
# Restart backend server
```

## Development Setup

### Hot Reload for Backend

```bash
# Install development dependencies
pip install watchdog

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
# Install live-server for auto-refresh
npm install -g live-server

# Start with live reload
live-server --port=3000
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# Frontend tests (if using Jest)
npm test
```

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY .env .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "backend/main.py"]
```

Build and run:
```bash
docker build -t voice-ai-agent .
docker run -p 8000:8000 --env-file .env voice-ai-agent
```

### Environment Variables for Production

```env
# .env.production
OPENAI_API_KEY=sk-prod-key-here
OPENAI_MODEL=gpt-4-turbo
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
MAX_REQUESTS_PER_MINUTE=60
TTS_CACHE_DIR=/var/cache/tts
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/voice-ai-agent

upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /var/www/voice-ai-agent/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Systemd Service

```ini
# /etc/systemd/system/voice-ai-agent.service

[Unit]
Description=Voice AI Agent Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/voice-ai-agent
Environment="PATH=/opt/voice-ai-agent/venv/bin"
ExecStart=/opt/voice-ai-agent/venv/bin/python backend/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable voice-ai-agent
sudo systemctl start voice-ai-agent
sudo systemctl status voice-ai-agent
```

## Performance Tuning

### Backend Optimization

```python
# main.py - Add these configurations

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1

# Connection pool
max_connections = 100
keepalive = 5

# Timeout settings
timeout = 300  # 5 minutes for TTS generation
```

### Database for Conversation Storage

```python
# For production, use Redis for conversation storage
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store conversation
redis_client.setex(
    f"conversation:{conv_id}",
    3600,  # 1 hour expiry
    json.dumps(conversation_data)
)
```

## Monitoring

### Health Check Endpoint

```bash
# Set up monitoring
*/5 * * * * curl -f http://localhost:8000/api/health || alert-team
```

### Logging Configuration

```python
# logging_config.py

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/voice-ai-agent.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'default',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
}
```

## Support

For issues and questions:
1. Check documentation in `docs/dev/`
2. Review error logs in `logs/`
3. Open an issue on GitHub
4. Contact support team

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview
- Review [STT_IMPLEMENTATION.md](./STT_IMPLEMENTATION.md) for STT details
- Check [TTS_IMPLEMENTATION.md](./TTS_IMPLEMENTATION.md) for TTS details
- See [OPENAI_INTEGRATION.md](./OPENAI_INTEGRATION.md) for API integration
