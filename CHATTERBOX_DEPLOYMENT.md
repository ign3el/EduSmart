# Chatterbox TTS - Standalone Docker Service

## Overview
Chatterbox TTS runs as a **separate, stateless HTTP service** accessed by EduSmart backend.
**DO NOT** install Chatterbox inside the EduSmart app container.

## Architecture

```
┌─────────────────────┐      HTTP POST      ┌──────────────────────┐
│  EduSmart Backend   │ ───────────────────> │  Chatterbox TTS      │
│  (App Container)    │                      │  (Separate Container)│
│                     │ <─────────────────── │                      │
│  - Job state        │      MP3 audio       │  - CPU-intensive     │
│  - Scene tracking   │                      │  - Stateless         │
│  - HTTP client      │                      │  - No job storage    │
└─────────────────────┘                      └──────────────────────┘
```

## Deployment

### Option 1: Docker Compose (Recommended)

Add to your existing `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Your existing EduSmart services...
  edusmart-backend:
    build: ./backend
    environment:
      - CHATTERBOX_URL=http://chatterbox-tts:5000
    depends_on:
      - chatterbox-tts
    networks:
      - edusmart-network

  edusmart-frontend:
    build: ./frontend
    networks:
      - edusmart-network

  # NEW: Chatterbox TTS Service
  chatterbox-tts:
    image: chatterbox-tts:latest  # Replace with your Chatterbox image
    container_name: chatterbox-tts
    restart: unless-stopped
    ports:
      - "5000:5000"  # Expose for debugging (optional)
    environment:
      - MODEL_PATH=/models/en_US-jenny-medium.onnx
      - WORKERS=2
      - MAX_CONCURRENT_REQUESTS=10
    volumes:
      - ./tts_models:/models:ro  # Mount TTS models
    networks:
      - edusmart-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

networks:
  edusmart-network:
    driver: bridge
```

### Option 2: Separate Docker Run

```bash
# Run Chatterbox TTS on same network as EduSmart
docker network create edusmart-network

docker run -d \
  --name chatterbox-tts \
  --network edusmart-network \
  -p 5000:5000 \
  -e MODEL_PATH=/models/en_US-jenny-medium.onnx \
  -v $(pwd)/tts_models:/models:ro \
  chatterbox-tts:latest
```

### Option 3: Shared Chatterbox for Multiple Apps

If running multiple EduSmart instances or other apps:

```yaml
# Global chatterbox-tts service (separate compose file)
version: '3.8'

services:
  chatterbox-tts:
    image: chatterbox-tts:latest
    container_name: shared-chatterbox-tts
    restart: unless-stopped
    ports:
      - "5000:5000"
    networks:
      - global-services
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G

networks:
  global-services:
    external: true
```

Then in each app's `docker-compose.yml`:

```yaml
services:
  edusmart-backend:
    environment:
      - CHATTERBOX_URL=http://shared-chatterbox-tts:5000
    networks:
      - default
      - global-services

networks:
  global-services:
    external: true
```

## Configuration

### Backend Environment Variables

In `backend/.env`:

```bash
# Chatterbox TTS endpoint (internal Docker network)
CHATTERBOX_URL=http://chatterbox-tts:5000

# OR if running on localhost for development:
# CHATTERBOX_URL=http://localhost:5000
```

### Verify Connectivity

From inside the EduSmart backend container:

```bash
docker exec -it edusmart-backend bash
curl http://chatterbox-tts:5000/health
```

Expected response:
```json
{"status": "healthy", "model_loaded": true}
```

### Test TTS Generation

```bash
curl -X POST http://chatterbox-tts:5000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test.",
    "voice": "en-US-JennyNeural",
    "rate": 0.9,
    "format": "mp3"
  }' \
  --output test_audio.mp3
```

## API Contract

### POST /tts

**Request:**
```json
{
  "text": "Scene narration text",
  "voice": "en-US-JennyNeural",
  "rate": 0.9,
  "format": "mp3"
}
```

**Response:**
- `200 OK`: MP3 audio bytes
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: TTS generation failed

**Supported Voices:**
- English: `en-US-JennyNeural`, `en-US-GuyNeural`
- Arabic: `ar-SA-HamedNeural`
- Spanish: `es-ES-ElviraNeural`
- French: `fr-FR-DeniseNeural`

## Performance Tuning

### CPU Allocation
- **Minimum**: 1 CPU core, 2GB RAM
- **Recommended**: 2 CPU cores, 4GB RAM
- **High Load**: 4 CPU cores, 8GB RAM

### Concurrency
```yaml
environment:
  - WORKERS=4  # Number of parallel TTS workers
  - MAX_CONCURRENT_REQUESTS=20
  - TIMEOUT_SECONDS=30
```

### Model Selection
- **Fast**: `en_US-lessac-medium.onnx` (~50MB, lower quality)
- **Balanced**: `en_US-jenny-medium.onnx` (~100MB, good quality)
- **High Quality**: `en_US-ljspeech-high.onnx` (~200MB, best quality)

## Monitoring

### Health Checks

Add to `docker-compose.yml`:

```yaml
services:
  chatterbox-tts:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Logs

```bash
# View Chatterbox logs
docker logs -f chatterbox-tts

# Check for errors
docker logs chatterbox-tts 2>&1 | grep -i error
```

### Metrics

Monitor these metrics:
- Request latency (should be <2s per scene)
- CPU usage (should be <80% sustained)
- Memory usage (should be stable)
- Error rate (should be <1%)

## Troubleshooting

### Issue: Connection Refused

**Cause**: EduSmart backend can't reach Chatterbox

**Fix**:
```bash
# Check if both containers are on same network
docker network inspect edusmart-network

# Verify Chatterbox is running
docker ps | grep chatterbox

# Test from backend container
docker exec -it edusmart-backend curl http://chatterbox-tts:5000/health
```

### Issue: TTS Timeouts

**Cause**: Chatterbox is overloaded

**Fix**:
```yaml
# Increase CPU allocation
deploy:
  resources:
    limits:
      cpus: '4.0'

# Increase timeout in backend
CHATTERBOX_TIMEOUT=60
```

### Issue: Poor Audio Quality

**Cause**: Using low-quality model or wrong voice

**Fix**:
```yaml
# Switch to higher quality model
environment:
  - MODEL_PATH=/models/en_US-jenny-high.onnx
```

## Security

### Production Recommendations

1. **Network Isolation**: Keep Chatterbox on internal network only
2. **No Public Exposure**: Don't expose port 5000 publicly
3. **Rate Limiting**: Implement rate limits in EduSmart backend
4. **Resource Limits**: Always set CPU/memory limits

```yaml
services:
  chatterbox-tts:
    networks:
      - internal  # Not exposed to internet
    ports: []  # No port mapping
```

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
services:
  chatterbox-tts:
    deploy:
      replicas: 3  # Run 3 instances
      restart_policy:
        condition: on-failure
```

### Load Balancing

Use Docker Swarm or add nginx upstream:

```nginx
upstream chatterbox_backend {
    server chatterbox-tts-1:5000;
    server chatterbox-tts-2:5000;
    server chatterbox-tts-3:5000;
}
```

## Cost Optimization

- **Shared Service**: Run one Chatterbox for multiple apps
- **Model Caching**: Keep models in shared volume
- **Lazy Loading**: Start Chatterbox only when needed
- **Auto-scaling**: Scale down during low traffic

---

**Remember**: Chatterbox is a **separate, stateless service**. Never install it inside the app container!
