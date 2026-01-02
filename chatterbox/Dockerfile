# Chatterbox TTS Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    libsndfile1 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (remove version pins to avoid build issues)
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    TTS \
    numpy \
    torch \
    torchaudio

# Create app file
COPY app.py /app/

# Create cache directory for models
RUN mkdir -p /root/.local/share/tts

EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
