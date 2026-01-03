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
    tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False)
    logger.info("✅ TTS model loaded successfully (multi-speaker).")
except Exception as e:
    logger.error(f"❌ Failed to load TTS model: {e}")
    tts = None

# Maps friendly names from the frontend to VCTK speaker IDs
VOICE_MAPPING = {
    # Top-tier expressive voices
    "Ana Florence": "p232",  # Female, clear, youthful
    "Abrahan Mack": "p236",  # Male, deep, warm
    "Claribel Dervla": "p225",  # Female, soft, soothing
    "Lidiya Szekeres": "p230",  # Female, animated
    "Damien Black": "p243",  # Male, mysterious
    "Daisy Studious": "p228",  # Female, clear, intelligent
    "Viktor Eka": "p254",  # Male, rugged
    "Nova Hogarth": "p229",  # Female, whimsical
    # Adventure Group
    "Chandra MacFarland": "p231",
    "Royston Min": "p244",
    # Calm & Cozy Group
    "Alison Dietlinde": "p226",
    "Gitta Nikolina": "p227",
    # Character Actors
    "Craig Gutsy": "p239",
    "Badr Odhiambo": "p251",
}
DEFAULT_SPEAKER = "p232"  # Default to Ana Florence


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": tts is not None}), 200

@app.route('/tts', methods=['POST'])
@require_api_key
def generate_tts():
    """
    Generate TTS audio from text
    Request body: {"text": "...", "voice": "Ana Florence"}
    Headers: X-API-Key: your-api-key (if API_KEY is set)
    Returns: WAV audio file
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice = data.get('voice', 'Ana Florence')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({"error": f"Text too long (max {MAX_TEXT_LENGTH} chars)"}), 400
        
        if not tts:
            return jsonify({"error": "TTS model not loaded"}), 503
        
        # Get speaker ID from mapping, with a fallback to the default
        speaker_id = VOICE_MAPPING.get(voice, DEFAULT_SPEAKER)
        logger.info(f"Generating audio for text (length: {len(text)}) using voice: {voice} (speaker: {speaker_id})")
        
        # Generate audio directly to BytesIO
        audio_buffer = io.BytesIO()
        tts.tts_to_file(text=text, speaker=speaker_id, file_path=audio_buffer)
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
