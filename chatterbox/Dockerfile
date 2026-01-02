# Chatterbox TTS Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    TTS==0.22.0 \
    numpy==1.24.3 \
    torch==2.1.0 \
    torchaudio==2.1.0

# Create app file
COPY app.py /app/

# Create cache directory for models
RUN mkdir -p /root/.local/share/tts

EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
