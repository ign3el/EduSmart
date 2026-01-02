# EduSmart Progressive Refactoring - Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Code Changes Complete
- [x] Edge TTS completely removed from app container
- [x] Chatterbox HTTP client implemented (`services/chatterbox_client.py`)
- [x] Job state manager with SQLite (`job_state.py`)
- [x] Progressive scene generation endpoints
- [x] Frontend progressive player component
- [x] Requirements.txt updated (no edge-tts dependency)

### 2. Architecture Verified
```
✓ App Container:     EduSmart backend + SQLite job state
✓ TTS Container:     Chatterbox (separate, stateless)
✓ Communication:     HTTP POST to http://chatterbox-tts:5000/tts
✓ No Redis:          Job state is app-local only
✓ No TTS in app:     All TTS via HTTP calls
```

## 📋 Deployment Steps

### Step 1: Deploy Chatterbox TTS (First!)

```bash
# Create shared network if not exists
docker network create edusmart-network

# Deploy Chatterbox TTS
docker run -d \
  --name chatterbox-tts \
  --network edusmart-network \
  --restart unless-stopped \
  -p 5000:5000 \
  -e MODEL_PATH=/models/en_US-jenny-medium.onnx \
  -e WORKERS=2 \
  -v $(pwd)/tts_models:/models:ro \
  chatterbox-tts:latest

# Verify it's running
docker logs chatterbox-tts
curl http://localhost:5000/health
```

**Expected output:**
```json
{"status": "healthy", "model_loaded": true}
```

### Step 2: Update EduSmart Backend Config

```bash
cd backend

# Update .env file
cat >> .env << EOF
# Chatterbox TTS Configuration
CHATTERBOX_URL=http://chatterbox-tts:5000
EOF

# Verify config
grep CHATTERBOX .env
```

### Step 3: Rebuild & Deploy EduSmart

```bash
# Pull latest code
cd /path/to/edusmart
git pull origin main

# Rebuild without cache to ensure Edge TTS is gone
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

# Check logs
docker logs -f edusmart-backend
```

**Expected logs:**
```
✓ MySQL connection pool created successfully
✓ Database tables initialized successfully
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Verify Connectivity

```bash
# Test from backend to Chatterbox
docker exec -it edusmart-backend bash
curl http://chatterbox-tts:5000/health

# Exit container
exit
```

### Step 5: Test End-to-End

1. **Upload a PDF:**
   ```bash
   curl -X POST http://your-domain.com/api/upload \
     -F "file=@test.pdf" \
     -F "grade_level=Grade 4" \
     -F "voice=en-US-JennyNeural"
   ```

2. **Check story status:**
   ```bash
   curl http://your-domain.com/api/story/{story_id}/status
   ```

3. **Verify scene generation:**
   - First scene text should be available within 10s
   - First scene audio/image should complete within 30s
   - Check logs for Chatterbox TTS calls

### Step 6: Monitor Production

```bash
# Watch backend logs
docker logs -f edusmart-backend | grep -E "Scene|TTS|Chatterbox"

# Watch Chatterbox logs
docker logs -f chatterbox-tts

# Check resource usage
docker stats edusmart-backend chatterbox-tts
```

## 🔍 Verification Tests

### Test 1: Upload & Progressive Loading
```bash
# Upload PDF
STORY_ID=$(curl -X POST http://localhost:8000/api/upload \
  -F "file=@sample.pdf" \
  -F "grade_level=Grade 4" | jq -r '.story_id')

# Poll status (should show scenes appearing progressively)
watch -n 3 "curl -s http://localhost:8000/api/story/$STORY_ID/status | jq"
```

**Expected behavior:**
- Story structure returns immediately
- Scene text is available right away
- Image/audio status updates from `pending` → `processing` → `completed`

### Test 2: Chatterbox TTS Call
```bash
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test of the text to speech system.",
    "voice": "en-US-JennyNeural",
    "rate": 0.9,
    "format": "mp3"
  }' \
  --output test.mp3

