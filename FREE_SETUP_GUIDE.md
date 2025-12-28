# Free & Open-Source Setup Guide

Complete guide to running EduStory **completely free** using open-source alternatives with **zero API costs**.

## 🎯 Quick Summary

| Component | Free Alternative | Cost | Setup Time |
|-----------|------------------|------|-----------|
| **Text Generation** | Ollama + Mistral/Llama 2 | $0 | 15 min |
| **Image Generation** | Stable Diffusion (diffusers) | $0 | 20 min |
| **Voice Generation** | Piper TTS | $0 | 10 min |
| **Caching** | Redis | $0 | 5 min |
| **Total** | | **$0** | ~50 min |

## Prerequisites

- Python 3.11+
- Node.js 18+
- At least 8GB RAM (16GB recommended for image generation)
- GPU is optional but speeds up image generation 10-50x

---

## Step 1: Install Ollama (Text Generation)

Ollama allows you to run LLMs locally on your machine.

### Windows

1. Download from https://ollama.ai/download
2. Run the installer
3. Open PowerShell and verify:
```powershell
ollama --version
```

4. Pull a model (first time takes a few minutes):
```powershell
ollama pull mistral
# OR for smaller model:
ollama pull neural-chat
```

5. Start Ollama in background (it stays running):
```powershell
ollama serve
```

### Linux/Mac

```bash
curl https://ollama.ai/install.sh | sh
ollama pull mistral
ollama serve
```

**Verify it's working:**
```powershell
# In another terminal
curl http://localhost:11434/api/generate -X POST `
  -H "Content-Type: application/json" `
  -d @{ model = "mistral"; prompt = "Hello" } | ConvertFrom-Json
```

---

## Step 2: Install Stable Diffusion (Image Generation)

Uses the `diffusers` library to generate images locally.

### Option A: GPU (Fastest - Recommended)

If you have an NVIDIA GPU:

```powershell
cd backend
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install diffusers transformers accelerate safetensors
```

First model download will be ~5GB. Subsequent images generate in 10-30 seconds.

### Option B: CPU (Slower but works)

```powershell
cd backend
pip install diffusers transformers safetensors
# Note: Image generation will be 2-3 minutes per image
```

**Test image generation:**
```python
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
prompt = "a friendly wizard teaching children, cartoon style"
image = pipe(prompt).images[0]
image.save("test.png")
```

---

## Step 3: Install Piper TTS (Voice Generation)

Piper generates fast, realistic speech with zero API calls.

### Windows

```powershell
# Install Piper
pip install piper-tts

# Download a voice model (one-time, ~80MB)
piper --download-dir ./piper_models --voice en_US-ryan-medium

# Test it
"Hello, this is Piper TTS!" | piper --model ./piper_models/en_US-ryan-medium/en_US-ryan-medium.onnx --output-file test.wav
```

### Linux/Mac

```bash
pip install piper-tts
piper --download-dir ./piper_models --voice en_US-ryan-medium

echo "Hello, this is Piper TTS!" | piper --model ./piper_models/en_US-ryan-medium/en_US-ryan-medium.onnx --output-file test.wav
```

**Available voices:**
- `en_US-ryan-medium` (default, natural male voice)
- `en_US-amy-medium` (natural female voice)
- `en_US-lessac-medium` (slightly higher pitched male)

---

## Step 4: Install Redis (Caching)

Caching saves time and storage by reusing generated assets.

### Windows (WSL2 or Docker)

```powershell
# Option 1: Docker
docker run -d -p 6379:6379 redis:latest

# Option 2: Using WSL2
# In WSL terminal:
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

### Linux/Mac

```bash
# Homebrew (Mac)
brew install redis
redis-server

# Ubuntu/Debian
sudo apt-get install redis-server
redis-server
```

**Test Redis:**
```powershell
redis-cli ping
# Should output: PONG
```

---

## Step 5: Configure EduStory

### Update Environment File

```powershell
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```env
# Use local services (FREE!)
SERVICE_MODE=local

# Text Generation (Ollama - running locally)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Image Generation (local Stable Diffusion)
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
IMAGE_INFERENCE_STEPS=25

# Voice Generation (Piper TTS)
PIPER_MODEL=en_US-ryan-medium

# Caching (Redis)
USE_CACHE=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=86400  # 24 hours

# Leave API keys empty (not needed for local mode!)
OPENAI_API_KEY=
STABILITY_API_KEY=
ELEVENLABS_API_KEY=
```

