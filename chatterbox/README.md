# Chatterbox TTS Deployment Guide

## 🎯 Overview
Chatterbox is a lightweight TTS service using Coqui TTS that replaces Edge TTS in EduSmart.

## 📦 What's Included
- **Dockerfile**: Python 3.11 with Flask + Coqui TTS
- **app.py**: HTTP server with `/tts` and `/health` endpoints
- **docker-compose.yml**: Updated to include Chatterbox service

## 🚀 Quick Start

### 1. Build and Deploy All Services
```bash
cd /path/to/EduStory
docker-compose up -d --build
```

### 2. Verify Chatterbox is Running
```bash
# Check health
curl http://localhost:5000/health

# Expected response:
# {"status": "healthy", "model_loaded": true}
```

### 3. Test TTS Generation
```bash
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello students, welcome to EduSmart!", "voice": "en-US-JennyNeural"}' \
  --output test_audio.wav
```

## 🐳 Docker Commands

### Build Chatterbox Only
```bash
docker-compose build chatterbox-tts
```

### Run Chatterbox Standalone
```bash
docker run -d \
  --name chatterbox-tts \
  -p 5000:5000 \
  --restart unless-stopped \
  edusmart-chatterbox-tts
```

### View Logs
```bash
docker logs -f chatterbox-tts
```

### Stop/Start
```bash
docker-compose stop chatterbox-tts
docker-compose start chatterbox-tts
```

## 🔧 Configuration

### Environment Variables (Backend)
The backend automatically connects to Chatterbox via:
```
CHATTERBOX_URL=http://chatterbox-tts:5000
```

This is set in [docker-compose.yml](docker-compose.yml#L47).

### Model Selection
Default model: `tts_models/en/ljspeech/tacotron2-DDC` (fast, lightweight)

To use a different model, edit [chatterbox/app.py](chatterbox/app.py#L17):
```python
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
```

Available models:
- `tts_models/en/ljspeech/tacotron2-DDC` - Fast English (default)
- `tts_models/en/ljspeech/glow-tts` - High quality English
- `tts_models/multilingual/multi-dataset/xtts_v2` - Multilingual, voice cloning

## 📊 Resource Usage

**Container Size**: ~2.5GB (includes PyTorch + TTS models)
**RAM**: ~1GB during idle, ~2GB during generation
**CPU**: 1-2 cores recommended

## 🔍 Troubleshooting

### Model Download Issues
First run downloads TTS model (~200MB). Check logs:
```bash
docker logs chatterbox-tts
```

### Connection Refused
Ensure backend is on same network:
```bash
docker network inspect edusmart-network
```

### Slow Generation
- Use lighter models (tacotron2-DDC)
- Reduce text length per scene
- Add more CPU cores to container

## 🔄 Integration with EduSmart

### Backend Changes
- [chatterbox_client.py](../backend/services/chatterbox_client.py) - HTTP client
- [main.py](../backend/main.py#L138) - Uses `chatterbox.generate_audio()`
- Edge TTS completely removed ✅

### Progressive Loading
Chatterbox integrates with progressive scene generation:
1. Scene text generated
2. Image + Audio generated in parallel
3. Audio sent to Chatterbox via HTTP POST
4. Frontend polls for completion

## 🚀 Production Deployment

### On VPS
```bash
# 1. Clone repository
git clone https://github.com/yourusername/EduStory.git
cd EduStory

# 2. Configure environment
cp .env.example .env
nano .env  # Add GEMINI_API_KEY, MYSQL credentials, etc.

# 3. Deploy all services
docker-compose up -d --build

# 4. Verify Chatterbox
curl http://localhost:5000/health

# 5. Check EduSmart backend logs
docker logs -f edusmart-backend
```

### Nginx Reverse Proxy (Optional)
```nginx
location /tts/ {
    proxy_pass http://localhost:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📝 API Reference

### POST /tts
Generate TTS audio from text.

**Request:**
```json
{
  "text": "Text to convert to speech",
  "voice": "en-US-JennyNeural"
}
```

**Response:** WAV audio file (binary)

**Status Codes:**
- 200: Success
- 400: Missing text
- 500: Generation failed
- 503: Model not loaded

### GET /health
Check service health.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## 🔐 Security Notes
- Chatterbox runs on internal network only
- Not exposed to public internet (only backend can access)
- No authentication needed (internal service)

## ⚡ Performance Tips
1. **Pre-warm Container**: Send test request after startup
2. **Keep Container Running**: Restart policy = unless-stopped
3. **Monitor Memory**: TTS models load in RAM
4. **Use Fast Models**: tacotron2-DDC for production

## 📚 Additional Resources
- [Coqui TTS Docs](https://github.com/coqui-ai/TTS)
- [EduSmart Progressive Refactoring](../PROGRESSIVE_REFACTORING.md)
- [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md)
