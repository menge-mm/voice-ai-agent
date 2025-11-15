https://huggingface.co/spaces/course-demos/speech-to-speech-translation/resolve/main/app.py
https://huggingface.co/spaces/gobeldan/insanely-fast-whisper-webui/resolve/main/app.py
https://huggingface.co/spaces/gobeldan/insanely-fast-whisper-webui/resolve/main/languages.py
https://huggingface.co/spaces/gobeldan/insanely-fast-whisper-webui/resolve/main/subtitle_manager.py    Started server process [61074]
INFO:     Waiting for application startup.
2025-11-15 03:01:10,851 - main - INFO - ============================================================
2025-11-15 03:01:10,851 - main - INFO - Starting Voice AI Agent API...
2025-11-15 03:01:10,851 - main - INFO - ============================================================
2025-11-15 03:01:10,851 - main - INFO - Initializing TTS engine...
2025-11-15 03:01:10,851 - tts_engine - INFO - Loading TTS model 'microsoft/speecht5_tts' on cpu...
2025-11-15 03:01:14,290 - tts_engine - INFO - Loading speaker embeddings...
2025-11-15 03:01:14,502 - tts_engine - ERROR - ✗ Failed to load TTS model: 404 Client Error. (Request ID: Root=1-6917c2ca-2215aca36c10307f12116e34;dad1219d-f5d6-4e73-a9e2-51b0af7900d8)

Entry Not Found for url: https://huggingface.co/datasets/Matthijs/cmu-arctic-xvectors/resolve/main/xvectors.npy.
2025-11-15 03:01:14,502 - main - ERROR - ✗ Failed to initialize TTS engine: 404 Client Error. (Request ID: Root=1-6917c2ca-2215aca36c10307f12116e34;dad1219d-f5d6-4e73-a9e2-51b0af7900d8)

Entry Not Found for url: https://huggingface.co/datasets/Matthijs/cmu-arctic-xvectors/resolve/main/xvectors.npy.
2025-11-15 03:01:14,502 - main - WARNING - TTS will be unavailable
2025-11-15 03:01:14,502 - main - INFO - Initializing OpenAI client...
2025-11-15 03:01:15,477 - httpx - INFO - HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"
2025-11-15 03:01:15,480 - openai_integration - INFO - ✓ OpenAI API connection successful
2025-11-15 03:01:15,480 - main - INFO - ✓ OpenAI client initialized successfully
2025-11-15 03:01:15,480 - main - INFO - ============================================================
2025-11-15 03:01:15,480 - main - INFO - Voice AI Agent API is ready!
2025-11-15 03:01:15,480 - main - INFO - Access docs at: http://localhost:8000/docs
2025-11-15 03:01:15,480 - main - INFO - ============================================================
INFO:     Application startup complete.