### Install Python Dependencies

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate

# Install only dependencies for local services
pip install -r requirements.txt
```

### Install Frontend Dependencies

```powershell
cd ../frontend
npm install
```

---

## Step 6: Run Everything

You need **4 terminal windows**:

### Terminal 1: Ollama (Text Generation)
```powershell
ollama serve
# Keep this running - Ollama stays in background
```

### Terminal 2: Redis (Caching)
```powershell
redis-server
# Or if using Docker:
docker start redis  # Assuming container named 'redis'
```

### Terminal 3: Backend API
```powershell
cd backend
.\venv\Scripts\activate
python main.py
# Runs at http://localhost:8000
```

### Terminal 4: Frontend
```powershell
cd frontend
npm run dev
# Runs at http://localhost:3000
```

**Open browser:** http://localhost:3000

---

## 🚀 First Story Generation

1. Create a simple test document (PDF or DOCX) with educational content
2. Upload it to EduStory
3. Choose grade level (e.g., Grade 3)
4. Select your guide character (e.g., Wizard)
5. Click "Generate Story"

**First run timings (with caching OFF):**
- Text: 30-60 seconds (Ollama)
- Images (GPU): 2-3 minutes total (8 scenes × 15-20s each)
- Images (CPU): 15-20 minutes (much slower, not recommended)
- Audio: 1-2 minutes (Piper TTS)
- **Total: 4-8 minutes first time**

**Subsequent runs:** 1-2 seconds (cached!)

---

## ⚙️ Performance Tuning

### Speed Up Image Generation (GPU)

If images are slow, try:

```env
IMAGE_INFERENCE_STEPS=15  # Faster but lower quality
# or
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5-inpainting  # Faster variant
```

### Speed Up Ollama

```powershell
# Use faster model instead of Mistral
ollama pull neural-chat  # Faster, 7B parameters
ollama pull dolphin-mixtral  # Higher quality
```

### Use ONNX Models (Faster Diffusers)

```powershell
pip install onnx onnxruntime
# Update .env:
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-onnx
```

---

## 🐛 Troubleshooting

### "Ollama connection failed"
- Verify Ollama is running: `ollama serve` in separate terminal
- Check: `curl http://localhost:11434/api/generate`

### "Torch not found" or GPU issues
- Reinstall torch: `pip install torch --force-reinstall --index-url https://download.pytorch.org/whl/cu118`
- Verify GPU: `python -c "import torch; print(torch.cuda.is_available())"`

### "Redis connection failed"
- Make sure Redis is running: `redis-cli ping` should return PONG
- Or disable caching: `USE_CACHE=false` in .env

### Images taking too long (5+ minutes)
- You're using CPU. Switch to GPU or use faster model
- Reduce `IMAGE_INFERENCE_STEPS=15` for draft quality

### Memory issues during image generation
- Close other apps
- Reduce `IMAGE_INFERENCE_STEPS` to 15
- Use smaller model: `stabilityai/stable-diffusion-2-1-base`

---

## 💰 Cost Comparison

### Using Paid APIs (Default Setup)
For 1,000 stories per month:
- OpenAI GPT-4: ~$30/month
- Stability AI: ~$50/month
- ElevenLabs: ~$80/month
- **Total: ~$160/month**

### Using Free Open-Source (This Guide)
- Ollama: $0 (runs on your server)
- Stable Diffusion: $0 (local)
- Piper TTS: $0 (local)
- Redis: $0 (self-hosted)
- **Total: $0/month**

**Annual savings: ~$1,920** ✅

---

## Next Steps

- ✅ All services running locally
- ✅ Zero API costs
- ✅ Full data privacy (nothing sent to cloud)
- ✅ Unlimited generations
- ✅ Customizable model swapping

**Want to scale?**
- Use Docker Compose for multi-server setup
- Deploy to cloud (AWS/GCP/Azure) with same free models
- Add load balancing for multiple user requests

---

## Support

Having issues? Check:
1. All 4 terminals running (Ollama, Redis, Backend, Frontend)
2. Browser console for frontend errors (F12)
3. Backend logs for API errors
4. `.env` file has correct `SERVICE_MODE=local`