# Verify audio file
file test.mp3  # Should be: MPEG ADTS, layer III
```

### Test 3: Frontend Progressive Loading
1. Open browser to https://your-domain.com
2. Upload a PDF
3. **Verify:**
   - Story text appears immediately
   - Skeleton loading shows for incomplete scenes
   - First scene becomes playable within ~30s
   - Progress bar updates as scenes complete
   - Can navigate to completed scenes while others load

## 🚨 Troubleshooting

### Issue: "Connection refused" to Chatterbox

**Diagnosis:**
```bash
# Check if Chatterbox is running
docker ps | grep chatterbox

# Check network connectivity
docker network inspect edusmart-network | grep -A 10 chatterbox
```

**Fix:**
```bash
# Restart Chatterbox
docker restart chatterbox-tts

# Verify backend can reach it
docker exec edusmart-backend ping chatterbox-tts
```

### Issue: Audio generation fails

**Check Chatterbox logs:**
```bash
docker logs chatterbox-tts --tail 100
```

**Common causes:**
- Model not loaded: Check `MODEL_PATH` env var
- Out of memory: Increase container memory limit
- Invalid voice name: Check supported voices in Chatterbox

**Fix:**
```bash
# Increase memory
docker update --memory 4G chatterbox-tts
docker restart chatterbox-tts
```

### Issue: Slow scene generation

**Diagnosis:**
```bash
# Check resource usage
docker stats --no-stream chatterbox-tts edusmart-backend

# Check if jobs are piling up
docker exec edusmart-backend sqlite3 job_state.db "SELECT COUNT(*) FROM scenes WHERE audio_status='processing';"
```

**Fix:**
```bash
# Scale Chatterbox horizontally
docker-compose up -d --scale chatterbox-tts=3

# Or allocate more CPU
docker update --cpus 4 chatterbox-tts
```

### Issue: Database locked errors

**Cause:** SQLite concurrent writes

**Fix:** Already handled by thread-safe connection pooling in `job_state.py`. If persist:
```bash
# Check for stuck connections
docker exec edusmart-backend ps aux | grep python
```

## 🎯 Performance Targets

After deployment, verify these metrics:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| First scene text visible | <10s | Check frontend console |
| First scene playable | 20-30s | Manual test |
| Full story complete | ~2 min | Check status endpoint |
| Chatterbox TTS latency | <2s/scene | Check backend logs |
| CPU usage (Chatterbox) | <80% | `docker stats` |
| Memory usage (Backend) | <500MB | `docker stats` |

## 📊 Monitoring Dashboard

Set up these metrics (optional but recommended):

```bash
# Request latency
curl http://localhost:8000/api/story/{id}/status

# Scene completion rate
sqlite3 backend/job_state.db "SELECT 
  COUNT(CASE WHEN image_status='completed' THEN 1 END) as completed_images,
  COUNT(CASE WHEN audio_status='completed' THEN 1 END) as completed_audio,
  COUNT(*) as total_scenes
FROM scenes;"

# Chatterbox health
curl http://localhost:5000/health
```

## ✨ Success Criteria

Deployment is successful when:

- [  ] PDF uploads process without errors
- [  ] Story structure appears within 10 seconds
- [  ] First scene is playable within 30 seconds
- [  ] No Edge TTS errors in logs
- [  ] Chatterbox health check passes
- [  ] Frontend shows skeleton loading correctly
- [  ] All scenes eventually complete
- [  ] Mobile layout works correctly

## 🔄 Rollback Plan

If critical issues occur:

```bash
# Stop new system
docker-compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild
docker-compose build --no-cache
docker-compose up -d

# Note: Restore edge-tts in requirements.txt if needed
```

## 📞 Support Contacts

- **Backend logs:** `docker logs edusmart-backend`
- **Chatterbox logs:** `docker logs chatterbox-tts`
- **Job state DB:** `sqlite3 backend/job_state.db`
- **Documentation:** See `PROGRESSIVE_REFACTORING.md` and `CHATTERBOX_DEPLOYMENT.md`

---

**Last Updated:** January 2, 2026  
**Version:** 2.0.0-progressive  
**Status:** Ready for Production ✅
