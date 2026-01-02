# Deploy Chatterbox TTS independently
# This ensures Chatterbox runs separately from EduSmart

Write-Host "🚀 Deploying Chatterbox TTS Service..." -ForegroundColor Green

# Create external network if it doesn't exist
$networkExists = docker network inspect edusmart-network 2>$null
if (-not $networkExists) {
    Write-Host "Creating edusmart-network..." -ForegroundColor Yellow
    docker network create edusmart-network
}

# Deploy Chatterbox
Set-Location chatterbox
docker-compose up -d --build

# Wait for health check
Write-Host "⏳ Waiting for Chatterbox to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test health endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Chatterbox TTS is running and healthy!" -ForegroundColor Green
        docker logs chatterbox-tts --tail 20
    }
} catch {
    Write-Host "❌ Chatterbox health check failed" -ForegroundColor Red
    docker logs chatterbox-tts
    exit 1
}

Write-Host ""
Write-Host "📝 Chatterbox is now independent. You can rebuild EduSmart without affecting it:" -ForegroundColor Cyan
Write-Host "   cd .. && docker-compose up -d --build" -ForegroundColor White
