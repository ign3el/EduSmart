# Chatterbox TTS - Standalone Microservice Deployment Guide

## 🎯 Overview
Deploy Chatterbox as a shared TTS service that multiple applications can use.

## 📁 Deployment Location

### **VPS Structure:**
```
/opt/
├── chatterbox-tts/          ← Standalone TTS service
│   ├── Dockerfile
│   ├── docker-compose.standalone.yml
│   ├── app.py
│   ├── .env
│   └── README_STANDALONE.md
│
├── EduStory/                ← Your app 1
│   └── ...
│
├── AnotherApp/              ← Your app 2
│   └── ...
```

## 🚀 Deployment Steps

### **1. Create Standalone Directory**
```bash
# On your VPS
cd /opt
mkdir chatterbox-tts
cd chatterbox-tts
```

### **2. Copy Chatterbox Files**
```bash
# Copy from your EduStory repo
cp /path/to/EduStory/chatterbox/Dockerfile .
cp /path/to/EduStory/chatterbox/app.py .
cp /path/to/EduStory/chatterbox/docker-compose.standalone.yml docker-compose.yml
cp /path/to/EduStory/chatterbox/.env.example .env
```

Or create a separate Git repo:
```bash
git clone https://github.com/yourusername/chatterbox-tts.git /opt/chatterbox-tts
```

### **3. Configure Environment**
```bash
nano .env
```

Set your API key:
```env
API_KEY=super-secret-key-12345
MAX_TEXT_LENGTH=1000
ALLOWED_ORIGINS=*
```

### **4. Deploy**
```bash
docker-compose up -d --build
```

### **5. Verify**
```bash
# Health check
curl http://localhost:5000/health

# Test TTS with API key
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: super-secret-key-12345" \
  -d '{"text": "Hello from Chatterbox!"}' \
  --output test.wav
```

## 🔌 Connecting Apps to Chatterbox

### **App 1: EduStory**

**Backend .env:**
```env
CHATTERBOX_URL=http://chatterbox-tts:5000
CHATTERBOX_API_KEY=super-secret-key-12345
```

**Docker network:**
```bash
# Connect EduStory to Chatterbox network
docker network connect chatterbox-public edusmart-backend
```

Or in `docker-compose.yml`:
```yaml
services:
  backend:
    networks:
      - edusmart-network
      - chatterbox-public

networks:
  chatterbox-public:
    external: true
```

### **App 2: Another App**

```python
import requests

def generate_speech(text):
    response = requests.post(
        'http://chatterbox-tts:5000/tts',
        json={'text': text},
        headers={'X-API-Key': 'super-secret-key-12345'}
    )
    return response.content  # WAV bytes
```

```yaml
# docker-compose.yml
networks:
  - chatterbox-public

networks:
  chatterbox-public:
    external: true
```

### **External Apps (Public Internet)**

If exposing publicly, use nginx reverse proxy with SSL:

```nginx
# /etc/nginx/sites-available/chatterbox
server {
    listen 443 ssl http2;
    server_name tts.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/tts.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tts.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Rate limiting
        limit_req zone=tts_limit burst=10;
    }
}

# Rate limit zone
http {
    limit_req_zone $binary_remote_addr zone=tts_limit:10m rate=10r/s;
}
```

Then access:
```bash
curl -X POST https://tts.yourdomain.com/tts \
  -H "X-API-Key: super-secret-key-12345" \
  -d '{"text": "Hello!"}'
```

## 🔐 Security Best Practices

1. **Always set API_KEY** in production:
   ```bash
   openssl rand -hex 32  # Generate random key
   ```

2. **Use HTTPS** for public access

3. **Set MAX_TEXT_LENGTH** to prevent abuse:
   ```env
   MAX_TEXT_LENGTH=500
   ```

4. **Enable rate limiting** via nginx

5. **Monitor usage**:
   ```bash
   docker logs -f chatterbox-tts
   ```

## 📊 Resource Management

**Single Chatterbox instance specs:**
- CPU: 2 cores
- RAM: 2-3GB
- Disk: 3GB (model cache)

**Handles multiple apps because:**
- Stateless HTTP service
- Model loaded once in memory
- Fast generation (~2s per request)
- Can scale horizontally if needed

## 🔄 Management Commands

```bash
# View logs
docker logs -f chatterbox-tts

# Restart
docker restart chatterbox-tts

# Update
cd /opt/chatterbox-tts
git pull  # if using Git repo
docker-compose down
docker-compose up -d --build

# Monitor resource usage
docker stats chatterbox-tts
```

## 📈 Scaling (Optional)

If you need higher throughput:

```yaml
# docker-compose.yml
services:
  chatterbox-tts-1:
    build: .
    ports: ["5001:5000"]
    
  chatterbox-tts-2:
    build: .
    ports: ["5002:5000"]

# Add nginx load balancer
upstream chatterbox {
    server localhost:5001;
    server localhost:5002;
}
```

## 🧪 Testing Multiple Apps

```bash
# Test from EduStory container
docker exec edusmart-backend curl http://chatterbox-tts:5000/health

# Test from another app container
docker exec otherapp curl http://chatterbox-tts:5000/health
```

## 📝 Summary

**Deployment Path:** `/opt/chatterbox-tts/`

**Access:**
- Internal apps: `http://chatterbox-tts:5000` (Docker network)
- External apps: `https://tts.yourdomain.com` (nginx proxy)

**Authentication:** API key via `X-API-Key` header

**Independence:** Completely separate from any app, shared by all
