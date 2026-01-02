# Progressive Scene Loading & Chatterbox TTS - Refactoring Guide

## Overview
This refactoring transforms EduSmart from synchronous full-story generation to **progressive scene-by-scene streaming**, reducing perceived wait time from ~5 minutes to ~2 minutes for the first playable scene.

## Key Changes

### Backend Refactoring

#### 1. **Job State Management** (`backend/job_state.py`)
- **SQLite-based scene tracking** (no Redis required)
- Stores per-scene status for images and audio
- Thread-safe with connection pooling
- Isolated per application instance

**Schema:**
- `stories` table: story-level metadata and completion status
- `scenes` table: per-scene text, image status/URL, audio status/URL

#### 2. **Chatterbox TTS Client** (`backend/services/chatterbox_client.py`)
- Replaces Edge TTS with self-hosted Chatterbox HTTP API
- Supports multiple voices (English, Arabic)
- Async-compatible with FastAPI
- **Configuration:** Set `CHATTERBOX_URL=http://your-chatterbox-server:8001` in `.env`

#### 3. **Progressive Scene Generation** (`backend/main.py`)
**Old Flow:**
```
Upload → Generate full story → Generate all images → Generate all audio → Return
```

**New Flow:**
```
Upload → Generate story structure → Create scene records (text ready immediately)
       → For each scene IN PARALLEL:
           - Generate image
           - Generate audio (Chatterbox)
           - Update scene status individually
```

**Key Functions:**
- `generate_scene_media_progressive()`: Parallel image + audio generation per scene
- `run_ai_workflow_progressive()`: Orchestrates progressive generation
- Scene state updates happen as each asset completes

#### 4. **New API Endpoints**
```
GET /api/story/{story_id}/status
  → Returns overall story status + all scene statuses
  → Frontend polls this every 3s

GET /api/story/{story_id}/scene/{scene_index}
  → Returns specific scene data (text, image_url, audio_url, statuses)

POST /api/upload
  → Now returns story_id immediately (not job_id)
  → Story text available within ~10s
```

### Frontend Refactoring

#### 1. **Progressive Story Player** (`frontend/src/components/ProgressiveStoryPlayer.jsx`)
- **Polling:** Fetches story status every 3 seconds
- **Skeleton Loading:** Shows animated placeholder for incomplete scenes
- **Lazy Media Loading:** Images/audio load only when ready
- **Scene Unlocking:** Users can view completed scenes while others generate

**Features:**
- Spinner + "Generating scene X..." message for incomplete scenes
- Progress bar showing overall completion
- Play/Pause disabled until scene audio is ready
- Mobile-first responsive design

#### 2. **CSS Enhancements** (`StoryPlayer.css`)
- Skeleton shimmer animation for loading states
- Spinner animation for progress indicators
- Progress bar with gradient fill
- Mobile-optimized touch targets

### Configuration

#### Backend `.env` Updates
```bash
# Add Chatterbox TTS endpoint
CHATTERBOX_URL=http://localhost:8001

# Existing configs remain unchanged
GEMINI_API_KEY=your-key
MYSQL_HOST=10.0.0.147
# ... etc
```

#### Requirements
```txt
# Removed: edge-tts>=6.1.0
# Edge TTS no longer needed

# Existing dependencies unchanged
fastapi==0.108.0
google-genai>=0.2.0
# ... etc
```

### Deployment Steps

#### 1. **Deploy Chatterbox TTS** (separate container/server)
```bash
# Example docker-compose service
services:
  chatterbox-tts:
    image: chatterbox-tts:latest
    ports:
      - "8001:8001"
    environment:
      - MODEL_PATH=/models/en-us-jenny.onnx
```

#### 2. **Update EduSmart Backend**
```bash
cd backend
pip install -r requirements.txt  # No new deps, just removed edge-tts
python -c "from job_state import job_manager; print('DB initialized')"
```

#### 3. **Update Environment**
```bash
echo "CHATTERBOX_URL=http://chatterbox-tts:8001" >> .env
```

#### 4. **Restart Services**
```bash
docker-compose down
docker-compose up -d --build
```

### Performance Targets

| Metric | Before | After |
|--------|--------|-------|
| First scene playable | ~5 min | **20-30s** |
| Full story complete | ~5 min | **~2 min** |
| User wait perception | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### Mobile Optimizations

1. **Lower Image Resolution**: Target 768×768 (adjustable in `gemini_service.py`)
2. **Lazy Loading**: Images load only when scene is visited
3. **Audio Streaming**: No preloading, plays on-demand
4. **Progressive Rendering**: Text shows immediately, media fills in

### Monitoring & Debugging

#### Check Job State
```python
from job_state import job_manager

# Get story status
status = job_manager.get_story_status("story-uuid-123")
print(status)

# Get all scenes
scenes = job_manager.get_all_scenes("story-uuid-123")
for scene in scenes:
    print(f"Scene {scene['scene_index']}: img={scene['image_status']}, audio={scene['audio_status']}")
```

#### Check Chatterbox Connectivity
```bash
curl http://localhost:8001/tts \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "en-US-JennyNeural", "format": "mp3"}'
```

### Rollback Plan

If issues arise, you can temporarily revert to the old system:

1. **Backend**: Comment out `run_ai_workflow_progressive` calls, uncomment old `run_ai_workflow`
2. **Frontend**: Use `StoryPlayer.jsx` instead of `ProgressiveStoryPlayer.jsx`
3. **TTS**: Reinstall `edge-tts` in requirements.txt and restore `gemini_service.py` TTS calls

### Known Limitations

1. **No Redis**: Job state is per-instance only (not shared across multiple backend containers)
2. **SQLite Concurrency**: Fine for <100 concurrent users per instance; scale horizontally if needed
3. **Chatterbox Dependency**: If Chatterbox is down, audio generation fails (add fallback to Edge TTS if critical)

### Future Enhancements

1. **WebSocket Updates**: Replace polling with server-sent events for real-time updates
2. **Scene Prioritization**: Generate current scene first, others in background
3. **Partial Scene Playback**: Show image while audio still generating
4. **Batch Image Generation**: Group multiple scenes per GPU call to reduce overhead

---

## Testing Checklist

- [ ] Upload PDF, verify story structure appears within 10s
- [ ] First scene image + audio complete within 30s
- [ ] Skeleton loading shows for incomplete scenes
- [ ] Users can navigate to completed scenes while others generate
- [ ] Progress bar updates as scenes complete
- [ ] Play/Pause works correctly when scene is ready
- [ ] Mobile layout renders correctly (< 768px width)
- [ ] Multiple concurrent uploads don't interfere
- [ ] Story completion marked correctly when all scenes done
- [ ] Saved stories retain progressive loading data

## Support

For issues, check:
1. Backend logs: `docker logs edusmart-backend`
2. Job state database: `sqlite3 backend/job_state.db "SELECT * FROM stories;"`
3. Chatterbox logs: `docker logs chatterbox-tts`
4. Frontend console: Browser DevTools → Console tab

---

**Version:** 2.0.0-progressive  
**Author:** EduSmart Refactoring Team  
**Date:** January 2026
