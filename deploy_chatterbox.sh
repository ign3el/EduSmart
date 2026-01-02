#!/bin/bash

# Deploy Chatterbox TTS independently
# This script ensures Chatterbox runs separately from EduSmart

echo "🚀 Deploying Chatterbox TTS Service..."

# Create external network if it doesn't exist
docker network inspect edusmart-network >/dev/null 2>&1 || \
    docker network create edusmart-network

# Deploy Chatterbox
cd chatterbox
docker-compose up -d --build

# Wait for health check
echo "⏳ Waiting for Chatterbox to be healthy..."
sleep 10

# Test health endpoint
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✅ Chatterbox TTS is running and healthy!"
    docker logs chatterbox-tts --tail 20
else
    echo "❌ Chatterbox health check failed"
    docker logs chatterbox-tts
    exit 1
fi

echo ""
echo "📝 Chatterbox is now independent. You can rebuild EduSmart without affecting it:"
echo "   cd .. && docker-compose up -d --build"
