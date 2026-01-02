"""
Chatterbox TTS Service
A lightweight HTTP server for text-to-speech using Coqui TTS
Supports multiple applications with optional API key authentication
"""
from flask import Flask, request, jsonify, send_file
from TTS.api import TTS  # type: ignore
import io
import logging
import os
from functools import wraps

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('API_KEY', None)
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 1000))
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')

# API Key middleware
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if API_KEY:
            provided_key = request.headers.get('X-API-Key')
            if provided_key != API_KEY:
                return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Initialize TTS model (using fast, lightweight model)
# jenny_xtts_v2 is a good quality English model
try:
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
    logger.info("✅ TTS model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load TTS model: {e}")
    tts = None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": tts is not None}), 200

@app.route('/tts', methods=['POST'])
@require_api_key
def generate_tts():
    """
    Generate TTS audio from text
    Request body: {"text": "...", "voice": "en-US-JennyNeural"}
    Headers: X-API-Key: your-api-key (if API_KEY is set)
    Returns: WAV audio file
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'en-US-JennyNeural')  # Ignored for now, can extend later
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({"error": f"Text too long (max {MAX_TEXT_LENGTH} chars)"}), 400
        
        if not tts:
            return jsonify({"error": "TTS model not loaded"}), 503
        
        logger.info(f"Generating audio for text (length: {len(text)})")
        
        # Generate audio directly to BytesIO
        audio_buffer = io.BytesIO()
        tts.tts_to_file(text=text, file_path=audio_buffer)
        audio_buffer.seek(0)
        
        logger.info(f"✅ Audio generated ({audio_buffer.getbuffer().nbytes} bytes)")
        
        return send_file(
            audio_buffer,
            mimetype='audio/wav',
            as_attachment=False,
            download_name='speech.wav'
        )
    
    except Exception as e:
        logger.error(f"❌ TTS generation failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
